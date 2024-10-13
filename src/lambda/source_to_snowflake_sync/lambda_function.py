from datetime import datetime, date
import os
import pandas as pd
import numpy as np
from src.utils.snowflake_utils import SnowflakeDatabaseManager
from src.utils.postgres_utils import PostgresDatabaseManager
from src.utils.notification_utils import SendNotification
import traceback
import sys
import platform
import json
from datetime import timedelta



# Getting all unloaded data from the PostgreSQL table
def get_data_from_postgres(postgres_database_manager, database, schema, table, full_load, incremental_column,
                           updated_at):
    conn, cursor = postgres_database_manager.get_postgres_connection(database=database)
    try:
        if full_load :
            query = f"SELECT *, current_timestamp as _FIVETRAN_SYNCED, FALSE as _FIVETRAN_DELETED FROM \"{database}\".\"{schema}\".\"{table}\" ;"
        else:
            # Example: Execute a SQL query
            query = f"SELECT *, current_timestamp as _FIVETRAN_SYNCED, FALSE as _FIVETRAN_DELETED FROM \"{database}\".\"{schema}\".\"{table}\" where \"{incremental_column}\" >= '{updated_at}' ;"

        print(query)
        df = pd.read_sql_query(query, conn)

        # Fetch max and min values from the updated_at column
        print("Data loaded into DataFrame:")
        print(df)

        print("Removing NaT and NaN")
        df.replace({pd.NaT: None, np.nan: None}, inplace=True)
        print("Removed NaT and NaN")

        conn.close()
        return df

    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(f"Error [get_data_from_postgres]: {str(e)}")

        if conn is not None:
            conn.close()
            print("PostgreSQL connection closed")
        raise e


# Retrieve the maximum value of the 'updated_at' column, if present in the table
def get_max_updated_at_from_snowflake(snowflake_database_manager, database, schema, table):
    try:
        conn = snowflake_database_manager.get_snowflake_connection(database=database)
        # snowflake_database_manager = SnowflakeDatabaseManager()
        colunmn_list = []
        # Execute a SQL query
        cursor = conn.cursor()
        cursor.execute(f"USE {database}.{schema};")
        cursor.execute(
            f'''SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_CATALOG = '{database.upper()}' 
            AND TABLE_SCHEMA = '{schema.upper()}' 
            AND TABLE_NAME = '{table.upper()}';''')
        result = cursor.fetchall()
        for column_data in result:
            for column in column_data:
                colunmn_list.append(column)
        if 'updated_at' in colunmn_list or 'UPDATED_AT' in colunmn_list:
            print("Incremental Load is configured.")
            full_load = False
            incremental_column = 'updated_at'
        elif 'ts' in colunmn_list or 'TS' in colunmn_list:
            print("Incremental Load is configured.")
            full_load = False
            incremental_column = 'ts'
        else:
            print("Full Load is configured.")
            full_load = True

        if full_load:
            return full_load, None, None
        else:
            reserved_keywords = ['account', 'Account', 'ACCOUNT', 'current', 'Current', 'CURRENT', 'grant',
                                 'Grant', 'GRANT', 'group', 'Group', 'GROUP',
                                 'increment', 'Increment', 'INCREMENT', 'issue', 'Issue', 'ISSUE',
                                 'natural', 'Natural', 'NATURAL', 'order', 'Order', 'ORDER',
                                 'organization', 'Organization', 'ORGANIZATION', 'sample', 'Sample', 'SAMPLE',
                                 'value', 'Value', 'VALUE']  # We can add more keywords later
            if database in reserved_keywords:
                database = f"\"{database.upper()}\""
            if schema in reserved_keywords:
                schema = f"\"{schema.upper()}\""
            if table in reserved_keywords:
                table = f"\"{table.upper()}\""
            cursor.execute(f"SELECT max(TO_TIMESTAMP({incremental_column})) FROM {database}.{schema}.{table} ;")
            results = cursor.fetchone()
            if results is not None and len(results) > 0:
                if results[0] is not None:
                    max_date = results[0]
                    print("Max Date in Snowflake is: ", results[0])
                    cursor.close()
                    conn.close()
                    return full_load, incremental_column, max_date
                else:
                    # Close the cursor and the connection
                    cursor.close()
                    conn.close()
                    return full_load, incremental_column, datetime.strptime('1970-01-01 00:00:00.000',
                                                                            '%Y-%m-%d %H:%M:%S.%f')
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(f"Error [get_max_updated_at_from_snowflake]: {str(e)}")
        raise e


# Retrieve the primary key of the PostgreSQL table
def get_primary_keys(postgres_database_manager, database, table):
    print("Fetching Primary Keys...")
    primary_key_list = []
    conn, cursor = postgres_database_manager.get_postgres_connection(database=database)
    # Execute a SQL query
    cursor.execute(f'''SELECT c.column_name, c.data_type
    FROM information_schema.table_constraints tc 
    JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name) 
    JOIN information_schema.columns AS c ON c.table_schema = tc.constraint_schema
      AND tc.table_name = c.table_name AND ccu.column_name = c.column_name
    WHERE constraint_type = 'PRIMARY KEY' and tc.table_name = '{table}'; ''')
    result = cursor.fetchall()
    if len(result) > 0:
        for data in result:
            primary_key_list.append(data[0])
    cursor.close()
    conn.close()
    # print(primary_key_list)
    return primary_key_list


# Delete the stage, file format, and generated CSV files upon successful data load or job failure
def delete_files_and_stages(snowflake_database_manager, database, schema, stage_name, stage_file_name, file_format_name,
                            file_name):
    try:
        # snowflake_database_manager = SnowflakeDatabaseManager()
        conn = snowflake_database_manager.get_snowflake_connection(database=database)
        cursor = conn.cursor()
        cursor.execute(f'USE {database}.{schema}')

        print("Deleting File from Stage..")
        cursor.execute(f"REMOVE @{stage_name}/{stage_file_name}.gz")
        print("File Deleted")
        print("Deleting Stage...")
        cursor.execute(f"DROP STAGE {stage_name};")
        print("Stage Deleted from snowflake.")
        print("Deleting File Format...")
        cursor.execute(f"DROP FILE FORMAT IF EXISTS {file_format_name};")
        print("File Format Deleted from Snowflake stage.")
        print("Deleting File from glue storage.")
        print(delete_uploaded_files(file_name))
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(f"Error [delete_files_and_stages]: {str(e)}")
        raise e


# Retrieve the full local path of the given file name from the working directory
def get_full_file_path_of_file(file_name):
    try:
        # Set the search_directory to None or an empty string to search in the current directory
        # search_directory = "D:\\"
        search_directory = os.getcwd()
        print("search_directory :", search_directory)

        # Find the file by searching
        full_path = search_file(file_name, search_directory)

        if full_path is not None:
            print(f"The full path of '{file_name}' is: {full_path}")
            return full_path
        else:
            print(f"'{file_name}' not found in the current directory.")
            return file_name
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(f"Error [get_full_file_path_of_file]: {str(e)}")
        raise e


# Check whether the platform is local Windows or AWS
def check_platform():
    # Get the system's platform
    system_platform = platform.system()
    print(f"The running machine is {system_platform}.")
    return system_platform


# Search for files from the given directory
def search_file(filename, search_dir):
    try:
        for root, dirs, files in os.walk(search_dir):
            if filename in files:
                return os.path.join(root, filename)
        return None
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(f"Error [search_file]: {str(e)}")
        raise e


# Delete the temporary local file
def delete_uploaded_files(file_name):
    if os.path.exists(file_name):
        os.remove(file_name)
        return f"File '{file_name}' removed after upload."
    else:
        return f"File '{file_name}' does not exist or was not uploaded successfully."


# Generate a Merge Query or Full Load Query based on the table's columns and primary keys for loading data into Snowflake
def get_merged_query(postgres_database_manager, database, schema, table, stage, file_name, file_format_name, dataframe,
                     src_db, src_table,
                     primary_key):
    try:

        reserved_keywords = ['account', 'Account', 'ACCOUNT', 'current', 'Current', 'CURRENT', 'grant',
                             'Grant', 'GRANT', 'group', 'Group', 'GROUP',
                             'increment', 'Increment', 'INCREMENT', 'issue', 'Issue', 'ISSUE',
                             'natural', 'Natural', 'NATURAL', 'order', 'Order', 'ORDER',
                             'organization', 'Organization', 'ORGANIZATION', 'sample', 'Sample', 'SAMPLE',
                             'value', 'Value', 'VALUE']  # We can add more keywords later
        temp_columns = dataframe.columns
        columns = []
        if database in reserved_keywords:
            database = f"\"{database.upper()}\""
        if schema in reserved_keywords:
            schema = f"\"{schema.upper()}\""
        if table in reserved_keywords:
            table = f"\"{table.upper()}\""
        for col in temp_columns:
            # if col == 'current' or col == 'Current' or col == 'CURRENT':
            if col in reserved_keywords:
                col = f"\"{col.upper()}\""
            columns.append(col)

        col_list = []
        src_col_list = []
        update_list = []
        primary_keys_condition = []
        index = 1
        if primary_key is None or len(primary_key) == 0:
            primary_keys = get_primary_keys(postgres_database_manager=postgres_database_manager, database=src_db,
                                            table=src_table)
        else:
            primary_keys = primary_key

        for col in columns:
            # col_list.append(f"${index} {col}")
            col_list.append(f"$1:{col} as {col}")
            src_col_list.append(f"source.{col}")
            update_list.append(f"target.{col} = source.{col}")
            index = index + 1

        if primary_keys is not None and len(primary_keys) > 0:

            for key in primary_keys:
                if key in reserved_keywords:
                    key = f"\"{key.upper()}\""
                primary_keys_condition.append(f"target.{key} = source.{key}")

            merge_query = f'''MERGE INTO {database}.{schema}.{table} AS target
            USING (SELECT {",".join(col_list)} from @{database}.{schema}.{stage}/{file_name} (FILE_FORMAT => {file_format_name}  )) AS source
            ON {" and ".join(primary_keys_condition)}
            WHEN MATCHED THEN
            UPDATE SET {",".join(update_list)}
            WHEN NOT MATCHED THEN
            INSERT ({",".join(columns)}) VALUES ({",".join(src_col_list)});'''

            return merge_query
        else:
            print("Inserting Data With out primary key")
            merge_query = f'''COPY INTO {database}.{schema}.{table} FROM (SELECT {",".join(col_list)} from @{database}.{schema}.{stage}/{file_name} (FILE_FORMAT => {file_format_name} ));'''
            return merge_query
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(f"Error [get_merged_query]: {str(e)}")
        raise e


# Upsert all unloaded data into Snowflake and retrieve the details of loaded data
def upsert_data_into_snowflake(postgres_database_manager, snowflake_database_manager, database, schema, table,
                               dataframe, src_db, src_table, primary_key):
    file_format_name = f"{database}_{schema}_{table}_json_format_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}"
    stage_name = f"{database}_{schema}_{table}_stage_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}"

    # Check the running platform and provide the filename accordingly
    if check_platform() == 'Linux':
        file_name = f"/tmp/{database}_{schema}_{table}_data_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.json"  # For glue
    else:
        file_name = f"{database}_{schema}_{table}_data_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.json"  # For Local

    stage_file_name = f"{database}_{schema}_{table}_data_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.json"

    try:
        total_data_count = len(dataframe)
        # dataframe.to_csv(file_name, index=False)
        # dataframe.to_parquet(file_name, engine='fastparquet')
        # dataframe.to_json(file_name, orient='records', lines=True, date_format='iso', date_unit='ns')
        print("Converting Dataframe into Dict")
        dict_data = dataframe.to_dict(orient='records')
        print("Converted Dataframe into Dict")
        print("Converting Dict into JSON")
        with open(file_name, 'w') as json_file:
            json.dump(dict_data, json_file, default=str)
        print("Converted Dict into JSON")
        merge_query = get_merged_query(postgres_database_manager=postgres_database_manager, dataframe=dataframe,
                                       database=database, schema=schema, table=table,
                                       stage=stage_name,
                                       file_name=stage_file_name, src_db=src_db, file_format_name=file_format_name,
                                       src_table=src_table, primary_key=primary_key)
        print("Merge Query :", merge_query)

        conn = snowflake_database_manager.get_snowflake_connection(database=database)
        cursor = conn.cursor()

        # Create a temporary stage, file format, and upload the CSV file to the stage
        cursor.execute(f'USE {database}.{schema}')
        print("Creating File Format")
        # cursor.execute(f"CREATE OR REPLACE FILE FORMAT {file_format_name} TYPE = 'CSV' SKIP_HEADER = 1 ;")
        # cursor.execute(f"CREATE OR REPLACE FILE FORMAT {file_format_name} TYPE = 'PARQUET' ;")
        cursor.execute(f"CREATE OR REPLACE FILE FORMAT {file_format_name} TYPE = 'JSON' STRIP_OUTER_ARRAY = TRUE ;")
        print("File Format Created")
        print("Creating Stage")
        cursor.execute(f"CREATE OR REPLACE STAGE {stage_name};")
        print("Stage Created")
        print("Uploading File to Stage")
        if check_platform() == "Linux":
            file_upload_command = f"PUT file:///{file_name} @{stage_name}"  # For glue
            print("Linux command", file_upload_command)
        else:
            file_upload_command = f"PUT file:///{get_full_file_path_of_file(file_name=file_name)} @{stage_name}"  # For Local
            print('Window command', file_upload_command)

        # Upload the file to Snowflake stage
        cursor.execute(file_upload_command)

        print("File Uploaded")
        print("Merge Query:", merge_query)
        print("Merging or Loading Data")

        # Upsert data into Snowflake table
        cursor.execute(merge_query)
        result = cursor.fetchall()
        print('insert query result ', result)
        if len(result) == 1:
            if len(result[0]) == 2:
                inserted_data = result[0][0]
                updated_data = result[0][1]
            elif len(result[0]) > 2:
                inserted_data = result[0][3]
                updated_data = 0
            else:
                inserted_data = None
                updated_data = None
        else:
            inserted_data = None
            updated_data = None

        # Delete stage, file-format, and temporary local file
        delete_files_and_stages(snowflake_database_manager=snowflake_database_manager, database=database, schema=schema,
                                stage_name=stage_name,
                                stage_file_name=stage_file_name, file_format_name=file_format_name, file_name=file_name)
        return total_data_count, inserted_data, updated_data
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(f"Error [upsert_data_into_snowflake]: {str(e)}")
        delete_files_and_stages(snowflake_database_manager=snowflake_database_manager, database=database, schema=schema,
                                stage_name=stage_name,
                                stage_file_name=stage_file_name, file_format_name=file_format_name, file_name=file_name)
        raise e


def start_process(src_type, src_db, src_schema, src_table, primary_key, snowflake_db, snowflake_schema,
                  snowflake_table, snowflake_secret_name, connect_postgres_secret_name,
                  aidbox_postgres_secret_name, sns_secret_name):
    print("Starting Process")

    try:
        snowflake_database_manager = SnowflakeDatabaseManager(snowflake_secret_name)
        print('src_type: ', src_type)
        if src_type == "connect_postgres":
            database_manager = PostgresDatabaseManager(connect_postgres_secret_name)
        elif src_type == "aidbox_postgres":
            database_manager = PostgresDatabaseManager(aidbox_postgres_secret_name)
        else:
            database_manager = None

        if database_manager is not None:
            # Retrieve the maximum 'updated_at' if available in the table; otherwise, return True as 'full_load'
            full_load, incremental_column, max_updated_at = get_max_updated_at_from_snowflake(
                snowflake_database_manager=snowflake_database_manager,
                database=snowflake_db,
                schema=snowflake_schema,
                table=snowflake_table)

            # Retrieve all unloaded data from the PostgreSQL table as a DataFrame
            postgres_dataframe = get_data_from_postgres(postgres_database_manager=database_manager,
                                                        database=src_db,
                                                        schema=src_schema,
                                                        table=src_table,
                                                        full_load=full_load,
                                                        incremental_column=incremental_column,
                                                        updated_at=max_updated_at)

            if len(postgres_dataframe) > 0:

                # Upsert all unloaded data into Snowflake and obtain details of the loaded data
                total_data_count, inserted_data, updated_data = upsert_data_into_snowflake(
                    postgres_database_manager=database_manager,
                    snowflake_database_manager=snowflake_database_manager,
                    database=snowflake_db,
                    schema=snowflake_schema,
                    table=snowflake_table,
                    dataframe=postgres_dataframe,
                    src_db=src_db,
                    src_table=src_table,
                    primary_key=primary_key)

                print('Total Count: ', total_data_count, ' inserted: ', inserted_data, ' updated: ', updated_data)
            else:
                print("Dataframe is empty. Skipping Upserting Data. ")

    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print("Error in starting Process: ", e)

        # Create a dictionary for sending a notification of the job status
        sns_dict = {"status": "Fail",
                    "src_type": src_type,
                    "src_db": src_db,
                    "src_schema": src_schema,
                    "src_table": src_table,
                    "snowflake_db": snowflake_db,
                    "snowflake_schema": snowflake_schema,
                    "snowflake_table": snowflake_table,
                    "Error": str(e)}

        subject = f"Glue-Job [Status:{sns_dict.get('status')}] [src_db:{sns_dict.get('src_db')}] [src_schema:{sns_dict.get('src_schema')}] [src_table:{sns_dict.get('src_table')}]"
        print("SNS_DICT:", sns_dict)

        # Send notification of the failed job status
        SendNotification(sns_secret_name=sns_secret_name).send_sns_notification(subject=subject, message=sns_dict)
        print("Notification Sent")
        raise e

def lambda_handler(event, context):
    print(f"Getting Event from lambda ::::{event}")
    src_schema = event.get('src_schema')
    snowflake_db = event.get('snowflake_db')
    snowflake_schema = event.get('snowflake_schema')
    snowflake_table = event.get('snowflake_table')
    src_table = event.get('src_table')
    src_type = event.get('src_type')
    src_db = event.get('src_db')
    primary_key = event.get('primary_key')
    snowflake_secret_name = os.environ['snowflake_secret_name']
    connect_postgres_secret_name = os.environ['connect_postgres_secret_name']
    aidbox_postgres_secret_name = os.environ['aidbox_postgres_secret_name']
    sns_secret_name = os.environ['sns_secret_name']
    # snowflake_secret_name = "dev/snowflake_secrets"
    # connect_postgres_secret_name = "dev/connect_postgres_secret"
    # aidbox_postgres_secret_name = "dev/aidbox_postgres_secret"
    # sns_secret_name = "prod/snowflake_replication_sns_arn"
    start_process(src_type=src_type,
                  src_db=src_db,
                  src_schema=src_schema,
                  src_table=src_table,
                  primary_key=primary_key.split(",") if len(
                      primary_key.strip()) > 0 and primary_key != 'None' else None,
                  snowflake_db=snowflake_db,
                  snowflake_schema=snowflake_schema,
                  snowflake_table=snowflake_table,
                  snowflake_secret_name=snowflake_secret_name,
                  connect_postgres_secret_name=connect_postgres_secret_name,
                  aidbox_postgres_secret_name=aidbox_postgres_secret_name,
                  sns_secret_name=sns_secret_name)

    # For testing aidbox postgres
        # args = {'src_type': "aidbox_postgres",
        #         'src_db': "curve",
        #         'src_schema': "public",
        #         'src_table': "client",
        #         'snowflake_db': "dev_db",
        #         'snowflake_schema': "int_stg_public",
        #         'snowflake_table': "client",
        #         'primary_key': "id",
        #         "connect_postgres_secret_name": "dev/connect_postgres_secret",
        #         "aidbox_postgres_secret_name": "dev/aidbox_postgres_secret",
#         #         "snowflake_secret_name": "dev/ch_snowflake_secrets"}
# event = {'src_type': "connect_postgres",
#         'src_db': "chpostgres",
#         'src_schema': "public",
#         'src_table': "family_histories",
#         'snowflake_db': "test_db",
#         'snowflake_schema': "test",
#         'snowflake_table': "family_histories",
#         'primary_key': "",
#         "connect_postgres_secret_name": "dev/connect_postgres_secret",
#         "aidbox_postgres_secret_name": "dev/aidbox_postgres_secret",
#         "snowflake_secret_name": "dev/snowflake_secrets",
#         "sns_secret_name":"prod/snowflake_replication_sns_arn"
#         }
# lambda_handler(event=event,context=None)