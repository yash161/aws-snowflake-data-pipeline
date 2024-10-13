from tenacity import retry, stop_after_attempt
import snowflake.connector
import json  # Import the json module
from src.utils.secret_manager_utils import SecretManagerUtils
import traceback
import sys
import time


class SnowflakeDatabaseManager:
    def __init__(self, secret_name):
        self.secret_manager = json.loads(SecretManagerUtils().get_secret(secret_name))
    @retry(stop=stop_after_attempt(3))
    def get_snowflake_connection(self, database):
        try:
            print("Connecting Snowflake...")
            conn = snowflake.connector.connect(
                user=self.secret_manager.get('username'),
                password=self.secret_manager.get('password'),
                account=self.secret_manager.get('account'),
                role=self.secret_manager.get('role'),
                warehouse=self.secret_manager.get('warehouse'),
                database=database,
                login_timeout=5,
            )
            print("Snowflake connected successfully")
            return conn
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            print(f"Error [get_snowflake_connection]: {str(e)}")
            raise e

    def create_database(self, snowflake_database):
        conn = self.get_snowflake_connection(snowflake_database)
        if conn:
            try:
                # Create a cursor to execute SQL statements
                cursor = conn.cursor()

                # SQL statement to create the new database
                create_database_sql = f"CREATE OR REPLACE DATABASE {snowflake_database}"

                # Execute the SQL statement
                cursor.execute(create_database_sql)

                # Commit the transaction to make the database creation permanent
                conn.commit()

                print(f"Database '{snowflake_database}' created successfully")

            except snowflake.connector.errors.ProgrammingError as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_traceback)
                print(f"Error [SnowflakeDatabaseManager][create_database]: {str(e)}")


if __name__ == "__main__":
    secret_name = "prod/ch_snowflake_secrets"  # Replace with your AWS Secrets Manager secret name
    snowflake_database = 'beta_db'

    manager = SnowflakeDatabaseManager(secret_name)
    manager.get_snowflake_connection(snowflake_database)
