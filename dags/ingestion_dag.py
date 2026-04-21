from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
import os

# To allow airflow to import our src logic
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from asteroid_classifier.data.ingestion import ingest_nasa_neo_data
from asteroid_classifier.data.validation import validate_neo_data
from asteroid_classifier.core.logging import get_logger

logger = get_logger()

def on_failure_callback(context):
    exception = context.get('exception')
    logger.error(f"DAG Execution Failed: {exception}")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'on_failure_callback': on_failure_callback
}

with DAG(
    'neo_ingestion_validation_dag',
    default_args=default_args,
    description='A daily DAG to ingest and validate NASA NEO data',
    schedule_interval='0 0 * * *',
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['ingestion'],
) as dag:

    def ingestion_task(**kwargs):
        logger.info("Executing Ingestion Task")
        output_path = ingest_nasa_neo_data()
        if output_path is None:
            raise ValueError("Ingestion returned None data. Halting.")
        # Push to XCom to pass path to validation
        kwargs['ti'].xcom_push(key='raw_csv_path', value=output_path)
        return output_path

    def validation_task(**kwargs):
        logger.info("Executing Validation Task")
        csv_path = kwargs['ti'].xcom_pull(key='raw_csv_path', task_ids='ingest_data')
        if not csv_path:
            raise ValueError("No CSV path found from ingestion task")
        validate_neo_data(csv_path)

    ingest_task = PythonOperator(
        task_id='ingest_data',
        python_callable=ingestion_task,
        provide_context=True
    )

    validate_task = PythonOperator(
        task_id='validate_data',
        python_callable=validation_task,
        provide_context=True
    )

    ingest_task >> validate_task
