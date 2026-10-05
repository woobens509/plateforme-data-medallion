import os
import glob
import boto3
from dotenv import load_dotenv
from botocore.client import Config

load_dotenv()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")

BRONZE_BUCKET = "bronze"

s3_client = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
)


def upload_folder(local_folder, bucket, prefix):
    files = glob.glob(os.path.join(local_folder, "*.csv"))
    for file_path in files:
        file_name = os.path.basename(file_path)
        object_key = f"{prefix}/{file_name}"
        s3_client.upload_file(file_path, bucket, object_key)
        print(f"EnvoyÃ© -> {bucket}/{object_key}")


def main():
    print("Ingestion des fichiers Olist vers la couche bronze...")
    upload_folder("data/olist", BRONZE_BUCKET, "olist")

    print("Ingestion du fichier Superstore vers la couche bronze...")
    upload_folder("data/superstore", BRONZE_BUCKET, "superstore")

    print("\nIngestion terminÃ©e.")


if __name__ == "__main__":
    main()
