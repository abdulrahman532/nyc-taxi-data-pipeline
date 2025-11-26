"""Airflow DAG for dbt transformations.

This DAG runs dbt models in the correct order:
staging → intermediate → marts (core → aggregations → insights)

It can be triggered manually or automatically after the sync DAG completes.
"""

import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.sdk import TaskGroup


# Configuration
DBT_PROJECT_DIR = os.path.expanduser("~/nyc-taxi-data-pipeline/nyc_taxi_dbt")
DBT_VENV_PATH = os.path.expanduser("~/nyc-taxi-data-pipeline/dbt_venv/bin/activate")

# Base command to activate venv and cd to project
DBT_BASE_CMD = f"source {DBT_VENV_PATH} && cd {DBT_PROJECT_DIR}"


default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="dbt_transformation_pipeline",
    description="Run dbt transformations after data sync",
    start_date=datetime(2025, 1, 1),
    schedule=None,  # Triggered by sync DAG or manually
    catchup=False,
    default_args=default_args,
    tags=["dbt", "transformation", "production"],
    doc_md=__doc__,
) as dag:

    # Start
    start = EmptyOperator(task_id="start")

    # Install dbt dependencies
    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"{DBT_BASE_CMD} && dbt deps",
    )

    # Staging layer
    with TaskGroup(group_id="staging") as staging_group:
        dbt_run_staging = BashOperator(
            task_id="dbt_run_staging",
            bash_command=f"{DBT_BASE_CMD} && dbt run --select staging",
        )
        
        dbt_test_staging = BashOperator(
            task_id="dbt_test_staging",
            bash_command=f"{DBT_BASE_CMD} && dbt test --select staging",
        )
        
        dbt_run_staging >> dbt_test_staging

    # Intermediate layer
    with TaskGroup(group_id="intermediate") as intermediate_group:
        dbt_run_intermediate = BashOperator(
            task_id="dbt_run_intermediate",
            bash_command=f"{DBT_BASE_CMD} && dbt run --select intermediate",
        )
        
        dbt_test_intermediate = BashOperator(
            task_id="dbt_test_intermediate",
            bash_command=f"{DBT_BASE_CMD} && dbt test --select intermediate",
        )
        
        dbt_run_intermediate >> dbt_test_intermediate

    # Marts layer
    with TaskGroup(group_id="marts") as marts_group:
        # Core models first (dimensions + OBT)
        dbt_run_core = BashOperator(
            task_id="dbt_run_core",
            bash_command=f"{DBT_BASE_CMD} && dbt run --select marts.core",
        )
        
        # Aggregations depend on core
        dbt_run_aggregations = BashOperator(
            task_id="dbt_run_aggregations",
            bash_command=f"{DBT_BASE_CMD} && dbt run --select marts.aggregations",
        )
        
        # Insights depend on core
        dbt_run_insights = BashOperator(
            task_id="dbt_run_insights",
            bash_command=f"{DBT_BASE_CMD} && dbt run --select marts.insights",
        )
        
        # Test all marts
        dbt_test_marts = BashOperator(
            task_id="dbt_test_marts",
            bash_command=f"{DBT_BASE_CMD} && dbt test --select marts",
        )
        
        dbt_run_core >> [dbt_run_aggregations, dbt_run_insights] >> dbt_test_marts

    # Generate docs
    dbt_docs = BashOperator(
        task_id="dbt_docs_generate",
        bash_command=f"{DBT_BASE_CMD} && dbt docs generate",
    )

    # End
    end = EmptyOperator(task_id="end")

    # Task dependencies
    start >> dbt_deps >> staging_group >> intermediate_group >> marts_group >> dbt_docs >> end
