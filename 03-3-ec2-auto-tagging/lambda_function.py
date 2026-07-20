import json
import logging
import os
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


# Create the EC2 client once, outside the handler.
# Lambda can reuse this client during warm invocations.
ec2 = boto3.client("ec2")

# Configure structured messages for CloudWatch Logs.
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Add standard tags to an EC2 instance when EventBridge reports that
    the instance has entered the running state.

    Expected EventBridge field:
        event["detail"]["instance-id"]
    """

    logger.info("Received event: %s", json.dumps(event))

    try:
        # The assignment specifically requires the instance ID to be
        # extracted from detail.instance-id.
        instance_id = event["detail"]["instance-id"]

        # Read customizable tag values from Lambda environment variables.
        owner = os.environ.get("OWNER", "Unknown")
        environment = os.environ.get("ENVIRONMENT", "Development")

        # Get the current date in UTC.
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Describe the instance to confirm that it exists and to inspect
        # its current state and existing tags.
        response = ec2.describe_instances(InstanceIds=[instance_id])

        reservations = response.get("Reservations", [])
        if not reservations or not reservations[0].get("Instances"):
            raise ValueError(f"Instance {instance_id} was not found")

        instance = reservations[0]["Instances"][0]
        instance_state = instance["State"]["Name"]
        existing_tags = {
            tag["Key"]: tag["Value"]
            for tag in instance.get("Tags", [])
        }

        logger.info(
            "Instance %s is currently in state %s",
            instance_id,
            instance_state,
        )

        # Normally this function is invoked only for a running-state event.
        # This check also protects against an incorrect manual test event.
        if instance_state != "running":
            message = (
                f"Instance {instance_id} is in state '{instance_state}', "
                "so no tags were added."
            )
            logger.warning(message)

            return {
                "statusCode": 200,
                "body": message,
            }

        # Preserve the first LaunchDate if the instance was tagged earlier.
        # This prevents a stop/start operation from replacing the launch date.
        launch_date = existing_tags.get("LaunchDate", current_date)

        tags_to_apply = [
            {
                "Key": "LaunchDate",
                "Value": launch_date,
            },
            {
                "Key": "Owner",
                "Value": owner,
            },
            {
                "Key": "Environment",
                "Value": environment,
            },
            {
                "Key": "ManagedBy",
                "Value": "Lambda",
            },
        ]

        # Add or update the specified tags on the EC2 instance.
        ec2.create_tags(
            Resources=[instance_id],
            Tags=tags_to_apply,
        )

        confirmation = (
            f"Successfully tagged EC2 instance {instance_id}: "
            f"LaunchDate={launch_date}, "
            f"Owner={owner}, "
            f"Environment={environment}, "
            "ManagedBy=Lambda"
        )

        # This confirmation appears in the Lambda test output and
        # CloudWatch Logs.
        logger.info(confirmation)
        print(confirmation)

        return {
            "statusCode": 200,
            "instanceId": instance_id,
            "tagsApplied": tags_to_apply,
            "body": confirmation,
        }

    except KeyError as error:
        logger.exception(
            "Invalid event: detail.instance-id is missing"
        )
        raise ValueError(
            "The event must contain detail.instance-id"
        ) from error

    except ClientError as error:
        logger.exception(
            "AWS API error while tagging the EC2 instance"
        )
        raise

    except Exception:
        logger.exception(
            "Unexpected error while processing the EC2 event"
        )
        raise