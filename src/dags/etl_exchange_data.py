from __future__ import annotations

import json
import os
import sys
from datetime import datetime

import requests
from airflow.models import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'retries': 0,
    # 'retry_delay': None,
}


def get_exchange_data(ti, **kwargs):
    url = 'https://api.coincap.io/v2/exchanges'
    try:
        r = requests.get(url)
    except requests.ConnectionError as ce:
        print(f"Error:  There was an error with the request, {ce}")
        sys.exit(1)
    if r.status_code == 200:
        # Get json data
        json_data = r.json().get('data', [])
        file_name = str(datetime.now().strftime('%Y%m%d-%H%M%S'))+'.json'
        abs_path = os.path.join(
            os.path.dirname(__file__),
            'data',
            file_name,
        )
        # Create folder if not exists
        if not os.path.exists(os.path.join(os.path.dirname(__file__), 'data')):
            os.mkdir(os.path.join(os.path.dirname(__file__), 'data'))
        # Dump json data
        with open(abs_path, 'w') as op_file:
            json.dump(json_data, op_file)
        ti.xcom_push(key='filepath', value=abs_path)
        print(f"Pushed {abs_path} to xcom")
    else:
        print(f"Error:  {r.text}")


def insert_records(ti, **kwargs):
    pg_hook = PostgresHook(
        postgres_conn_id='btc_postgres_connection', schema='btc_exchange_data',
    )
    connection = pg_hook.get_conn()
    cursor = connection.cursor()
    # file_name = str(datetime.now().strftime("%Y%m%d-%H%M%S"))+'.json'
    abs_path = ti.xcom_pull(task_ids=['get_exchange_data'], key='filepath')[0]
    print(f"Path recieved as {abs_path}")
    # Dump json data
    with open(abs_path, 'rb') as data_file:
        res = json.load(data_file)
    res = list(res)
    ts = str(datetime.now().astimezone())
    for record in res:
        if not record['percentTotalVolume'] or \
                record['percentTotalVolume'] == 'None':
            record['percentTotalVolume'] = 0

        if not record['volumeUsd'] or record['volumeUsd'] == 'None':
            record['volumeUsd'] = 0
        cursor.execute(
            f'''INSERT INTO bitcoin_exchange.exchange
                       (
                            id,
                            name,
                            rank,
                            percenttotalvolume,
                            volumeusd,
                            tradingpairs,
                            socket,
                            exchangeurl,
                            updated_unix_millis,
                            updated_utc
                       )
                       VALUES (
                            '{record['exchangeId']}',
                            '{record['name']}',
                            {int(record['rank'])},
                            {float(record['percentTotalVolume'])},
                            {float(record['volumeUsd'])},
                            {int(record['tradingPairs'])},
                            {bool(record['socket'])},
                            '{record['exchangeUrl']}',
                            0,
                            '{ts}'
                        )''',
        )

    connection.commit()
    cursor.close()
    connection.close()


with DAG(
    'etl_exchange_data',
    default_args=default_args,
    schedule_interval='*/5 * * * *',
    catchup=False,
) as dag:
    """A dag that run's every 5 mins to collect exhange data \
        from CoinCap API."""

    # Get exchange data from API
    get_data_task = PythonOperator(
        task_id='get_exchange_data',
        python_callable=get_exchange_data,
        provide_context=True,
        dag=dag,
    )

    # Insert data in sql database
    execute_query_task = PythonOperator(
        task_id='insert_data_to_sql',
        python_callable=insert_records,
        provide_context=True,
        dag=dag,
    )

    get_data_task >> execute_query_task
