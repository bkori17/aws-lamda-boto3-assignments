import json
import os
from datetime import datetime, timedelta, timezone

import boto3
from botocore.exceptions import ClientError


# Create the S3 client.
# Boto3 is already available in the AWS Lambda Python runtime.
s3_client = boto3.client("s3")


def lambda_handler(event, context):
    """
    Delete objects older than the configured retention period.

    Final production settings:
        RETENTION_DAYS=30
        TEST_AGE_MINUTES=0
        DRY_RUN=false

    Temporary test settings:
        RETENTION_DAYS=30
        TEST_AGE_MINUTES=5
        DRY_RUN=true or false
    """

    # Read values from Lambda environment variables.
    bucket_name = os.environ["BUCKET_NAME"]
    retention_days = int(os.environ.get("RETENTION_DAYS", "30"))
    test_age_minutes = int(os.environ.get("TEST_AGE_MINUTES", "0"))
    dry_run = os.environ.get("DRY_RUN", "true").lower() == "true"

    # Current time must be timezone-aware and in UTC.
    current_time = datetime.now(timezone.utc)

    # Use minutes only while testing.
    # When TEST_AGE_MINUTES is 0, use the required 30-day value.
    if test_age_minutes > 0:
        cutoff_time = current_time - timedelta(minutes=test_age_minutes)
        active_threshold = f"{test_age_minutes} minute(s)"
        execution_mode = "TEST"
    else:
        cutoff_time = current_time - timedelta(days=retention_days)
        active_threshold = f"{retention_days} day(s)"
        execution_mode = "FINAL-30-DAY"

    print("==================================================")
    print("S3 CLEANUP STARTED")
    print(f"Bucket name       : {bucket_name}")
    print(f"Execution mode    : {execution_mode}")
    print(f"Current UTC time  : {current_time.isoformat()}")
    print(f"Cutoff UTC time   : {cutoff_time.isoformat()}")
    print(f"Active threshold  : {active_threshold}")
    print(f"Dry run           : {dry_run}")
    print("==================================================")

    scanned_count = 0
    eligible_count = 0
    deleted_count = 0
    deleted_objects = []

    try:
        # Never assume that S3 returns all objects in one response.
        # The paginator processes every response page.
        paginator = s3_client.get_paginator("list_objects_v2")

        pages = paginator.paginate(Bucket=bucket_name)

        for page in pages:
            # An empty bucket may not contain the "Contents" key.
            objects = page.get("Contents", [])

            for s3_object in objects:
                scanned_count += 1

                object_key = s3_object["Key"]
                last_modified = s3_object["LastModified"]

                print("----------------------------------------------")
                print(f"Checking object : {object_key}")
                print(f"Last modified   : {last_modified.isoformat()}")

                # last_modified and cutoff_time are both timezone-aware.
                if last_modified < cutoff_time:
                    eligible_count += 1

                    print(f"Eligible        : YES - older than {active_threshold}")

                    if dry_run:
                        print(f"[DRY RUN] Would delete: {object_key}")
                    else:
                        s3_client.delete_object(
                            Bucket=bucket_name,
                            Key=object_key
                        )

                        deleted_count += 1
                        deleted_objects.append(object_key)

                        # Assignment explicitly asks us to print deleted names.
                        print(f"DELETED OBJECT  : {object_key}")
                else:
                    print("Eligible        : NO")
                    print(f"RETAINED OBJECT : {object_key}")

        result = {
            "status": "SUCCESS",
            "bucket": bucket_name,
            "execution_mode": execution_mode,
            "active_threshold": active_threshold,
            "dry_run": dry_run,
            "scanned_count": scanned_count,
            "eligible_count": eligible_count,
            "deleted_count": deleted_count,
            "deleted_objects": deleted_objects
        }

        print("==================================================")
        print("S3 CLEANUP COMPLETED")
        print(f"Objects scanned  : {scanned_count}")
        print(f"Objects eligible : {eligible_count}")
        print(f"Objects deleted  : {deleted_count}")
        print(f"Deleted names    : {deleted_objects}")
        print("==================================================")

        return {
            "statusCode": 200,
            "body": json.dumps(result)
        }

    except ClientError as error:
        print("AWS CLIENT ERROR")
        print(str(error))

        return {
            "statusCode": 500,
            "body": json.dumps({
                "status": "FAILED",
                "error": str(error)
            })
        }

    except Exception as error:
        print("UNEXPECTED ERROR")
        print(str(error))

        return {
            "statusCode": 500,
            "body": json.dumps({
                "status": "FAILED",
                "error": str(error)
            })
        }