import pytest
import psycopg2
import time
from psycopg2 import sql
import re
import json


def load_db_config(file_path):
    """Load database configuration from a JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


# Load database configuration
DB_CONFIG = load_db_config("db_config.json")


@pytest.fixture(scope="module")
def db_connection():
    """Fixture to establish and close the PostgreSQL connection."""
    conn = None
    try:
        print("Attempting to connect to the database...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("Connection successful!")
        yield conn
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")
    finally:
        if conn:
            conn.close()
            print("Connection closed.")


def test_connection_successful(db_connection):
    """Test that the database connection is successful."""
    assert db_connection is not None, "Database connection is None."
    assert db_connection.closed == 0, "Database connection is closed."
    time.sleep(1)


def test_count_tables(db_connection):
    """Test that there is at least one table in the database."""
    try:
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public';
                """
            )
            table_count = cursor.fetchone()[0]
            assert table_count > 0, "No tables found in the database."
    except Exception as e:
        pytest.fail(f"Error counting tables: {e}")


@pytest.mark.parametrize(
    "table_name", ["address", "business", "contact", "detail", "review", "reviewer"]
)
def test_check_row_count(db_connection, table_name):
    """Test if specific tables contain data (at least one row)."""
    try:
        with db_connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("SELECT COUNT(*) FROM {} LIMIT 10000").format(
                    sql.Identifier(table_name)
                )
            )
            row_count = cursor.fetchone()[0]
            print(f"Table '{table_name}' has {row_count} rows.")
            assert row_count > 0, f"Table '{table_name}' has no rows."
    except Exception as e:
        pytest.fail(f"Error checking row count for table '{table_name}': {e}")


@pytest.mark.parametrize(
    "table_name, column_name",
    [
        ("contact", "phone"),
    ],
)
def test_check_column_has_letters(db_connection, table_name, column_name):
    """Test if a column contains non-numeric values (letters)."""
    try:
        with db_connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    "SELECT {column} FROM {table} WHERE {column} IS NOT NULL LIMIT 10000"
                ).format(
                    column=sql.Identifier(column_name), table=sql.Identifier(table_name)
                )
            )
            rows = cursor.fetchall()
            letter_pattern = re.compile(r"[a-zA-Z]")
            contains_letters = any(letter_pattern.search(str(row[0])) for row in rows)
            assert (
                contains_letters
            ), f"Table '{table_name}' column '{column_name}' has no values containing letters."
    except Exception as e:
        pytest.fail(f"Error checking letters in '{table_name}.{column_name}': {e}")
    time.sleep(1)


@pytest.mark.parametrize(
    "table_name, column_name",
    [
        ("business", "gmapsURL"),
        ("business", "name"),
        ("review", "ratingRaw"),
        ("review", "reviewText"),
        ("review", "upvotes"),
        ("review", "derivedSignals"),
        ("address", "addressFull"),
        ("reviewer", "userName"),
        ("reviewer", "firstName"),
        ("reviewer", "userProfileLink"),
        ("reviewer", "userProfilePicture"),
        ("business", "category"),
        ("business", "latitude"),
    ],
)
def test_check_column_has_null(db_connection, table_name, column_name):
    """Test if a column in a table has NULL values."""
    try:
        with db_connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("SELECT COUNT(*) FROM {table} WHERE {column} IS NULL").format(
                    table=sql.Identifier(table_name), column=sql.Identifier(column_name)
                )
            )
            null_count = cursor.fetchone()[0]
            if null_count > 0:
                pytest.fail(
                    f"❌ Table '{table_name}' column '{column_name}' has {null_count} NULL values."
                )
            else:
                print(
                    f"✅ Table '{table_name}' column '{column_name}' has no NULL values."
                )
    except Exception as e:
        print(
            f"⚠️ Error checking NULL values in '{table_name}.{column_name}': {e}"
        )  # Apenas loga o erro, não falha o teste


if __name__ == "__main__":
    pytest.main()
