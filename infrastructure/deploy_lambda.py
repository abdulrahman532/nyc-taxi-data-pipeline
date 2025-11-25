"""
AWS Lambda deployment script.

Automates deployment of the NYC Taxi ingestion Lambda function.
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import time
import zipfile

import boto3

AWS_REGION = "us-east-1"
LAMBDA_FUNCTION_NAME = "NYCTaxiIngestionLambda"
S3_BUCKET_NAME = "nyc-tlc-data-raw-prod"
IAM_ROLE_NAME = "NYCTaxiIngestionLambdaRole"
LAMBDA_SOURCE_FILE = "lambda_function.py"
LAMBDA_TIMEOUT_SECONDS = 300

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_iam_role(iam_client):
    """Create or retrieve IAM role."""
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]
    }
    try:
        role = iam_client.get_role(RoleName=IAM_ROLE_NAME)
        return role["Role"]["Arn"]
    except iam_client.exceptions.NoSuchEntityException:
        role = iam_client.create_role(RoleName=IAM_ROLE_NAME, AssumeRolePolicyDocument=json.dumps(trust_policy))
        iam_client.attach_role_policy(RoleName=IAM_ROLE_NAME, PolicyArn="arn:aws:iam::aws:policy/AmazonS3FullAccess")
        iam_client.attach_role_policy(RoleName=IAM_ROLE_NAME, PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")
        time.sleep(10)
        return role["Role"]["Arn"]


def prepare_deployment_package():
    """Create deployment zip."""
    build_dir = "build_package"
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-t", build_dir], stdout=subprocess.DEVNULL)
    shutil.copy(LAMBDA_SOURCE_FILE, os.path.join(build_dir, "lambda_function.py"))
    zip_path = "lambda_deployment.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(build_dir):
            for f in files:
                zf.write(os.path.join(root, f), os.path.relpath(os.path.join(root, f), build_dir))
    shutil.rmtree(build_dir)
    return zip_path


def deploy_lambda_function(lambda_client, zip_path, role_arn):
    """Deploy Lambda function."""
    with open(zip_path, "rb") as f:
        code = f.read()
    try:
        lambda_client.update_function_code(FunctionName=LAMBDA_FUNCTION_NAME, ZipFile=code)
        time.sleep(5)
        lambda_client.update_function_configuration(
            FunctionName=LAMBDA_FUNCTION_NAME, Timeout=LAMBDA_TIMEOUT_SECONDS,
            Environment={"Variables": {"BUCKET_NAME": S3_BUCKET_NAME}}
        )
    except lambda_client.exceptions.ResourceNotFoundException:
        lambda_client.create_function(
            FunctionName=LAMBDA_FUNCTION_NAME, Runtime="python3.9", Role=role_arn,
            Handler="lambda_function.lambda_handler", Code={"ZipFile": code},
            Timeout=LAMBDA_TIMEOUT_SECONDS, Environment={"Variables": {"BUCKET_NAME": S3_BUCKET_NAME}}
        )


def main():
    session = boto3.Session(region_name=AWS_REGION)
    role_arn = create_iam_role(session.client("iam"))
    zip_pkg = prepare_deployment_package()
    deploy_lambda_function(session.client("lambda"), zip_pkg, role_arn)
    os.remove(zip_pkg)
    logger.info("Deployment complete!")


if __name__ == "__main__":
    main()
