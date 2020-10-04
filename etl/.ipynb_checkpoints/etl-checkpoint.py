import configparser
import os
from datetime import datetime, timedelta
from pyspark.sql import functions as F
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, regexp_replace
from pyspark.sql.functions import year, month, dayofmonth, hour, weekofyear, date_format, dayofweek, to_date, date_format, unix_timestamp
from pyspark.sql.types import TimestampType, IntegerType, DateType, FloatType, StringType


config = configparser.ConfigParser()
config.read('etl/dl.cfg')

os.environ['AWS_ACCESS_KEY_ID']=config['AWS']['AWS_ACCESS_KEY_ID']
os.environ['AWS_SECRET_ACCESS_KEY']=config['AWS']['AWS_SECRET_ACCESS_KEY']

def create_spark_session():
    """
    This function creates Spark Session
    """
    spark = SparkSession.builder.config("spark.jars.packages",
                                        "saurfang:spark-sas7bdat:2.0.0-s_2.11,org.apache.hadoop:hadoop-aws:2.7.0")\
    .enableHiveSupport().getOrCreate()
    return spark


def etl_immigration(spark, 
                    input_data='../../data/18-83510-I94-Data-2016/i94_apr16_sub.sas7bdat', 
                    output_path="s3://zafarsohaib/immigrationt"):
    """ ETL process for immigration data
    """
    # read immigration data file
    df = spark.read.load(input_data, format="com.github.saurfang.sas.spark")
    dateformat = "%Y-%m-%d"
    # Convert SAS Date into date format
    convert_sas_date = udf(lambda x: x if x is None else (timedelta(days=x) + datetime(1960, 1, 1)).strftime(dateformat))
    
    # Converting data types
    df = df.withColumn("arrdate", convert_sas_date(df.arrdate))
    df = df.withColumn("depdate", convert_sas_date(df.depdate))
    df = df.withColumn("i94yr", df.i94yr.cast(IntegerType()))
    df = df.withColumn("i94mon", df.i94mon.cast(IntegerType()))
    df = df.withColumn("i94mode", df.i94mode.cast(IntegerType()))
    df = df.withColumn("biryear", df.biryear.cast(IntegerType()))
    df = df.withColumn("i94res", df.i94res.cast(IntegerType()))
    df = df.withColumn("i94visa", df.i94visa.cast(IntegerType()))
    df = df.withColumn("cicid", df.cicid.cast(IntegerType()))
    #df = df.withColumn("dtaddto", df.dtaddto.cast("date"))
    
    # Immigration Table Temporary View
    df.createOrReplaceTempView("immigration_table")
    
    # extract columns to create immigration table
    immigration_table = spark.sql(""" 
        select distinct cicid as ID, i94yr as YEAR, i94mon as MONTH, arrdate as ARR_DATE, depdate as DEP_DATE, 
        i94port as ARR_CITYCODE, i94addr as ARR_STATECODE, i94mode as ARR_MODE, fltno as ARR_FLIGHT, airline as ARR_AIRLINE, 
        biryear as RES_BIRTHYEAR, i94res as RES_COUNTRYCODE, gender as RES_GENDER, 
        dtaddto as VISA_EXPIRYDATE, visapost as VISA_ISSUESTATE, i94visa as VISA_CATEGORY, visatype as VISA_TYPE
        from immigration_table    
        """)
    
    # write immigration table to parquet files can be partitioned by year and month
    immigration_table.write.parquet(output_path, mode='overwrite') #, partitionBy=["YEAR", "MONTH"])
    return immigration_table

def etl_temperature_by_country(spark, 
                  input_data='../../data2/GlobalLandTemperaturesByCity.csv', 
                  label_data="i94_labels/I94CIT_I94RES.csv",
                  output_path="s3://udacity-capstone-project-outputs/country_temperature"):
    """ ETL process for countries temperature data
        - Loads of the csv file of the global temperature and I94CIT_I94RES labels
        - Aggregates the temperatures dataset by country and rename new columns
        - Join the two datasets based on Country Name
        - Save the resulting parquet file to the staging area in Amazon S3
    """
    # read temperature data file
    df = spark.read.csv(input_data, header=True)
    df = df.withColumn("AverageTemperature", df.AverageTemperature.cast(FloatType()))
    # Temperature Table Temporary View
    df.createOrReplaceTempView("t1")

    # extract columns to create songs table
    temperature_by_country = spark.sql(""" 
        select distinct UPPER(Country) as Country, round(avg(AverageTemperature), 4) as AverageTemperature, 
        first(Latitude) as Latitude, first(Longitude) as Longitude
        from t1   
        group by country
        """)
    # read country codes file
    df2 = spark.read.csv(label_data, header=True)

    country_temperature_table = temperature_by_country.join(df2, on="Country")
    country_temperature_table = country_temperature_table.withColumn("Code", country_temperature_table.Code.cast(IntegerType()))
    country_temperature_table.write.parquet(output_path, mode='overwrite')
    #country_temperature_table.write.save(output_path, mode='overwrite', format="parquet")
    return country_temperature_table

def etl_state_demographics(spark, 
                          input_data="us-cities-demographics.csv", 
                          label_data="i94_labels/I94ADDR.csv",
                          output_path="s3://udacity-capstone-project-outputs/state_demographics"):
    """ ETL process for state demographics data
        - Loads the csv file of the state demographics and I94ADDR labels
        - Aggregates the demographics dataset by state and rename new columns
        - Join the two datasets based on State Name
        - Save the resulting parquet file to the staging area in Amazon S3
    """
    # read temperature data file
    df = spark.read.csv(input_data, header=True, sep=";")
    
    df = df.withColumn("Male_Population", df["Male Population"].cast(IntegerType()))
    df = df.withColumn("Female_Population", df["Female Population"].cast(IntegerType()))
    df = df.withColumn("Total_Population", df["Total Population"].cast(IntegerType()))
    df = df.withColumn("Veterans", df["Number of Veterans"].cast(IntegerType()))
    df = df.withColumn("Foreign_born", df["Foreign-born"].cast(IntegerType()))
    # Temperature Table Temporary View
    df.createOrReplaceTempView("t1")

    # extract columns to create songs table
    state_demographics = spark.sql(""" 
        select distinct UPPER(State) as State, 
        sum(Male_Population) as Male_Population, 
        sum(Female_Population) as Female_Population, 
        sum(Total_Population) as Total_Population,
        sum(Veterans) as Veterans,
        sum(Foreign_born) as Foreign_born
        from (
            select distinct city, State, Male_Population, Female_Population, Total_Population, Veterans, Foreign_born
            from t1 
        )  
        group by State
        order by Total_Population desc
        """)

    # read country codes file
    df2 = spark.read.csv(label_data, header=True)
    
    state_demographics_table = state_demographics.join(df2, on="State")
    state_demographics_table = state_demographics_table.withColumn("Code", state_demographics_table.Code.cast(StringType()))
    state_demographics_table.write.parquet(output_path, mode='overwrite')
    return state_demographics_table

def main():
    print(os.environ['AWS_ACCESS_KEY_ID'], os.environ['AWS_SECRET_ACCESS_KEY'])
    spark = create_spark_session()

    immigration_table = etl_immigration(spark)    
    country_temperature_table = etl_temperature_by_country(spark)
    state_demographics_table = etl_state_demographics(spark)

    spark.stop()

if __name__ == "__main__":
    main()
