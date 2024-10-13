import datetime
import psycopg2
import json
import base64
from enum import Enum
import boto3
from botocore.exceptions import ClientError
import snowflake.connector
import traceback
import sys
import os
from src.utils.secret_manager_utils import SecretManagerUtils
from src.utils.snowflake_utils import SnowflakeDatabaseManager
from src.utils.postgres_utils import PostgresDatabaseManager
from src.utils.notification_utils import SendNotification

snowflake_database_manager = SnowflakeDatabaseManager(os.environ['snowflake_secret_name'])
connect_postgres_database_manager = PostgresDatabaseManager(os.environ['connect_postgres_secret_name'])
aidbox_postgres_database_manager = PostgresDatabaseManager(os.environ['aidbox_postgres_secret_name'])

'''
Lambda function is to fetch the list of tables to be sync by Glue Jobs
'''
extra_big_tables_names = ["hl7v2message","observation"]
big_tables_names=["condition","documentreference","medicationstatement","progressnote","subsnotification"]
skip_tables = ["_schema_version","schema_migrations"]

def get_metadata_details(database, schema, table):
    metadata_json_list = []
    conn = snowflake_database_manager.get_snowflake_connection(database=database)
    cursor = conn.cursor()
    cursor.execute(f"USE {database}.{schema};")
    print(f"SELECT * from {database}.{schema}.{table};")
    cursor.execute(f"SELECT * from {database}.{schema}.{table};")
    result = cursor.fetchall()
    print(result)
    if len(result) > 0:
        for data in result:
            if len(data) >= 7:
                temp_json = {}
                temp_json["src_type"] = data[0]
                if data[0] == 'connect_postgres' or data[0] == 'aidbox_postgres':
                    temp_json["src_db"] = data[1]
                    temp_json["src_schema"] = data[2]
                else:
                    temp_json["bucket_name"] = data[1]
                    temp_json["prefix"] = data[2]
                    temp_json["snowflake_table"] = data[5]
                    temp_json["primary_key"] = data[6]
                temp_json["snowflake_db"] = data[3]
                temp_json["snowflake_schema"] = data[4]
                print("Temp json", temp_json)
                metadata_json_list.append(temp_json)
    cursor.close()
    conn.close()
    return metadata_json_list


def get_postgres_table_details(postgres_database, postgres_schema, conn, cursor, specific_table_list):
    # Fetch tables and their primary keys as JSON
    print("specific_table_list:", specific_table_list)
    cursor.execute(f"""
    SELECT
    c.relname AS table_name,
    n.nspname AS schema_name,
    string_agg(a.attname, ',') AS primary_keys
    FROM
        pg_attribute a
    JOIN
        pg_class c ON a.attrelid = c.oid
    JOIN
        pg_namespace n ON c.relnamespace = n.oid
    JOIN
        pg_index i ON c.oid = i.indrelid
    WHERE
        n.nspname = '{postgres_schema}'
        AND c.relkind = 'r' -- Select only regular tables
        AND NOT c.relname LIKE 'pg_%' -- Exclude system tables
        AND NOT c.relname LIKE 'sql_%' -- Exclude system tables
        AND NOT c.relname LIKE 'information_schema%'
        AND i.indisprimary -- Select only primary key indexes
        AND a.attnum = ANY(i.indkey) -- Match the primary key columns
    GROUP BY
        c.relname,
        n.nspname;
    """)

    tables = cursor.fetchall()

    print("Query Result:", tables)

    # Convert the result to a list of JSON objects
    result_list = []
    if len(tables) > 0:
        for row in tables:
            if len(row) >= 3:
                temp_dict = {}
                temp_dict["table_catalog"] = postgres_database
                temp_dict["table_name"] = row[0]
                temp_dict["table_schema"] = row[1]
                temp_dict["primary_keys"] = row[2]
                if specific_table_list is not None:
                    if temp_dict.get("table_name") in specific_table_list:
                        result_list.append(temp_dict)
                        continue
                    continue
                result_list.append(temp_dict)

    # Print the list of JSON objects
    for item in result_list:
        print(item)

    # Close connections
    cursor.close()
    conn.close()
    return result_list


def lambda_handler(event, context):
    lambda_function_name = os.environ['AWS_LAMBDA_FUNCTION_NAME']
    print("Name of lambda is:::", lambda_function_name)
    env_terms = ["release", "dev", "prod"]
    env = next((term for term in env_terms if term in lambda_function_name), None)
    region = context.invoked_function_arn.split(':')[3]
    log_stream_name = context.log_stream_name.replace('$', '$2524').replace('/', '$252F').replace('[', '$255B').replace(
        ']', '$255D')
    log_group_name = context.log_group_name.replace('/', '$252F')
    cw_logs_url = 'https://' + region + '.console.aws.amazon.com/cloudwatch/home?region=' + region + '#logsV2:log-groups/log-group/' + log_group_name + '/log-events/' + log_stream_name
    print("the current environment is ::", env)
    print("Starting Process")
    sns_secret_name = os.getenv("sns_secret_name")
    print("Starting Lambda")
    event_json = json.dumps(event)
    event_dict = json.loads(event_json)

    # Check if the "tables" key is present in the event
    if "tables" in event_dict and event_dict["tables"] is not None:
        # Fetch the value associated with the "tables" key and convert it to a list
        table_list = event_dict["tables"] if len(event_dict["tables"]) > 0 else None
    else:
        table_list = None

    if "snowflake_database_name" in event_dict.keys() and "snowflake_schema_name" in event_dict.keys() and "snowflake_table_name" in event_dict.keys():
        snowflake_database_name = event_dict["snowflake_database_name"]
        snowflake_schema_name = event_dict['snowflake_schema_name']
        snowflake_table_name = event_dict['snowflake_table_name']
    else:

        snowflake_database_name, snowflake_schema_name, snowflake_table_name = os.getenv("SNOWFLAKE_METADATA_DATABASE_NAME"),os.getenv("SNOWFLAKE_METADATA_SCHEMA_NAME"), os.getenv("SNOWFLAKE_METADATA_TABLE_NAME")# Hardcoded For Testing, We can give this parameters in event also

    try:
        print("Getting Metadata")
        metadata_details_json_list = get_metadata_details(database=snowflake_database_name,
                                                          schema=snowflake_schema_name, table=snowflake_table_name)
        updated_metadata_details_json_list = []

        for json_metadata in metadata_details_json_list:
            if json_metadata.get("src_type") == "s3":
                updated_metadata_details_json_list.append(json_metadata)
                continue
            elif json_metadata.get("src_type") == "connect_postgres":
                conn, cursor = connect_postgres_database_manager.get_postgres_connection(
                    database=json_metadata.get("src_db"))
            elif json_metadata.get("src_type") == "aidbox_postgres":
                conn, cursor = aidbox_postgres_database_manager.get_postgres_connection(
                    database=json_metadata.get("src_db"))

            table_details = get_postgres_table_details(postgres_database=json_metadata.get("src_db"),
                                                       postgres_schema=json_metadata.get("src_schema"), conn=conn,
                                                       cursor=cursor, specific_table_list=table_list)
            for details in table_details:
                if details.get("table_name") in skip_tables:
                    continue
                new_json_metadata = {key: value for key, value in json_metadata.items()}
                new_json_metadata["src_table"] = details.get("table_name")
                new_json_metadata["snowflake_table"] = details.get("table_name")
                new_json_metadata["primary_key"] = details.get("primary_keys") if details.get(
                    "primary_keys") != '' and details.get("primary_keys") is not None else 'None'
                if details.get("table_name") in extra_big_tables_names:
                    new_json_metadata["worker_type"] = "G.2X"
                elif details.get("table_name") in big_tables_names:
                    new_json_metadata["worker_type"] = "G.1X"
                else:
                    new_json_metadata["worker_type"] = "G.025X"

                print("new json: ", new_json_metadata)
                updated_metadata_details_json_list.append(new_json_metadata)
        print("updated_metadata_details_json_list:", updated_metadata_details_json_list)
        databases = set(x for x in (y for y in (data.get("src_db") for data in updated_metadata_details_json_list if
                                                data.get("src_db") is not None)))
        s3_files = set(x.split('/')[-1] for x in (y for y in
                                                  (data.get("prefix") for data in updated_metadata_details_json_list
                                                   if
                                                   data.get("prefix") is not None)))

        # You can return the 'databases' list as a response
        return {
            "statusCode": 200,
            "body": updated_metadata_details_json_list
        }

    except Exception as e:

        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(f"Error [lambda_handler]: {str(e)}")
        subject = f"Status:[Failed] Env:[{env}]  Lambda function:[{lambda_function_name}]"
        sns_dict = {'Execution_time': str(datetime.datetime.now()),
                    'cloudwatch_log_group_link':cw_logs_url,
                    'Reason of failure': str(e)}
        SendNotification(sns_secret_name=sns_secret_name).send_sns_notification(subject=subject, message=sns_dict)
        print("Notification Sent")
        return {
            "statusCode": 500,
            "body": "Internal Server Error"
        }


if __name__ == "__main__":
    event = {
        # "tables":['admins']
    }
    print(lambda_handler(event, None))
