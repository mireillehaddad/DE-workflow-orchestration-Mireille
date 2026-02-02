# Module 2 Homework – Workflow Orchestration with Kestra

This homework extends the existing NYC Taxi ingestion pipelines to include **2021 data** using **Kestra** and **Google Cloud Platform (GCS + BigQuery)**.

The solution is implemented using two Kestra flows in the `zoomcamp` namespace:

- `07_gcp_setup`
- `hw_gcp_taxi_scheduled`
- `10_manual_gcp_taxi`
---

## 1. GCP Setup Flow (`07_gcp_setup`)

This flow is responsible for initializing all required Google Cloud resources and configuration using Kestra’s **KV Store**.

### What this flow does
- Stores the following values in Kestra KV:
  - `GCP_PROJECT_ID = calm-snowfall-485503-b4`
  - `GCP_LOCATION = northamerica-northeast1`
  - `GCP_BUCKET_NAME = calm-snowfall-485503-b4-terra-bucket`
  - `GCP_DATASET = demo_dataset_ny_taxi`
- Creates the GCS bucket (if it does not already exist)
- Creates the BigQuery dataset (if it does not already exist)
- Defines `pluginDefaults` so all GCP plugins reuse the same configuration

### Why this is useful
- Centralizes configuration
- Avoids hardcoding values in multiple flows
- Makes the ingestion flow reusable and environment-agnostic

---

## 2. Scheduled Taxi Ingestion Flow (`hw_gcp_taxi_scheduled`)

This flow ingests **monthly green and yellow taxi data** from the DataTalksClub GitHub repository into BigQuery.

### Input parameters
- `taxi`: `green` or `yellow`

### Date handling
The flow dynamically determines the target month:
- Uses `trigger.date` for scheduled runs and backfills
- Uses `execution.startDate` for manual runs

This allows the same flow to work in all execution modes.

---

## 3. Ingestion Logic (Per Execution)

Each execution performs the following steps:

1. Download the monthly `*.csv.gz` taxi file from GitHub
2. Unzip the file locally
3. Upload the CSV file to Google Cloud Storage
4. Create a BigQuery external table pointing to the GCS file
5. Create a temporary monthly table
6. Merge the data into the final partitioned table:
   - `demo_dataset_ny_taxi.green_tripdata`
   - `demo_dataset_ny_taxi.yellow_tripdata`

Partitioning is done by pickup date to support efficient querying.

---

## 4. Extending the Pipeline to 2021 (Homework Requirement)

The original pipeline only handled 2019 and 2020 data.  
To load **2021 data**, Kestra’s **Backfill** feature was used.

### Backfill configuration
- Start date: `2021-01-01`
- End date: `2021-07-31`
- Taxi types:
  - One backfill run with `taxi = green`
  - One backfill run with `taxi = yellow`

Kestra automatically triggered one execution per month, loading all available 2021 data without manual intervention.

---

## 5. Verification Queries

After backfill completion, the following queries were used to verify that 2021 data was successfully loaded.


---


### Green taxi (Jan–Jul 2021)
```sql
SELECT COUNT(*) AS rows_2021_green
FROM `calm-snowfall-485503-b4.demo_dataset_ny_taxi.green_tripdata`
WHERE DATE(lpep_pickup_datetime) BETWEEN '2021-01-01' AND '2021-07-31';
```
## 6. Manual Taxi Ingestion Flow (10_manual_gcp_taxi)

This flow is designed to execute taxi ingestion manually by explicitly providing the taxi type, year, and month as inputs.
It was mainly used to validate data, inspect intermediate results, and answer homework questions that require per-month inspection.

Input parameters

taxi: green or yellow

year: integer (e.g. 2020, 2021)

month: two-digit string (e.g. 01, 12)

Unlike the scheduled flow, this flow does not rely on triggers or backfill.
Each execution processes exactly one taxi file for one specific month.

6. What the Manual Flow Does (Step by Step)

Each manual execution performs the following actions:

Builds the target filename dynamically using inputs:

Example: yellow_tripdata_2020-12.csv

Downloads the corresponding .csv.gz file from GitHub

Uncompresses the file locally

Logs the uncompressed file size using ls -lh

Uploads the CSV file to Google Cloud Storage

Creates a BigQuery external table pointing to the uploaded file

Creates a temporary monthly table

Merges the data into the final partitioned table:

demo_dataset_ny_taxi.yellow_tripdata

demo_dataset_ny_taxi.green_tripdata

This flow mirrors the scheduled ingestion logic but allows full control and observability per execution.

7. How the Manual Flow Was Used to Answer Homework Questions
Question:

“What is the rendered value of the variable file when taxi=green, year=2020, month=04?”

Steps:

Execute the manual flow with:

taxi = green

year = 2020

month = 04

Observe the computed filename in the execution labels and logs

Result:

green_tripdata_2020-04.csv


## Question1: 

Within the execution for Yellow Taxi data for the year 2020 and month 12: what is the uncompressed file size (i.e. the output file yellow_tripdata_2020-12.csv of the extract task)?
128.3 MiB
134.5 MiB
364.7 MiB
692.6 MiB

## Answer1: 

Steps to verify the uncompressed file size for

Yellow Taxi – December 2020

1. Open Kestra UI

Go to http://localhost:8080 (or your Kestra URL)

2. Navigate to the correct flow

Click Namespaces

Click zoomcamp

Click the flow hw_gcp_taxi_scheduled

3. Run the flow for December 2020 (manual execution)

Click Execute

Set:

taxi = yellow

(If your flow uses execution date fallback)

Set Execution date to:
2020-12-01

Click Execute

4. Wait for execution to start

The execution will appear in the Executions list

Click on the latest execution ID

5. Open the extract task

Inside the execution view:

Click Tasks

Click extract

This is the task that downloads and unzips the file.

6. Read the logs carefully

Scroll in the Logs panel until you see:

Downloading: https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2020-12.csv.gz


A few lines later you will see:

-rw-r--r-- 1 root root 134.5M yellow_tripdata_2020-12.csv

The answer is 134.5MiB


## Question2: 

What is the rendered value of the variable file when the inputs taxi is set to green, year is set to 2020, and month is set to 04 during execution?
{{inputs.taxi}}_tripdata_{{inputs.year}}-{{inputs.month}}.csv
green_tripdata_2020-04.csv
green_tripdata_04_2020.csv
green_tripdata_2020.csv

## Answer2: 
{{inputs.taxi}}_tripdata_{{inputs.year}}-{{inputs.month}}.csv
Inputs:

taxi = green

year = 2020

month = 04

green_tripdata_2020-04.csv

## Question3: 

How many rows are there for the Yellow Taxi data for all CSV files in the year 2020?
13,537.299
24,648,499
18,324,219
29,430,127

## Answer3: 
```sql
SELECT COUNT(*) AS rows_2020
FROM `calm-snowfall-485503-b4.demo_dataset_ny_taxi.yellow_tripdata`
WHERE DATE(tpep_pickup_datetime) >= '2020-01-01'
  AND DATE(tpep_pickup_datetime) < '2021-01-01';
```
  Answer is 24,648,499

  ## Question4:
  How many rows are there for the Green Taxi data for all CSV files in the year 2020?
5,327,301
936,199
1,734,051
1,342,034

 ## Answer4:
 ```sql
 SELECT COUNT(*) AS total_rows
FROM `calm-snowfall-485503-b4.demo_dataset_ny_taxi.green_tripdata`
WHERE EXTRACT(YEAR FROM lpep_pickup_datetime) = 2020;
```
1,734,051

##  Question5:
 How many rows are there for the Yellow Taxi data for the March 2021 CSV file?
1,428,092
706,911
1,925,152
2,561,031

 ## Answer5:
 ```sql
SELECT COUNT(*) AS row_count
FROM `calm-snowfall-485503-b4.demo_dataset_ny_taxi.yellow_tripdata`
WHERE filename = 'yellow_tripdata_2021-03.csv';
```
The answer is 1,925,152

## Question 6: How would you configure the timezone to New York in a Schedule trigger?
Add a timezone property set to EST in the Schedule trigger configuration
Add a timezone property set to America/New_York in the Schedule trigger configuration
Add a timezone property set to UTC-5 in the Schedule trigger configuration
Add a location property set to New_York in the Schedule trigger configuration

## Answer 6:
Add a timezone property set to America/New_York in the Schedule trigger configuration

example: triggers:
  - id: monthly_yellow
    type: io.kestra.plugin.core.trigger.Schedule
    cron: "0 9 1 * *"
    timezone: America/New_York
    inputs:
      taxi: yellow