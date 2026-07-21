import boto3
from datetime import datetime

ce = boto3.client("ce")
sns = boto3.client("sns")

TOPIC_ARN = "arn:aws:sns:us-east-1:3784948679:DailyCostAlert"

THRESHOLD = 50.0


def lambda_handler(event, context):

    today = datetime.utcnow().date()

    start = today.replace(day=1).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")

    response = ce.get_cost_and_usage(
        TimePeriod={
            "Start": start,
            "End": end
        },
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"]
    )

    amount = float(
        response["ResultsByTime"][0]
        ["Total"]["UnblendedCost"]["Amount"]
    )

    print(f"Current AWS Cost = ${amount}")

    if amount > THRESHOLD:

        message = (
            f"AWS spending has exceeded the threshold.\n\n"
            f"Current Spend: ${amount:.2f}\n"
            f"Threshold: ${THRESHOLD:.2f}"
        )

        sns.publish(
            TopicArn=TOPIC_ARN,
            Subject="AWS Daily Cost Alert",
            Message=message
        )

        print("SNS Notification Sent")

    else:

        print("Cost below threshold")

    return {
        "statusCode": 200,
        "body": amount
    }