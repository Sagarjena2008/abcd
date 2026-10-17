import getpass
import secrets
from pathlib import Path

import mysql.connector
from mysql.connector import Error as MySQLError


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def main():
    if ENV_PATH.exists():
        raise SystemExit(
            ".env already exists. Back it up or remove it before setting up the database again."
        )

    new_root_password = secrets.token_urlsafe(32)
    app_password = secrets.token_urlsafe(32)
    connection = None
    try:
        try:
            connection = mysql.connector.connect(
                host="127.0.0.1",
                port=3306,
                user="root",
                password="",
                connection_timeout=5,
            )
        except MySQLError:
            root_password = getpass.getpass("MySQL root password: ")
            connection = mysql.connector.connect(
                host="127.0.0.1",
                port=3306,
                user="root",
                password=root_password,
                connection_timeout=5,
            )
        cursor = connection.cursor()
        for statement in SCHEMA_PATH.read_text(encoding="utf-8").split(";"):
            if statement.strip():
                cursor.execute(statement)
        cursor.execute(
            "CREATE USER IF NOT EXISTS 'gymkhana_app'@'127.0.0.1' IDENTIFIED BY %s",
            (app_password,),
        )
        cursor.execute(
            "ALTER USER 'gymkhana_app'@'127.0.0.1' IDENTIFIED BY %s",
            (app_password,),
        )
        cursor.execute(
            "GRANT SELECT, INSERT ON gymkhana.registrations TO 'gymkhana_app'@'127.0.0.1'"
        )
        cursor.execute(
            "ALTER USER 'root'@'localhost' IDENTIFIED BY %s",
            (new_root_password,),
        )
        cursor.close()
        connection.commit()
    except (MySQLError, OSError) as error:
        raise SystemExit(
            f"Database setup failed: {error}\nCheck that MySQL Server is running and the root password is correct."
        ) from error
    finally:
        if connection and connection.is_connected():
            connection.close()

    ENV_PATH.write_text(
        "\n".join(
            (
                "MYSQL_HOST=127.0.0.1",
                "MYSQL_PORT=3306",
                "MYSQL_DATABASE=gymkhana",
                "MYSQL_USER=gymkhana_app",
                f"MYSQL_PASSWORD={app_password}",
                f"MYSQL_ROOT_PASSWORD={new_root_password}",
                "APP_HOST=127.0.0.1",
                "APP_PORT=5000",
                "",
            )
        ),
        encoding="utf-8",
    )
    print("Database and restricted application account are ready. Local credentials saved in .env.")


if __name__ == "__main__":
    main()
