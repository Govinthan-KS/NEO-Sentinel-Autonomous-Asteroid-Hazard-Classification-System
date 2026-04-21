import pytest
from loguru import logger
from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError

from asteroid_classifier.data.ingestion import ingest_nasa_neo_data
from asteroid_classifier.core.exceptions import DataIngestionError


@pytest.fixture
def custom_sink():
    class Sink:
        def __init__(self):
            self.messages = []

        def write(self, message):
            self.messages.append(message)

    sink = Sink()
    handler_id = logger.add(
        sink,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {module} | {function} | {line} | {message}",
    )
    yield sink
    logger.remove(handler_id)


@patch("asteroid_classifier.data.ingestion.requests.get")
@patch("asteroid_classifier.data.ingestion.get_config")
def test_ingestion_403_forbidden_logs_correctly(mock_get_config, mock_get, custom_sink):
    # Setup mock config
    mock_cfg = MagicMock()
    mock_cfg.data.nasa_neows_api.base_url = "http://test.com"
    mock_cfg.data.nasa_neows_api.timeout_seconds = 30
    mock_cfg.data.storage.raw_data_dir = "data/raw"
    mock_cfg.data.nasa_neows_api.api_key = "FAKE_KEY"
    mock_get_config.return_value = mock_cfg

    # Setup mock 403 response
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = HTTPError("403 Forbidden")
    mock_get.return_value = mock_response

    with pytest.raises(DataIngestionError) as exc_info:
        ingest_nasa_neo_data()

    assert "HTTP Request failed" in str(exc_info.value)

    # Verify exact loguru format exists in sink
    error_message_found = False
    for msg in custom_sink.messages:
        # Check standard ERROR injection logic
        if "403 Forbidden" in msg and "ERROR" in msg:
            error_message_found = True
            # Assert proper formatting adherence from specs
            assert "| ERROR    | ingestion | ingest_nasa_neo_data |" in msg

    assert (
        error_message_found
    ), "DataIngestionError format check failed in logs. Observability is compromised."
