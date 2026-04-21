from airflow.models import DagBag


def test_ingestion_dag_structure_and_xcom():
    # Load Dags dynamically
    dagbag = DagBag(dag_folder="dags/", include_examples=False)
    # Ensure no python syntax errors in ingestion_dag.py
    assert not dagbag.import_errors, f"DAG import errors: {dagbag.import_errors}"

    dag = dagbag.get_dag("neo_ingestion_validation_dag")
    assert dag is not None

    # Check tasks exist mapping standard logic
    ingest_task = dag.get_task("ingest_data")
    validate_task = dag.get_task("validate_data")

    # Assert proper isolation and dependencies (Validation downstream of Ingestion)
    assert ingest_task.task_id in [t.task_id for t in validate_task.upstream_list]

    # Validate PythonOperators provide XCom contexts natively
    assert validate_task.provide_context is True
    assert ingest_task.provide_context is True
