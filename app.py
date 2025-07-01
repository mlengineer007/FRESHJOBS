from flask import Flask, render_template, request
import boto3
import csv
import io
import ast
from datetime import datetime
import os 
from dotenv import load_dotenv

load_dotenv()

aws_region = os.getenv('AWS_REGION')
aws_endpoint = os.getenv('aws_endpoint')
aws_access_key_id = os.getenv('aws_access_key')
aws_secret_access_key = os.getenv('aws_secret_access_key')

app = Flask(__name__)

# ✅ Skill cleaner function
def clean_skill_list(skills):
    return [skill.replace(" ", "").strip() for skill in skills if skill.strip()]

@app.route('/')
def index():
    s3 = boto3.client(
        's3',
        region_name=aws_region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
    bucket = 'freshjoblanding'
    key = 'skills_linkedin_jobs.csv'

    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')

        reader = csv.DictReader(io.StringIO(content))
        jobs = []

        for row in reader:
            # ✅ Parse and clean skills
            if 'skills' in row and row['skills']:
                try:
                    parsed_skills = ast.literal_eval(row['skills'])
                    row['skills'] = clean_skill_list(parsed_skills)
                except Exception:
                    row['skills'] = []
            else:
                row['skills'] = []

            # ✅ Parse and format date
            try:
                posted_date = datetime.strptime(row['posted_at'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                posted_date = datetime.strptime(row['posted_at'], '%Y-%m-%d')

            row['posted_at'] = posted_date
            row['posted_ago'] = f"{(datetime.today() - posted_date).days} days ago"

            jobs.append(row)

        # ✅ Sort jobs by posted date
        jobs = sorted(jobs, key=lambda x: x['posted_at'], reverse=True)

        # ✅ Pagination
        page = int(request.args.get('page', 1))
        per_page = 20
        start = (page - 1) * per_page
        end = start + per_page
        paginated_jobs = jobs[start:end]
        has_next = end < len(jobs)

        return render_template('index.html', jobs=paginated_jobs, page=page, has_next=has_next)

    except Exception as e:
        return f"Error fetching jobs: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
