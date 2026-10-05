import os
import io
import boto3
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from botocore.client import Config

load_dotenv()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")

BRONZE_BUCKET = "bronze"

PG_CONFIG = {
    "host": "localhost",
    "port": 5435,
    "dbname": "plateforme_db",
    "user": "plateforme_user",
    "password": "plateforme_password",
}

s3_client = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
)

engine = create_engine(
    f"postgresql+psycopg2://{PG_CONFIG['user']}:{PG_CONFIG['password']}"
    f"@{PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['dbname']}"
)


def table_name_from_key(object_key):
    file_name = os.path.basename(object_key)
    name_without_extension = os.path.splitext(file_name)[0]
    return f"raw_{name_without_extension}".lower()


def load_prefix(prefix):
    response = s3_client.list_objects_v2(Bucket=BRONZE_BUCKET, Prefix=prefix)
    objects = response.get("Contents", [])

    for obj in objects:
        object_key = obj["Key"]
        print(f"Lecture -> {object_key}")

        file_obj = s3_client.get_object(Bucket=BRONZE_BUCKET, Key=object_key)
        csv_bytes = file_obj["Body"].read()

        df = pd.read_csv(io.BytesIO(csv_bytes), encoding="latin1")

        table_name = table_name_from_key(object_key)
        df.to_sql(table_name, engine, if_exists="replace", index=False)

        print(f"ChargÃ© -> table {table_name} ({len(df)} lignes)")


def main():
    print("Chargement des fichiers Olist depuis MinIO vers PostgreSQL...")
    load_prefix("olist/")

    print("Chargement du fichier Superstore depuis MinIO vers PostgreSQL...")
    load_prefix("superstore/")

    print("\nChargement terminÃ©.")


if __name__ == "__main__":
    main()
