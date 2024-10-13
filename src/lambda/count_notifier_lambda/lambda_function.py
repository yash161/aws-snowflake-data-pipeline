import psycopg2
import os
import json
import snowflake.connector
from src.utils.notification_utils import SendNotification
from src.utils.snowflake_utils import SnowflakeDatabaseManager
from src.utils.postgres_utils import PostgresDatabaseManager
from src.utils.notification_utils import SendNotification


# Function to get table counts from PostgreSQL database
def compare_count(finale_json_list):
    mismatches = []
    mismatch_results = []  # Initialize a list to store mismatch information

    for data in finale_json_list:
        if data['postgres_count'] != data['snowflake_count']:
            data['count_difference'] = data['postgres_count'] - data['snowflake_count']
            mismatches.append(data)

    if mismatches:
        for mismatch in mismatches:
            mismatch_result = f"Table: {mismatch['table']}, Postgres Count: {mismatch['postgres_count']}, Snowflake Count: {mismatch['snowflake_count']}, Count Difference: {mismatch['count_difference']}"
            mismatch_results.append(mismatch_result)

        return "Count mismatches found in the following tables:\n" + "\n".join(mismatch_results)
    else:
        return "No count mismatches found in the tables."


def get_postgres_table_counts(secret_name, database):
    postgres_databse_manager = PostgresDatabaseManager(secret_name=secret_name)
    conn, cursor = postgres_databse_manager.get_postgres_connection(database=database)
    json_data = {}
    cursor.execute(f'''
       WITH tbl AS
  (SELECT table_schema,
          TABLE_NAME
   FROM information_schema.tables
   WHERE TABLE_NAME NOT LIKE 'pg_%'
     AND table_schema IN ('public')
     AND table_catalog = '{database}'
    )  
SELECT table_schema,
       TABLE_NAME,
       (xpath('/row/c/text()', query_to_xml(format('SELECT count(*) as c FROM %I.%I', table_schema, TABLE_NAME), FALSE, TRUE, '')))[1]::text::int AS rows_n
FROM tbl
ORDER BY rows_n DESC;
    ''')

    result = cursor.fetchall()
    print("Starting to iterate over result:::::")
    # print(result)
    for row in result:
        schema_name = row[0]
        table_name = row[1]
        row_count = row[2]
        json_data[table_name] = row_count

    cursor.close()
    conn.close()
    # print(json_data)
    return json_data


# Function to get table counts from Snowflake
def get_count_of_table_snowflake(conn, schema_name, table_name):
    cursor = conn.cursor()
    try:
        cursor.execute(
            f'''SELECT COUNT(*) FROM "{schema_name.upper()}"."{table_name.upper()}" WHERE _FIVETRAN_DELETED = FALSE;'''
        )
        result = cursor.fetchall()
    except Exception as e:
        print("Error in [get_snowflake_table_counts]: ", e)
        result = None

    if result is not None and len(result) > 0:
        if len(result[0]) > 0:
            return result[0][0]
        else:
            return 0
    else:
        return 0


def get_snowflake_table_counts():
    snowflake_manager = SnowflakeDatabaseManager(os.environ['snowflake_secret_name'])
    conn = snowflake_manager.get_snowflake_connection(database=os.getenv("SNOWFLAKE_METADATA_DATABASE_NAME"))

    schema_list = ["CONNECT_POSTGRES_PUBLIC", "INT_STG_PUBLIC"]
    snowflake_json = {}
    cursor = conn.cursor()

    for schema_name in schema_list:
        json_data = {}
        cursor.execute(
            f"SELECT t.table_schema || '.' || t.table_name AS table_name, t.row_count FROM information_schema.tables t WHERE t.table_type = 'BASE TABLE' AND t.table_schema = '{schema_name}' ORDER BY t.row_count DESC;"
        )
        result = cursor.fetchall()

        for row in result:
            table_name = row[0].split(".")[1]
            row_count = row[1]
            json_data[table_name.lower()] = row_count

        snowflake_json[schema_name.lower()] = json_data

    cursor.close()
    conn.close()

    return snowflake_json


def lambda_handler(event, context):
    # Retrieve environment variables and secrets from AWS Lambda environment
    sns_secret_name = os.environ["sns_secret_name"]
    connect_postgres_secret_name = os.environ["connect_postgres_secret_name"]
    aidbox_postgres_secret_name = os.environ["aidbox_postgres_secret_name"]

    # Call your functions to get data
    connect_postgres_json = get_postgres_table_counts(secret_name=connect_postgres_secret_name, database='prod-db')
    aidbox_postgres_json = get_postgres_table_counts(secret_name=aidbox_postgres_secret_name, database='curve')
    snowflake_json = get_snowflake_table_counts()

    # Perform the same data processing steps as before
    finale_json_list = []
    key_list = list(connect_postgres_json.keys()) + list(aidbox_postgres_json.keys())
    snowflake_manager = SnowflakeDatabaseManager(os.environ['snowflake_secret_name'])
    conn = snowflake_manager.get_snowflake_connection(database=os.getenv("SNOWFLAKE_METADATA_DATABASE_NAME"))
    for key in key_list:
        if key in connect_postgres_json.keys():
            finale_json = {}
            finale_json["table"] = key
            finale_json["postgres_count"] = connect_postgres_json[key]
            # finale_json["snowflake_count"] = snowflake_json["connect_postgres_public"][key]
            finale_json["snowflake_count"] = get_count_of_table_snowflake(conn=conn,
                                                                          schema_name='CONNECT_POSTGRES_PUBLIC',
                                                                          table_name=key)
            finale_json_list.append(finale_json)
        elif key in aidbox_postgres_json.keys():
            finale_json = {}
            finale_json["table"] = key
            finale_json["postgres_count"] = aidbox_postgres_json[key]
            # finale_json["snowflake_count"] = snowflake_json["int_stg_public"][key]
            finale_json["snowflake_count"] = get_count_of_table_snowflake(conn=conn,
                                                                          schema_name='INT_STG_PUBLIC',
                                                                          table_name=key)
            finale_json_list.append(finale_json)

    count_difference = compare_count(finale_json_list)

    Final_msg = f'''
    Table Comparison Data: {finale_json_list} 

    {count_difference}
    '''

    print(Final_msg)

    # Send SNS notification
    # SendNotification(sns_secret_name=sns_secret_name).send_sns_notification(subject="Table Replication Details",
    # message=Final_msg)

    # Return a response if needed
    return {
        "statusCode": 200,
        "body": "Notification Sent"
    }
