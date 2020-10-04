from datetime import datetime, timedelta
import os
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator

from airflow.operators.postgres_operator import PostgresOperator
from airflow.operators import StageToRedshiftOperator, DataQualityOperator


default_args = {
    'owner': 'Capstone_Project',
    'start_date': datetime(2019, 1, 12),
}

dag = DAG('capstone_dag',
          default_args=default_args,
          description='Stage from S3 to Redshift with Airflow',
          schedule_interval='*/10 * * * *',#'0 * * * *',
          max_active_runs = 1,
          catchup = False
        )

start_operator = DummyOperator(task_id='Begin_execution',  dag=dag)

create_table = PostgresOperator(
    task_id="Create_Tables",
    dag=dag,
    postgres_conn_id="redshift",
    sql="create_tables.sql"
)

stage_immigration_to_redshift = StageToRedshiftOperator(
    task_id='Load_Immigration_Fact_Table',
    dag=dag,
    aws_credentials_id="aws_credentials",
    redshift_conn_id="redshift",
    table="Immigration",
    s3_bucket="zafarsohaib",
    s3_key="immigration",
    file_type="PARQUET"
)

stage_country_temperature_to_redshift = StageToRedshiftOperator(
    task_id='Load_Country_Temperature_Dimension_Table',
    dag=dag,
    aws_credentials_id="aws_credentials",
    redshift_conn_id="redshift",
    table="Country_Temperature",
    s3_bucket="zafarsohaib",
    s3_key="country_temperature",
    file_type="PARQUET"
)

stage_state_demographics_to_redshift = StageToRedshiftOperator(
    task_id='Load_State_Demographics_Dimension_Table',
    dag=dag,
    aws_credentials_id="aws_credentials",
    redshift_conn_id="redshift",
    table="State_Demographics",
    s3_bucket="zafarsohaib",
    s3_key="state_demographics",
    file_type="PARQUET"
)

run_quality_checks = DataQualityOperator(
    task_id='Run_Data_Quality_checks',
    dag=dag,
    redshift_conn_id="redshift",
    tables=["Immigration","Country_Temperature","State_Demographics"],
)

end_operator = DummyOperator(task_id='Stop_execution',  dag=dag)

start_operator >>  create_table
create_table >> stage_immigration_to_redshift
stage_immigration_to_redshift >> stage_country_temperature_to_redshift
stage_immigration_to_redshift >> stage_state_demographics_to_redshift
stage_state_demographics_to_redshift >> run_quality_checks
stage_country_temperature_to_redshift >> run_quality_checks
run_quality_checks >> end_operator
