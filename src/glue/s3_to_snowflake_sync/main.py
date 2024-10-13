from datetime import datetime
import os
import sys
import boto3
import traceback
import platform
import pandas as pd
from src.utils.snowflake_utils import SnowflakeDatabaseManager
from src.utils.notification_utils import SendNotification

try:
    from awsglue.utils import getResolvedOptions
except Exception as e:
    print(f"Warning [importing awsglue.utils]: {str(e)}", " Acceptable while running locally")

def check_platform():
    try:
        # Get the system's platform
        system_platform = platform.system()
        print(f"The running machine is {system_platform}.")
        return system_platform
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(f"Error [check_platform]: {str(e)}")
        raise e
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

def get_files_from_s3(bucket_name, prefix):
    try:
        # Create an S3 client
        s3_client = boto3.client('s3')

        # List all objects in a bucket using the specified prefix
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        print(response.get('Contents'))
        return s3_client, response.get('Contents')
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(f"Error [get_files_from_s3]: {str(e)}")
        raise e

def move_file_to_archive(bucket_name,key,destination_path):
    try:
        s3_client = boto3.client('s3')
        # Perform the S3 object copy
        s3_client.copy_object(CopySource={'Bucket': bucket_name, 'Key': key}, Bucket=bucket_name, Key=destination_path)

        # Delete the original file from the source folder
        s3_client.delete_object(Bucket=bucket_name, Key=key)

        print("File moved to archive")
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(f"Error [move_file_to_archive]: {str(e)}")
        raise e


def delete_uploaded_files(file_name):
    if os.path.exists(file_name):
        os.remove(file_name)
        return f"File '{file_name}' removed after upload."
    else:
        return f"File '{file_name}' does not exist or was not uploaded successfully."

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
        print(delete_uploaded_files(file_name=file_name))
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(f"Error [delete_files_and_stages]: {str(e)}")
        raise e


def get_table_details_for_file(cursor,snowflake_databse,snowflake_schema,src_container,src_location):
    try:
        cursor.execute(f'''SELECT * FROM {snowflake_databse}.{snowflake_schema}.ETL_METADATA WHERE SRC_CONTAINER='{src_container}' AND SRC_LOCATION='{src_location}';''')
        result = cursor.fetchall()
        if len(result)>0:
            if len(result[0])>=7:
                table_details = result[0]
                dest_database = table_details[3]
                dest_schema = table_details[4]
                dest_table = table_details[5]
                primary_key = table_details[6].split(",")
                return dest_database,dest_schema,dest_table,primary_key
            print(result[0])
        else:
            return None,None,None,None
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(f"Error [get_table_details_for_file]: {str(e)}")
        raise e



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

def get_merged_query(database, schema, table, stage, file_name, file_format_name, dataframe,primary_key):
    try:
        columns = dataframe.columns
        col_list = []
        src_col_list = []
        update_list = []
        primary_keys_condition = []
        index = 1

        for col in columns:
            col_list.append(f"${index} {col}")
            src_col_list.append(f"source.{col}")
            update_list.append(f"target.{col} = source.{col}")
            index = index + 1

        if primary_key is not None and len(primary_key) > 0:

            for key in primary_key:
                primary_keys_condition.append(f"target.{key} = source.{key}")

            merge_query = f'''MERGE INTO {database}.{schema}.{table} AS target
            USING (SELECT {",".join(col_list)} from @{database}.{schema}.{stage}/{file_name}.gz(FILE_FORMAT => {file_format_name}  )) AS source
            ON {" and ".join(primary_keys_condition)}
            WHEN MATCHED THEN
            UPDATE SET {",".join(update_list)}
            WHEN NOT MATCHED THEN
            INSERT ({",".join(columns)}) VALUES ({",".join(src_col_list)});'''

            return merge_query
        else:
            print("Inserting Data With out primary key")
            merge_query = f'''COPY INTO {database}.{schema}.{table} FROM (SELECT {",".join(col_list)} from @{database}.{schema}.{stage}/{file_name}.gz(FILE_FORMAT => csv_format ));'''
            return merge_query
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(f"Error [get_merged_query]: {str(e)}")
        raise e

def load_files(snowflake_database_manager,bucket_name,prefix,snowflake_database, snowflake_schema):
    try:
        conn = snowflake_database_manager.get_snowflake_connection(database=snowflake_database)
        cursor = conn.cursor()

        s3_client , s3_file_response = get_files_from_s3(bucket_name=bucket_name, prefix=prefix)
        # Download and upload each file to Snowflake stage
        for obj in s3_file_response:

            key = obj['Key']
            print("Key:",key)
            s3_file_name = key.split('/')[-1]
            print("Filename:", s3_file_name)
            if s3_file_name is None or s3_file_name == '':
                continue
            if check_platform() == 'Linux':
                file_name = f"/tmp/{s3_file_name}"  # For glue
            else:
                file_name = s3_file_name  # For Local

            dest_database, dest_schema, dest_table, primary_key = get_table_details_for_file(cursor=cursor,
                                                                                             snowflake_databse=snowflake_database,
                                                                                             snowflake_schema=snowflake_schema,
                                                                                             src_container=bucket_name,
                                                                                             src_location=key)
            stage_file_name = s3_file_name
            file_format_name = f"{dest_database}_{dest_schema}_{dest_table}_file_format_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}"
            stage_name = f"{dest_database}_{dest_schema}_{dest_table}_stage_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}"

            if dest_database is None or dest_schema is None or dest_table is None or primary_key is None:
                print("Table has not proper destination database details")
                continue
            try:
                # Download file from S3
                s3_client.download_file(bucket_name, key, file_name)
                file_dataframe = pd.read_csv(file_name)
                # Get table name and primary key for this file
                # Upload file to Snowflake stage
                cursor.execute(f'USE {dest_database}.{dest_schema}')
                print("Creating File Format")
                cursor.execute(f"CREATE OR REPLACE FILE FORMAT {file_format_name} TYPE = 'CSV' skip_header = 1 ;")
                print("File Format Created")
                print("Creating Stage")
                cursor.execute(f"CREATE OR REPLACE STAGE {stage_name};")
                print("Stage Created")
                merged_query = get_merged_query(database=dest_database,
                                                schema=dest_schema,
                                                table=dest_table,
                                                stage=stage_name,
                                                file_name=stage_file_name,
                                                file_format_name=file_format_name,
                                                dataframe=file_dataframe,
                                                primary_key=primary_key)

                if check_platform() == "Linux":
                    file_upload_command = f"PUT file:///{file_name} @{stage_name}"  # For glue
                    print("Linux command", file_upload_command)
                else:
                    file_upload_command = f"PUT file:///{get_full_file_path_of_file(file_name=file_name)} @{stage_name}"  # For Local
                    print('Window command', file_upload_command)


                print("Uploading File to Stage")
                cursor.execute(file_upload_command)
                print("File uploaded")
                print("Loading data..")
                print("Query:",merged_query)
                cursor.execute(merged_query)
                result = cursor.fetchall()
                # for data in result:
                #     print(data)
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

                delete_files_and_stages(snowflake_database_manager=snowflake_database_manager, database=dest_database, schema=dest_schema,
                                        stage_name=stage_name,
                                        stage_file_name=stage_file_name, file_format_name=file_format_name, file_name=file_name)

                print("Inserted :",inserted_data," Updated :",updated_data)

                move_file_to_archive(bucket_name=bucket_name,key=key,destination_path=f'archive/{s3_file_name}')

            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_traceback)
                print(f"Error [upsert_data_into_snowflake]: {str(e)}")
                delete_files_and_stages(snowflake_database_manager=snowflake_database_manager, database=dest_database,
                                        schema=dest_schema,
                                        stage_name=stage_name,
                                        stage_file_name=stage_file_name, file_format_name=file_format_name,
                                        file_name=file_name)
                raise e

            # Close Snowflake connection
            cursor.close()
            conn.close()
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(f"Error [load_files]: {str(e)}")
        raise e


def start_process(src_type,bucket_name,prefix,snowflake_db,snowflake_schema,snowflake_secret_name,sns_secret_name):
    try:
        if src_type == "s3":
            snowflake_database_manager = SnowflakeDatabaseManager(snowflake_secret_name)
            load_files(snowflake_database_manager=snowflake_database_manager,bucket_name=bucket_name,
                       prefix=prefix,snowflake_database=snowflake_db,snowflake_schema=snowflake_schema)
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(f"Error [start_process]: {str(e)}")
        sns_dict = {"status": "Fail",
                    "src_type": src_type,
                    "bucket_name": bucket_name,
                    "prefix": prefix,
                    "snowflake_db": snowflake_db,
                    "snowflake_schema": snowflake_schema,
                    "Error": str(e)}
        subject = f"Glue-Job [Status:{sns_dict.get('status')}] [Bucket Name:{sns_dict.get('bucket_name')}] [Prefix:{sns_dict.get('prefix')}]"
        SendNotification(sns_secret_name=sns_secret_name).send_sns_notification(subject=subject,message=sns_dict)
        print("Notification Sent")
        # raise e


if __name__ == "__main__":
    if check_platform() == "Linux":
        args = getResolvedOptions(sys.argv, ['snowflake_secret_name','bucket_name','prefix','snowflake_db', 'snowflake_schema','sns_secret_name'])
    else:
        args = {"src_type":"s3",
                "bucket_name":"predict-datalake",
                "prefix":"raw/ga/",
                "snowflake_db":"test_db",
                "snowflake_schema":"public",
                "snowflake_secret_name": "dev/snowflake_secrets"}

    src_type = args["src_type"]
    snowflake_secret_name = args["snowflake_secret_name"]
    bucket_name = args["bucket_name"]
    prefix = args["prefix"]
    snowflake_db = args["snowflake_db"]
    snowflake_schema = args["snowflake_schema"]
    sns_secret_name = args["sns_secret_name"]
    start_process(src_type = src_type,
                  bucket_name=bucket_name,
                  prefix=prefix,
                  snowflake_db=snowflake_db,
                  snowflake_schema=snowflake_schema,
                  snowflake_secret_name=snowflake_secret_name,
                  sns_secret_name=sns_secret_name)
