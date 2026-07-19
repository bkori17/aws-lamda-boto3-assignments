# Assignment 2 – Automated EBS Snapshot Creation and Cleanup

## 1. Objective

Automate weekly EBS volume backups and delete snapshots older than
30 days using AWS Lambda, Python 3.12, Boto3 and EventBridge
Scheduler.

## 2. Architecture

EventBridge Scheduler
        |
        v
AWS Lambda
        |
        +--> Create and tag EBS snapshot
        |
        +--> List snapshots owned by this account
        |
        +--> Delete tagged snapshots older than 30 days
        |
        v
CloudWatch Logs

## 3. AWS Services Used

- Amazon EBS
- AWS Lambda
- AWS IAM
- Amazon EventBridge Scheduler
- Amazon CloudWatch Logs
- Boto3

## 4. Implementation Steps

1. Created a 1 GiB gp3 EBS test volume in ap-south-1.
2. Recorded the volume ID.
3. Created a Python 3.12 Lambda function.
4. Added a least-privilege inline IAM policy.
5. Configured the volume ID and retention settings as environment variables.
6. Created and tagged snapshots using Boto3.
7. Listed owned snapshots using a paginator and tag filter.
8. Tested cleanup using a temporary five-minute threshold.
9. Restored the final retention period to 30 days.
10. Created a weekly EventBridge Scheduler schedule.

## 5. IAM Permissions

The Lambda execution role was granted only:

- ec2:CreateSnapshot
- ec2:DescribeSnapshots
- ec2:DeleteSnapshot
- ec2:CreateTags

AWSLambdaBasicExecutionRole was used for CloudWatch logging.
No AdministratorAccess or AmazonEC2FullAccess policy was attached.

## 6. Testing and Results

The first invocation created a snapshot tagged
CreatedBy=Lambda-Backup. After the temporary retention threshold
elapsed, the next invocation created a new snapshot and deleted the
older tagged snapshot. The created and deleted snapshot IDs were
printed in CloudWatch Logs.

Final configuration:

- RETENTION_DAYS=30
- TEST_RETENTION_MINUTES=0
- Schedule=rate(7 days)

## 7. Challenges Faced

The initial snapshot appeared in the pending state, so the cleanup
logic skipped it until it reached the completed state. I also
verified that the volume ID in the Lambda environment variable
exactly matched the test EBS volume.

