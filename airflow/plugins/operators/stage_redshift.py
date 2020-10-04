from airflow.contrib.hooks.aws_hook import AwsHook
from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

class StageToRedshiftOperator(BaseOperator):
    """ Copying data from S3 to Redshift
    """
    ui_color = '#358140'

    @apply_defaults
    def __init__(self,
                 aws_credentials_id="",
                 redshift_conn_id="",
                 table="",
                 s3_bucket="",
                 s3_key="",
                 region="",
                 file_format="PARQUET",
                 *args, **kwargs):

        super(StageToRedshiftOperator, self).__init__(*args, **kwargs)
        self.aws_credentials_id = aws_credentials_id
        self.redshift_conn_id = redshift_conn_id
        self.table = table
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.file_format = file_format
        self.region = region
        
    def execute(self, context):
        """ Execute copying of data from S3 to Redshift
        """
        aws_hook = AwsHook(self.aws_credentials_id)
        credentials = aws_hook.get_credentials()
        redshift = PostgresHook(postgres_conn_id=self.redshift_conn_id)
        s3_path = f"s3://{self.s3_bucket}/{self.s3_key}"
        self.log.info(f"Copying data from S3 {s3_path} to Redshift table {self.table}")
        cmd = f"COPY {self.table} FROM '{s3_path}' ACCESS_KEY_ID '{credentials.access_key}' SECRET_ACCESS_KEY" \
        f" '{credentials.secret_key}' FORMAT AS PARQUET COMPUPDATE OFF"
        redshift.run(cmd)
