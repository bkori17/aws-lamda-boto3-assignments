# README.md

# AWS Assignment 4 – Automated AWS Cost Alert Using Cost Explorer API and SNS

## Objective

The objective of this assignment is to build an automated AWS cost monitoring solution that checks the month-to-date AWS spending using the AWS Cost Explorer API. If the total AWS cost exceeds a predefined threshold, the solution automatically sends an email notification using Amazon SNS.

---

## AWS Services Used

* AWS Lambda
* AWS Cost Explorer API
* Amazon SNS
* Amazon EventBridge
* IAM
* Amazon CloudWatch

---

## Solution Overview

The solution runs once every day using Amazon EventBridge. EventBridge invokes the Lambda function, which retrieves the current month's UnblendedCost using the AWS Cost Explorer API. The retrieved amount is compared with a configured threshold.

If the current cost exceeds the threshold, the Lambda function publishes a notification to an Amazon SNS topic, which sends an email to the subscribed recipient.

The Lambda function also logs the current AWS spending and the execution status in Amazon CloudWatch Logs.

---

## Implementation Steps

1. Created an SNS topic named **DailyCostAlert**.
2. Subscribed an email address and confirmed the subscription.
3. Created an IAM role for Lambda.
4. Attached the AWSLambdaBasicExecutionRole managed policy.
5. Added a least-privilege inline policy allowing:

   * ce
   * sns
6. Created a Python 3.12 Lambda function.
7. Implemented Boto3 code to:

   * Read month-to-date AWS cost.
   * Compare the cost with a threshold.
   * Send an SNS email alert if the threshold is exceeded.
   * Print the retrieved cost to CloudWatch Logs.
8. Configured an EventBridge rule to invoke the Lambda function daily.
9. Tested the solution by temporarily reducing the threshold to $0.01 to force an alert.
10. Restored the production threshold after successful testing.

---

## Testing Performed

* Executed the Lambda function manually.
* Verified the current AWS cost was retrieved successfully.
* Confirmed the SNS email notification was received.
* Verified CloudWatch Logs contained the retrieved cost and execution status.
* Confirmed EventBridge was configured successfully.

---

## Results

The Lambda function successfully retrieves the current month's AWS spending using the Cost Explorer API.

When the spending exceeds the configured threshold, an email notification is delivered through Amazon SNS.

All executions are recorded in CloudWatch Logs for monitoring and troubleshooting.

---

## IAM Permissions Used

* ce
* sns
* AWSLambdaBasicExecutionRole

These permissions follow the principle of least privilege.

---

## Discussion

AWS Budgets is the recommended managed service for standard cost alerts because it requires minimal configuration and maintenance.

A custom Lambda solution provides greater flexibility when advanced logic is required, such as:

* Per-service cost reporting.
* Custom spending calculations.
* Integration with Slack or Microsoft Teams.
* Custom anomaly detection.
* Integration with external applications using APIs.

---

## Cleanup

After testing:

* Disabled or deleted the EventBridge rule.
* Deleted the Lambda function if no longer required.
* Deleted the SNS topic if not reused.
* Deleted the IAM role created specifically for this assignment.
* Retained only the source code, documentation, and screenshots for submission.

---

## Repository Structure

assignment-4-daily-cost-alert/

* lambda_function.py
* IAM_Inline_Policy.json
* README.md
* Architecture_Document.md
* assignment-4-aws-cost-alert-using-CEAPI-SNS.docx

---

## Conclusion

This assignment demonstrates how AWS Lambda, Cost Explorer API,
 Amazon SNS, and EventBridge can be integrated to build an automated
 daily AWS cost monitoring solution. The implementation follows 
 AWS best practices by using least-privilege IAM permissions, 
 serverless architecture, and automated scheduling.
