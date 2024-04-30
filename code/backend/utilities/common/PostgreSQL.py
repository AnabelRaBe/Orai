import logging
import datetime
import os
import psycopg
import json
from typing import List, Dict, Tuple
from dotenv import load_dotenv

load_dotenv()

class PostgreSQL:
    """
    A class representing a PostgreSQL database connection.

    Attributes:
        connection (psycopg2.extensions.connection): The connection object to the PostgreSQL database.

    Methods:
        __init__(): Initializes the PostgreSQL connection.
        connect(): Connects to the PostgreSQL database using the provided connection string.
        create_table(table_name, columns): Create a new table in the PostgreSQL database.
        insert_data(table_name, data, columns): Inserts data into a table in the PostgreSQL database.
        select_data(table_name, condition, columns=None): Selects data from a table in the PostgreSQL database.
        update_data(table_name, new_values, condition): Update data in a table in the PostgreSQL database.
        delete_data(table_name, condition): Delete data from a table in the PostgreSQL database.
        upsert_rows(user_id, session_id, target_table, source_table, columns_target, columns_source, created_at): Upsert data from source table to target table in the PostgreSQL database.
        close_connection(): Close the PostgreSQL connection.
    """

    def __init__(self):
        """
        Initializes the PostgreSQL connection.
        """
        self.connection = self.connect()

    def connect(self):
        """
        Connects to the PostgreSQL database using the provided connection string.

        Returns:
            connection (psycopg2.extensions.connection): The connection object to the PostgreSQL database.
        """
        # # Get PostgreSQL connection details from environment variables
        # host = os.getenv("POSTGRESQL_HOST")
        # port = os.getenv("POSTGRESQL_PORT")
        # database = os.getenv("POSTGRESQL_DATABASE")
        # user = os.getenv("POSTGRESQL_USER")
        # password = os.getenv("POSTGRESQL_PASSWORD")

        # # Create a connection to the PostgreSQL database
        # connection = psycopg.connect(
        #     host=host,
        #     port=port,
        #     database=database,
        #     user=user,
        #     password=password
        # )
        
        connection = psycopg.connect(os.getenv("CONNECTION_STRING"))
        return connection
    
    def create_table(self, table_name: str, columns: str) -> None:
        """
        Create a new table in the PostgreSQL database.

        Args:
            table_name (str): The name of the table to be created.
            columns (str): The columns and their data types for the table.

        Returns:
            None
        """
        with self.connection.cursor() as cursor:
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
            cursor.execute(query)
        self.connection.commit()

    def insert_data(self, table_name: str, data: str, columns: str) -> None:
        """
        Inserts data into a table in the PostgreSQL database.

        Args:
            table_name (str): The name of the table to insert data into.
            data (str): The data to be inserted, in the form of a string.
            columns (str): The columns to insert the data into, in the form of a string.

        Returns:
            None
        """
        with self.connection.cursor() as cursor:
            query = f"INSERT INTO {table_name} {columns} VALUES ({data})"
            cursor.execute(query)
        self.connection.commit()

    def select_data(self, table_name: str, condition: str, columns: str = None) -> list:
        """
        Selects data from a table in the PostgreSQL database.

        Args:
            table_name (str): The name of the table to select data from.
            condition (str): The condition to filter the data.
            columns (str, optional): The columns to select. Defaults to None.

        Returns:
            list: A list of tuples representing the selected data.
        """
        with self.connection.cursor() as cursor:
            if columns:
                query = f"SELECT {columns} FROM {table_name} WHERE {condition}"
            else:
                query = f"SELECT * FROM {table_name} WHERE {condition}"

            cursor.execute(query)
            result = cursor.fetchall()
        return result

    def update_data(self, table_name: str, new_values: str, condition: str) -> None:
        """
        Update data in a table in the PostgreSQL database.

        Args:
            table_name (str): The name of the table to update.
            new_values (str): The new values to set in the table.
            condition (str): The condition to specify which rows to update.

        Returns:
            None
        """
        with self.connection.cursor() as cursor:
            query = f"UPDATE {table_name} SET {new_values} WHERE {condition}"
            cursor.execute(query)
        self.connection.commit()

    def delete_data(self, table_name: str, condition: str) -> None:
        """
        Delete data from a table in the PostgreSQL database.

        Args:
            table_name (str): The name of the table from which to delete data.
            condition (str): The condition to specify which rows to delete.

        Returns:
            None
        """
        with self.connection.cursor() as cursor:
            query = f"DELETE FROM {table_name} WHERE {condition}"
            cursor.execute(query)
        self.connection.commit()

    def upsert_rows(self, user_id: str, session_id: str, target_table: str, source_table: str, columns_target: str, columns_source: str, created_at: str) -> None:
        """
        Upsert data from source table to target table in the PostgreSQL database.

        Args:
            user_id (str): The user ID.
            session_id (str): The session ID.
            target_table (str): The name of the target table.
            source_table (str): The name of the source table.
            columns_target (str): The columns to be inserted into the target table.
            columns_source (str): The columns to be selected from the source table.
            created_at (str): The timestamp for when the data is inserted.

        Returns:
            None
        """
        with self.connection.cursor() as cursor:
            query = f"""INSERT INTO {target_table} ({columns_target})
                        SELECT '{user_id}',{columns_source},'{created_at}'
                        FROM {source_table} as a
                        WHERE a.session_id = '{session_id}'
                        AND NOT EXISTS (
                            SELECT 1 
                            FROM {target_table} 
                            WHERE {target_table}.message_id = a.id
                            AND {target_table}.session_id = a.session_id
                        )"""
            print(query)
            cursor.execute(query)
        self.connection.commit()

    def get_max_id_by_conversation_id(self, table_name: str, conversation_id: str) -> int:
        """
        Retrieves the maximum id for a given conversation_id from the PostgreSQL database.

        Args:
            conversation_id (str): The conversation_id to retrieve the maximum id for.

        Returns:
            int: The maximum id for the given conversation_id.
        """
        with self.connection.cursor() as cursor:
            query = f"SELECT MAX(id_message) FROM {table_name} WHERE conversation_id = '{conversation_id}'"
            cursor.execute(query)
            result = cursor.fetchone()
        return result[0] if result[0] else 0

    def close_connection(self):
        """
        Closes the PostgreSQL connection.

        This method closes the connection to the PostgreSQL database.

        Parameters:
        None

        Returns:
        None
        """
        # Close the PostgreSQL connection
        self.connection.close()


def main():
    """
    This is the main function that performs database operations using the PostgreSQL class.

    Parameters:
        None

    Returns:
        None
    """
    # Create an instance of the PostgreSQL class
    postgresql = PostgreSQL()

    # Perform database operations using the methods of the PostgreSQL class

    # Close the PostgreSQL connection
    postgresql.close_connection()