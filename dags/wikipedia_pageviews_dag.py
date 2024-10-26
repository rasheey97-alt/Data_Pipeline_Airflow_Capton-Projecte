from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime
import requests
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

POSTGRES_USER = os.getenv('rasheey97')
POSTGRES_PASSWORD = os.getenv('1234')


# Default arguments for DAG
default_args = {
    'owner': 'Rasheed',
    'start_date': datetime(2024, 10, 18),
    'retries': 1,
}

# Initialize the DAG
dag = DAG(
    'wikipedia_pageviews_dag',
    default_args=default_args,
    schedule_interval='@hourly',
    catchup=False
)

# Task 1: Download Wikipedia Pageviews Data
def download_wikipedia_data(execution_date, **kwargs):
    url = f"https://dumps.wikimedia.org/other/pageviews/{execution_date.year}/{execution_date.month:02}/pageviews-{execution_date.strftime('%Y%m%d')}-210000.gz"
    response = requests.get(url)
    with open('/tmp/pageviews.gz', 'wb') as file:
        file.write(response.content)

download_task = PythonOperator(
    task_id='download_wikipedia_data',
    python_callable=download_wikipedia_data,
    provide_context=True,
    dag=dag
)

# Task 2: Extract the downloaded .gz file
extract_task = BashOperator(
    task_id='extract_file',
    bash_command='gunzip /tmp/pageviews.gz',
    dag=dag
)

# Task 3: Fetch Pageviews for Selected Companies
def fetch_pageviews(**kwargs):
    selected_companies = ['Amazon', 'Apple', 'Facebook', 'Google', 'Microsoft']
    with open('/tmp/pageviews', 'r') as file:
        for line in file:
            data = line.split()
            domain_code = data[0]
            page_title = data[1]
            view_count = data[2]

            if page_title in selected_companies:
                # Print or save the relevant information
                print(f"Company: {page_title}, Views: {view_count}")

fetch_pageviews_task = PythonOperator(
    task_id='fetch_pageviews',
    python_callable=fetch_pageviews,
    dag=dag
)

# Load Data into a PostgreSQL Database (if needed)
load_data_task = PostgresOperator(
    task_id='load_data_to_db',
    postgres_conn_id='24577',  # Connection configured in Airflow UI
    sql="""
    INSERT INTO pageviews_table (company, views, load_date)
    VALUES ('Amazon', 12345, '{{ execution_date }}');
    """,
    dag=dag,
)

# Define task dependencies
download_task >> extract_task >> fetch_pageviews_task

# If loading into a database
# fetch_pageviews_task >> load_data_task
