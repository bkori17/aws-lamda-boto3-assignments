import json
import os
from datetime import datetime, timedelta, timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError


# Boto3 EC2 client.
# Amazon EBS APIs are accessed through the EC2 client.
ec2_client = boto3.client("ec2")


def get_snapshot_name(snapshot):
    """Return the Name tag when present."""
    for tag in snapshot.get("Tags", []):
        if tag.get("Key") == "Name":
            return tag.get("Value", "")
    return ""


def lambda_handler(event, context):
    """
    Create a tagged snapshot for one EBS volume and delete tagged
    snapshots older than the configured retention period.

    Final settings:
        RETENTION_DAYS=30
        TEST_RETENTION_MINUTES=0

    Temporary cleanup test:
        RETENTION_DAYS=30
        TEST_RETENTION_MINUTES=5
    """

    volume_id = os.environ["VOLUME_ID"]
    retention_days = int(os.environ.get("RETENTION_DAYS", "30"))
    test_retention_minutes = int(
        os.environ.get("TEST_RETENTION_MINUTES", "0")
    )
    tag_key = os.environ.get("SNAPSHOT_TAG_KEY", "CreatedBy")
    tag_value = os.environ.get(
        "SNAPSHOT_TAG_VALUE",
        "Lambda-Backup"
    )

    if retention_days < 0:
        raise ValueError("RETENTION_DAYS cannot be negative.")

    if test_retention_minutes < 0:
        raise ValueError(
            "TEST_RETENTION_MINUTES cannot be negative."
        )

    current_time_utc = datetime.now(timezone.utc)
    snapshot_name = (
        "Lambda-Backup-"
        + current_time_utc.strftime("%Y%m%d-%H%M%S-UTC")
    )

    print("=" * 60)
    print("EBS SNAPSHOT CREATION AND CLEANUP STARTED")
    print(f"Volume ID          : {volume_id}")
    print(f"Current UTC time   : {current_time_utc.isoformat()}")
    print(f"Backup tag         : {tag_key}={tag_value}")
    print("=" * 60)

    created_snapshot_id = None
    deleted_snapshot_ids = []
    retained_snapshot_ids = []
    skipped_snapshot_ids = []
    failed_snapshot_ids = []

    try:
        # ------------------------------------------------------------
        # STEP 1: CREATE A NEW SNAPSHOT
        # ------------------------------------------------------------
        create_response = ec2_client.create_snapshot(
            VolumeId=volume_id,
            Description=(
                f"Automated Lambda backup of {volume_id} "
                f"created at {current_time_utc.isoformat()}"
            ),
            TagSpecifications=[
                {
                    "ResourceType": "snapshot",
                    "Tags": [
                        {
                            "Key": tag_key,
                            "Value": tag_value
                        },
                        {
                            "Key": "Name",
                            "Value": snapshot_name
                        },
                        {
                            "Key": "SourceVolume",
                            "Value": volume_id
                        },
                        {
                            "Key": "RetentionDays",
                            "Value": str(retention_days)
                        }
                    ]
                }
            ]
        )

        created_snapshot_id = create_response["SnapshotId"]

        # The assignment explicitly asks us to print created IDs.
        print(f"CREATED SNAPSHOT ID : {created_snapshot_id}")
        print(
            f"Initial state       : "
            f"{create_response.get('State', 'unknown')}"
        )

        # ------------------------------------------------------------
        # STEP 2: CALCULATE THE CLEANUP CUTOFF
        # ------------------------------------------------------------
        if test_retention_minutes > 0:
            cutoff_time_utc = current_time_utc - timedelta(
                minutes=test_retention_minutes
            )
            execution_mode = "TEST"
            threshold_description = (
                f"{test_retention_minutes} minute(s)"
            )
        else:
            cutoff_time_utc = current_time_utc - timedelta(
                days=retention_days
            )
            execution_mode = "FINAL-30-DAY"
            threshold_description = f"{retention_days} day(s)"

        print("-" * 60)
        print(f"Cleanup mode        : {execution_mode}")
        print(f"Retention threshold : {threshold_description}")
        print(f"Cutoff UTC time     : {cutoff_time_utc.isoformat()}")
        print("-" * 60)

        # ------------------------------------------------------------
        # STEP 3: LIST ALL OWNED SNAPSHOTS WITH OUR BACKUP TAG
        # ------------------------------------------------------------
        paginator = ec2_client.get_paginator(
            "describe_snapshots"
        )

        pages = paginator.paginate(
            OwnerIds=["self"],
            Filters=[
                {
                    "Name": f"tag:{tag_key}",
                    "Values": [tag_value]
                },
                {
                    "Name": "volume-id",
                    "Values": [volume_id]
                }
            ]
        )

        scanned_count = 0

        for page in pages:
            for snapshot in page.get("Snapshots", []):
                scanned_count += 1

                snapshot_id = snapshot["SnapshotId"]
                start_time = snapshot["StartTime"]
                snapshot_state = snapshot.get("State", "unknown")
                snapshot_name_value = get_snapshot_name(snapshot)

                print("-" * 60)
                print(f"Checking snapshot : {snapshot_id}")
                print(f"Snapshot name     : {snapshot_name_value}")
                print(f"Source volume     : {snapshot.get('VolumeId')}")
                print(f"Start time        : {start_time.isoformat()}")
                print(f"State             : {snapshot_state}")

                # Never try to remove the snapshot created in this run.
                if snapshot_id == created_snapshot_id:
                    retained_snapshot_ids.append(snapshot_id)
                    print(
                        "RETAINED           : Snapshot created "
                        "during this invocation"
                    )
                    continue

                # Do not delete pending or error-state snapshots.
                if snapshot_state != "completed":
                    skipped_snapshot_ids.append(snapshot_id)
                    print(
                        "SKIPPED            : Snapshot is not completed"
                    )
                    continue

                if start_time < cutoff_time_utc:
                    try:
                        ec2_client.delete_snapshot(
                            SnapshotId=snapshot_id
                        )

                        deleted_snapshot_ids.append(snapshot_id)

                        # Assignment explicitly asks us to print deleted IDs.
                        print(
                            f"DELETED SNAPSHOT ID: {snapshot_id}"
                        )

                    except ClientError as delete_error:
                        failed_snapshot_ids.append(snapshot_id)
                        print(
                            f"FAILED TO DELETE   : {snapshot_id}"
                        )
                        print(str(delete_error))
                else:
                    retained_snapshot_ids.append(snapshot_id)
                    print(
                        "RETAINED           : Snapshot is newer "
                        "than the cutoff"
                    )

        result = {
            "status": "SUCCESS",
            "volume_id": volume_id,
            "execution_mode": execution_mode,
            "retention_threshold": threshold_description,
            "created_snapshot_id": created_snapshot_id,
            "scanned_count": scanned_count,
            "deleted_count": len(deleted_snapshot_ids),
            "deleted_snapshot_ids": deleted_snapshot_ids,
            "retained_snapshot_ids": retained_snapshot_ids,
            "skipped_snapshot_ids": skipped_snapshot_ids,
            "failed_snapshot_ids": failed_snapshot_ids
        }

        print("=" * 60)
        print("EBS SNAPSHOT CREATION AND CLEANUP COMPLETED")
        print(f"CREATED SNAPSHOT ID : {created_snapshot_id}")
        print(f"DELETED SNAPSHOT IDs: {deleted_snapshot_ids}")
        print(f"RETAINED SNAPSHOTS  : {retained_snapshot_ids}")
        print(f"SKIPPED SNAPSHOTS   : {skipped_snapshot_ids}")
        print(f"FAILED DELETIONS    : {failed_snapshot_ids}")
        print("=" * 60)

        return {
            "statusCode": 200,
            "body": json.dumps(result)
        }

    except (ClientError, BotoCoreError) as aws_error:
        print("AWS ERROR")
        print(str(aws_error))

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "status": "FAILED",
                    "created_snapshot_id": created_snapshot_id,
                    "error": str(aws_error)
                }
            )
        }

    except (KeyError, TypeError, ValueError) as error:
        print("CONFIGURATION OR DATA ERROR")
        print(str(error))

        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "status": "FAILED",
                    "created_snapshot_id": created_snapshot_id,
                    "error": str(error)
                }
            )
        }