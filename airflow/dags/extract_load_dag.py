from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from extract import arms_extractor, exat_extractor, loader

default_args = {
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="extract_load_dag",
    description="ดึงข้อมูล ARMS/EXAT (Issue 04) แล้วโหลดเข้า Postgres raw layer (Issue 05)",
    default_args=default_args,
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["extract", "load"],
) as dag:

    extract_arms = PythonOperator(
        task_id="extract_arms",
        python_callable=arms_extractor.main,
    )

    extract_exat = PythonOperator(
        task_id="extract_exat",
        python_callable=exat_extractor.main,
    )

    load_raw = PythonOperator(
        task_id="load_raw",
        python_callable=loader.main,
    )

    [extract_arms, extract_exat] >> load_raw
