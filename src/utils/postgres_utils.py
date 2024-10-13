import psycopg2
import json
from src.utils.secret_manager_utils import SecretManagerUtils
import traceback
import sys


class PostgresDatabaseManager:
    def __init__(self, secret_name):
        self.postgres_credentials = json.loads(SecretManagerUtils().get_secret(secret_name))

    def get_postgres_connection(self, database):
        try:
            print("Connecting Postgres....")
            conn = psycopg2.connect(
                dbname=database,
                user=self.postgres_credentials.get('user'),
                password=self.postgres_credentials.get('password'),
                host=self.postgres_credentials.get('host'),
                connect_timeout=5,
            )
            print("PostgresDB connected successfully")
            cursor = conn.cursor()
            return conn, cursor

        except psycopg2.Error as e:
            print(f"Error connecting to PostgreSQL ({database}): {e}")
            return None


if __name__ == "__main__":
    postgres_manager = PostgresDatabaseManager('secret_name')
