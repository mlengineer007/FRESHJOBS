import boto3


s3_client= boto3.client('s3')
response = s3_client.upload_file("linkedin_jobs.csv","freshjoblanding","linkedin_jobs_raw.csv")

