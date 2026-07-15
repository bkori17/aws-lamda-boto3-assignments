# AWS Assignment 1 – Automated S3 Bucket Cleanup

## Objective

Automate the deletion of Amazon S3 objects older than 30 days using
AWS Lambda, Python, Boto3, IAM and CloudWatch Logs.

## Architecture

Manual Invocation
       |
       v
AWS Lambda
       |
       | List objects using paginator
       | Compare LastModified with UTC cutoff
       | Delete objects older than retention period
       v
Amazon S3
       |
       v
CloudWatch Logs

## AWS Services Used

- Amazon S3
- AWS Lambda
- AWS IAM
- Amazon CloudWatch Logs
- Boto3

## Implementation

1. Created a private S3 test bucket in us-east-1.
2. Uploaded test files.
3. Created a Python 3.12 Lambda function.
4. Added a least-privilege IAM inline policy.
5. Used the Boto3 ListObjectsV2 paginator.
6. Compared timezone-aware LastModified timestamps with UTC time.
7. Tested with a temporary five-minute threshold.
8. Confirmed old objects were deleted and the newer object remained.
9. Restored the final retention period to 30 days.

## Required IAM Permissions

- s3:ListBucket on the specific bucket
- s3:DeleteObject on objects in the specific bucket
- AWSLambdaBasicExecutionRole for CloudWatch Logs

## Final Configuration

- RETENTION_DAYS=30
- TEST_AGE_MINUTES=0
- DRY_RUN=false

## Test Result

The Lambda function successfully deleted objects older than the
temporary test threshold and retained the newer object. CloudWatch
Logs displayed the names of all deleted objects.



## Cost and Cleanup

The resources were created only for testing. After collecting
screenshots, the Lambda function, CloudWatch log group, IAM role,
test objects and S3 bucket were removed to avoid unnecessary charges.