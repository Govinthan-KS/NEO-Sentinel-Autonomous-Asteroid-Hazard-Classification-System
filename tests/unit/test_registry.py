import pytest
from unittest.mock import patch, MagicMock
from asteroid_classifier.models.registry import init_registry, get_best_run, enrich_version_metadata, archive_active_models, register_and_promote
from asteroid_classifier.core.exceptions import ModelPromotionError

@pytest.fixture
def mock_run():
    mock_run = MagicMock()
    mock_run.info.run_id = "test-run-id"
    mock_run.info.start_time = 1713500000000 # dummy timestamp
    mock_run.data.params = {"data_dvc_hash": "a1b2c3d4"}
    mock_run.data.metrics = {"cpu_utilization_end": 45.2, "memory_used_gb_end": 1.2, "recall": 0.95, "f1": 0.90}
    return mock_run

def test_init_registry_missing_env(monkeypatch):
    monkeypatch.delenv("DAGSHUB_REPO_OWNER", raising=False)
    monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)
    
    with patch('asteroid_classifier.models.registry.dagshub.init') as mock_init, \
         patch('asteroid_classifier.models.registry.mlflow.set_tracking_uri') as mock_set_uri:
        
        uri = init_registry({"mlflow_tracking_uri": "http://config.local:5000"})
        mock_init.assert_called_once_with(repo_owner="Govinthan-KS", repo_name="Asteroid-Hazard-Classifier", mlflow=True)
        mock_set_uri.assert_called_once_with("http://config.local:5000")
        assert uri == "http://config.local:5000"

def test_get_best_run():
    client_mock = MagicMock()
    client_mock.get_experiment_by_name.return_value = MagicMock(experiment_id="exp1")
    
    run_mock = MagicMock()
    client_mock.search_runs.return_value = [run_mock]
    
    best_run = get_best_run(client_mock, "test-exp")
    
    assert best_run == run_mock
    client_mock.search_runs.assert_called_once_with(
        experiment_ids=["exp1"],
        order_by=["metrics.recall DESC", "metrics.f1 DESC"],
        max_results=1
    )

def test_get_best_run_no_experiment():
    client_mock = MagicMock()
    client_mock.get_experiment_by_name.return_value = None
    with pytest.raises(ValueError, match="not found"):
        get_best_run(client_mock, "test-exp")

def test_enrich_version_metadata(mock_run):
    client_mock = MagicMock()
    
    enrich_version_metadata(client_mock, "TestModel", "v1", mock_run, dry_run=False)
    
    client_mock.update_model_version.assert_called_once()
    call_args = client_mock.update_model_version.call_args[1]
    
    assert call_args["name"] == "TestModel"
    assert call_args["version"] == "v1"
    
    desc = call_args["description"]
    assert "a1b2c3d4" in desc
    assert "45.2" in desc
    assert "1.2" in desc

def test_archive_active_models():
    client_mock = MagicMock()
    
    info_mock = MagicMock()
    mv1 = MagicMock(version="1", current_stage="Production")
    mv2 = MagicMock(version="2", current_stage="Staging")
    mv3 = MagicMock(version="3", current_stage="Archived")
    
    info_mock.latest_versions = [mv1, mv2, mv3]
    client_mock.get_registered_model.return_value = info_mock
    
    archive_active_models(client_mock, "TestModel", keep_version="3", dry_run=False)
    
    assert client_mock.transition_model_version_stage.call_count == 2 # Only mv1 and mv2 (active) should be archived

@patch('asteroid_classifier.models.registry.init_registry')
@patch('asteroid_classifier.models.registry.MlflowClient')
@patch('asteroid_classifier.models.registry.get_best_run')
@patch('asteroid_classifier.models.registry.check_promotion_thresholds')
def test_register_and_promote(mock_check, mock_get_best, mock_client_cls, mock_init, mock_run):
    mock_get_best.return_value = mock_run
    
    client_instance = mock_client_cls.return_value
    
    # Mock models logic
    client_instance.get_registered_model.return_value = MagicMock(latest_versions=[]) # Exists
    mv_mock = MagicMock()
    mv_mock.version = "1"
    client_instance.create_model_version.return_value = mv_mock
    
    register_and_promote(
        experiment_name="test-exp",
        model_name="TestModel",
        thresholds={"recall": 0.90},
        training_config={},
        dry_run=False
    )
    
    mock_check.assert_called_once_with({"cpu_utilization_end": 45.2, "memory_used_gb_end": 1.2, "recall": 0.95, "f1": 0.90}, {"recall": 0.90})
    
    # Check registration flow
    client_instance.create_model_version.assert_called_once()
    client_instance.set_registered_model_alias.assert_called_once_with(name="TestModel", alias="champion", version="1")
    client_instance.transition_model_version_stage.assert_called_once_with(
        name="TestModel",
        version="1",
        stage="Production",
        archive_existing_versions=False
    )
    client_instance.update_model_version.assert_called_once() # Enriched Metadata

@patch('asteroid_classifier.models.registry.init_registry')
@patch('asteroid_classifier.models.registry.MlflowClient')
@patch('asteroid_classifier.models.registry.get_best_run')
@patch('asteroid_classifier.models.registry.logger')
def test_register_and_promote_dry_run(mock_logger, mock_get_best, mock_client_cls, mock_init, mock_run):
    mock_get_best.return_value = mock_run
    client_instance = mock_client_cls.return_value
    
    register_and_promote(
        experiment_name="test-exp",
        model_name="TestModel",
        thresholds={"recall": 0.90}, # Fits with mock run (0.95)
        training_config={},
        dry_run=True
    )
    
    # Assert client side-effects were completely skipped
    client_instance.create_model_version.assert_not_called()
    client_instance.set_registered_model_alias.assert_not_called()
    client_instance.transition_model_version_stage.assert_not_called()
    client_instance.update_model_version.assert_not_called()

    calls_str = ' '.join(str(call) for call in mock_logger.info.call_args_list)
    assert "[DRY RUN]" in calls_str
    assert "Would update version" in calls_str
    assert "Would assign @champion alias to TestModel Version 999-dry-run" in calls_str

@patch('asteroid_classifier.models.registry.init_registry')
@patch('asteroid_classifier.models.registry.MlflowClient')
@patch('asteroid_classifier.models.registry.get_best_run')
@patch('asteroid_classifier.models.registry.check_promotion_thresholds')
def test_register_and_promote_fails_threshold(mock_check, mock_get_best, mock_client_cls, mock_init, mock_run):
    mock_get_best.return_value = mock_run
    client_instance = mock_client_cls.return_value
    
    # Simulate a threshold failure
    mock_check.side_effect = ModelPromotionError("Failed Threshold")
    
    with pytest.raises(ModelPromotionError):
        register_and_promote(
            experiment_name="test-exp",
            model_name="TestModel",
            thresholds={"recall": 0.99}, # Higher than 0.95
            training_config={},
            dry_run=False
        )
        
    client_instance.create_model_version.assert_not_called()
