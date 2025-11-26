"""Airflow DAG for NYC Taxi data synchronization.

After successful data load, triggers the dbt transformation pipeline.
"""

import os
import sys
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.standard.operators.python import BranchPythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

sys.path.append(os.path.expanduser("~/airflow/dags/scripts"))
from sync_manager import smart_sync_logic


def execute_sync_and_branch(**context):
    files = smart_sync_logic()
    if files:
        context["ti"].xcom_push(key="files_to_load", value=", ".join([f"'{f}'" for f in files]))
        return "load_to_snowflake"
    return "skip_load"


with DAG(
    dag_id="nyc_taxi_sync_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule="0 0 15 * *",
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=2)},
    tags=["production", "etl"],
) as dag:

    sync = BranchPythonOperator(task_id="sync_and_check", python_callable=execute_sync_and_branch)
    
    load = SQLExecuteQueryOperator(
        task_id="load_to_snowflake",
        conn_id="snowflake_default",
        sql="""
            COPY INTO NYC_TAXI_DB.RAW.TRIPS
            FROM @NYC_TAXI_DB.RAW.NYC_TAXI_S3_STAGE
            FILES = ({{ ti.xcom_pull(task_ids='sync_and_check', key='files_to_load') }})
            FILE_FORMAT = (FORMAT_NAME = 'NYC_TAXI_DB.RAW.PARQUET_FORMAT')
            MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
            ON_ERROR = 'CONTINUE';
        """,
    )
    
    # Trigger dbt transformations after successful load
    trigger_dbt = TriggerDagRunOperator(
        task_id="trigger_dbt_pipeline",
        trigger_dag_id="dbt_transformation_pipeline",
        wait_for_completion=False,
        poke_interval=30,
    )
    
    skip = EmptyOperator(task_id="skip_load")
    
    sync >> [load, skip]
    load >> trigger_dbt
