"""Airflow DAG for Lambda infrastructure deployment."""

import os
from datetime import datetime
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator

PROJECT_DIR = os.path.expanduser("~/nyc-taxi-data-pipeline/infrastructure")
VENV_PYTHON = os.path.join(PROJECT_DIR, "venv/bin/python3")

with DAG(
    dag_id="deploy_lambda_infrastructure",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["infrastructure", "admin"],
) as dag:
    BashOperator(
        task_id="deploy_lambda",
        bash_command=f"cd {PROJECT_DIR} && {VENV_PYTHON} deploy_lambda.py",
    )
