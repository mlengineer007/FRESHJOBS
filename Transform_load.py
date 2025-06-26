#linkedin_jobs_raw.csv
import pandas as pd
import boto3
from datetime import datetime
from io import  StringIO
import csv

s3_client= boto3.client('s3')
response = s3_client.get_object(Key = 'linkedin_jobs_raw.csv', Bucket='freshjoblanding')

#print(response['Body'].read())

df= pd.read_csv(response['Body'], header = 0 )


#df1 = pd.read_csv('linkedin_jobs.csv', header=0)

print(df)

today= datetime.now()

df["posted_ago"] = (today - pd.to_datetime(df['posted_at'])).dt.days
df = df.sort_values(by='posted_ago')


df.to_csv("enriched_linked_job.csv",header=1)

s3_client.upload_file("enriched_linked_job.csv", "freshjoblanding" , Key= "enriched_linkedin_jobs.csv")



#print(df[['job_title'],['posted_at'],['posted_ago']])


