from flask import Flask, render_template, request
import boto3
import csv
import io
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    s3 = boto3.client('s3')
    bucket = 'freshjoblanding'
    key = 'enriched_linkedin_jobs.csv'

    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')

        reader = csv.DictReader(io.StringIO(content))
        jobs = []
        for row in reader:
            try:
                posted_date = datetime.strptime(row['posted_at'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                posted_date = datetime.strptime(row['posted_at'], '%Y-%m-%d')

            row['posted_at'] = posted_date  # Convert to datetime for strftime
            row['posted_ago'] = f"{(datetime.today() - posted_date).days} days ago"
            jobs.append(row)

        # Sort jobs by posted date, newest first
        jobs = sorted(jobs, key=lambda x: x['posted_at'], reverse=True)

        # --- Pagination ---
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
    app.run(debug=True)
