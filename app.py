from flask import Flask, render_template, request, jsonify, session
import boto3
import csv
import io
import ast
from datetime import datetime
import os 
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import PyPDF2
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import numpy as np

load_dotenv()

aws_region = os.getenv('AWS_REGION')
aws_endpoint = os.getenv('aws_endpoint')
aws_access_key_id = os.getenv('aws_access_key')
aws_secret_access_key = os.getenv('aws_secret_access_key')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""

def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting DOCX: {e}")
        return ""

def extract_text_from_txt(file_path):
    """Extract text from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error extracting TXT: {e}")
        return ""

def extract_resume_text(file_path):
    """Extract text based on file extension"""
    file_ext = file_path.split('.')[-1].lower()
    
    if file_ext == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_ext == 'docx':
        return extract_text_from_docx(file_path)
    elif file_ext == 'txt':
        return extract_text_from_txt(file_path)
    else:
        return ""

def extract_skills_from_resume(resume_text):
    """
    llm = HuggingFaceEndpoint(
    repo_id="microsoft/Phi-3-mini-4k-instruct",
    task="text-generation",
    max_new_tokens=512,
    do_sample=False,
    repetition_penalty=1.03,
)

    chat = ChatHuggingFace(llm=llm, verbose=True)
    parser = CommaSeparatedListOutputParser()
    """
    # Common tech skills (you can expand this list)
    common_skills = [
        'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js', 'django', 'flask',
        'html', 'css', 'sql', 'mongodb', 'postgresql', 'mysql', 'aws', 'azure', 'docker',
        'kubernetes', 'git', 'machine learning', 'data science', 'pandas', 'numpy', 'tensorflow',
        'pytorch', 'c++', 'c#', '.net', 'spring', 'hibernate', 'rest api', 'graphql',
        'microservices', 'agile', 'scrum', 'devops', 'ci/cd', 'jenkins', 'linux', 'bash'
    ]
    
    resume_lower = resume_text.lower()
    found_skills = []
    
    for skill in common_skills:
        if skill in resume_lower:
            found_skills.append(skill)
    
    return found_skills

def calculate_similarity_score(resume_skills, job_skills):
    """Calculate similarity between resume skills and job skills"""
    if not resume_skills or not job_skills:
        return 0.0
    
    # Convert to lowercase for comparison
    resume_skills_lower = [skill.lower().strip() for skill in resume_skills]
    job_skills_lower = [skill.lower().strip() for skill in job_skills]
    
    # Method 1: Simple overlap ratio
    matching_skills = set(resume_skills_lower) & set(job_skills_lower)
    overlap_score = len(matching_skills) / len(set(job_skills_lower)) if job_skills_lower else 0
    
    # Method 2: TF-IDF cosine similarity for more sophisticated matching
    try:
        all_skills = list(set(resume_skills_lower + job_skills_lower))
        if len(all_skills) < 2:
            return overlap_score * 100
        
        resume_text = ' '.join(resume_skills_lower)
        job_text = ' '.join(job_skills_lower)
        
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        # Combine both methods (weighted average)
        final_score = (overlap_score * 0.7 + cosine_sim * 0.3) * 100
        return min(final_score, 100.0)  # Cap at 100%
        
    except Exception as e:
        print(f"Error in similarity calculation: {e}")
        return overlap_score * 100

def clean_skill_list(skills):
    return [skill.replace(" ", "").strip() for skill in skills if skill.strip()]

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    """Handle resume upload and extract skills"""
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Extract text and skills from resume
        resume_text = extract_resume_text(file_path)
        resume_skills = extract_skills_from_resume(resume_text)
        
        # Store in session
        session['resume_skills'] = resume_skills
        session['resume_uploaded'] = True
        
        # Clean up uploaded file
        os.remove(file_path)
        
        return jsonify({
            'success': True,
            'skills': resume_skills,
            'message': f'Resume processed successfully! Found {len(resume_skills)} skills.'
        })
    
    return jsonify({'error': 'Invalid file type. Please upload PDF, DOCX, or TXT files.'}), 400

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
        resume_skills = session.get('resume_skills', [])

        for row in reader:
            # Parse and clean skills
            if 'skills' in row and row['skills']:
                try:
                    parsed_skills = ast.literal_eval(row['skills'])
                    row['skills'] = clean_skill_list(parsed_skills)
                except Exception:
                    row['skills'] = []
            else:
                row['skills'] = []

            # Calculate similarity score if resume is uploaded
            if resume_skills and row['skills']:
                row['similarity_score'] = round(calculate_similarity_score(resume_skills, row['skills']), 1)
                # Extract matching skills
                resume_skills_lower = [skill.lower() for skill in resume_skills]
                job_skills_lower = [skill.lower() for skill in row['skills']]
                row['matching_skills'] = [skill for skill in row['skills'] if skill.lower() in resume_skills_lower]
            else:
                row['similarity_score'] = None
                row['matching_skills'] = []

            # Parse and format date
            try:
                posted_date = datetime.strptime(row['posted_at'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                posted_date = datetime.strptime(row['posted_at'], '%Y-%m-%d')

            row['posted_at'] = posted_date
            row['posted_ago'] = f"{(datetime.today() - posted_date).days} days ago"

            jobs.append(row)

        # Sort jobs by similarity score if resume uploaded, otherwise by date
        if resume_skills:
            jobs = sorted(jobs, key=lambda x: x['similarity_score'] if x['similarity_score'] is not None else 0, reverse=True)
        else:
            jobs = sorted(jobs, key=lambda x: x['posted_at'], reverse=True)

        # Pagination
        page = int(request.args.get('page', 1))
        per_page = 20
        start = (page - 1) * per_page
        end = start + per_page
        paginated_jobs = jobs[start:end]
        has_next = end < len(jobs)

        return render_template('index.html', 
                             jobs=paginated_jobs, 
                             page=page, 
                             has_next=has_next,
                             resume_uploaded=session.get('resume_uploaded', False),
                             resume_skills=resume_skills)

    except Exception as e:
        return f"Error fetching jobs: {str(e)}"

@app.route('/clear_resume')
def clear_resume():
    """Clear uploaded resume from session"""
    session.pop('resume_skills', None)
    session.pop('resume_uploaded', None)
    return jsonify({'success': True, 'message': 'Resume cleared successfully'})

if __name__ == '__main__':
    app.run( debug=True)