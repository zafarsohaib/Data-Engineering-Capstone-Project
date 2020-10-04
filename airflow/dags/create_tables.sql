DROP TABLE IF EXISTS immigration;
DROP TABLE IF EXISTS country_temperature;
DROP TABLE IF EXISTS state_demographics;

CREATE TABLE immigration (   
    ID int NOT NULL, 
    YEAR int, 
    MONTH int,
    ARR_DATE varchar, 
    DEP_DATE varchar, 
    ARR_CITYCODE varchar, 
    ARR_STATECODE varchar, 
    ARR_MODE int, 
    ARR_FLIGHT varchar, 
    ARR_AIRLINE varchar, 
    RES_BIRTHYEAR int, 
    RES_COUNTRYCODE int, 
    RES_GENDER varchar, 
    VISA_EXPIRYDATE varchar, 
    VISA_ISSUESTATE varchar, 
    VISA_CATEGORY int, 
    VISA_TYPE varchar,
    CONSTRAINT immi_pkey PRIMARY KEY (ID)
);

CREATE TABLE country_temperature (  
    Country varchar, 
    AverageTemperature float, 
    Latitude varchar, 
    Longitude varchar,
    Code int NOT NULL,
    CONSTRAINT country_pkey PRIMARY KEY (Code)
) diststyle all;

CREATE TABLE state_demographics (
    State varchar, 
    Male_Population bigint, 
    Female_Population bigint, 
    Total_Population bigint, 
    Veterans bigint, 
    Foreign_born bigint,
    Code varchar NOT NULL,
    CONSTRAINT state_pkey PRIMARY KEY (Code)
) diststyle all;
