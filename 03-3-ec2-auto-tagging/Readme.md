# Assignment 3 — Auto-Tagging EC2 Instances on Launch

## Objective

Automatically tag an EC2 instance when it enters the running state.

## AWS Services

- Amazon EC2
- AWS Lambda
- AWS IAM
- Amazon EventBridge
- Amazon CloudWatch Logs

## Tags Applied

- LaunchDate
- Owner
- Environment
- ManagedBy

## Event Flow

EC2 running-state event → EventBridge rule → Lambda → EC2 CreateTags

## IAM Permissions

- ec2:DescribeInstances
- ec2:CreateTags

The Lambda execution role also uses AWSLambdaBasicExecutionRole for
CloudWatch logging.

## Event Pattern

The EventBridge rule matches:

- source: aws.ec2
- detail-type: EC2 Instance State-change Notification
- detail.state: running

## Testing

1. The Lambda function was first tested manually with a valid running
   EC2 instance ID.
2. The EventBridge rule was then enabled.
3. A new EC2 instance was launched.
4. The instance was automatically tagged after entering the running state.
5. Lambda execution was confirmed in CloudWatch Logs.

## Result

The automation successfully applied LaunchDate, Owner, Environment,
and ManagedBy tags to the launched EC2 instance.

## Cleanup

The temporary EC2 test instances were terminated after screenshots
were captured.
