from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace 
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers import CommaSeparatedListOutputParser
import boto3
import os
from langchain_core.prompts import PromptTemplate
import pandas as pd

#model = HuggingFaceEndpoint(model='google/flan-t5-small',task='Summerization',max_new_tokens=1000)
llm = HuggingFaceEndpoint(
    repo_id="microsoft/Phi-3-mini-4k-instruct",
    task="text-generation",
    max_new_tokens=512,
    do_sample=False,
    repetition_penalty=1.03,
)

chat = ChatHuggingFace(llm=llm, verbose=True)
parser = CommaSeparatedListOutputParser()

s3_client= boto3.client('s3')
response = s3_client.get_object(Key = 'linkedin_jobs_raw.csv', Bucket='freshjoblanding')
df= pd.read_csv(response['Body'], header = 0 )

aws_region = os.getenv('AWS_REGION')
aws_endpoint = os.getenv('aws_endpoint')
aws_access_key_id = os.getenv('aws_access_key')
aws_secret_access_key = os.getenv('aws_secret_access_key')

s3 = boto3.client('s3',region_name=aws_region,
                       aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
bucket = 'freshjoblanding'
key = 'enriched_linkedin_jobs.csv'





prompt_template = PromptTemplate.from_template(
    ('You need to extract top 10 required skills form the job description. list top 10 skills for the job discription {topic}  note: only give output as skills as word'
    ' just the list, do not assume education as skill ' \
    'output example as below python, sql ,container ,AWS , snowflake   strip anything after the skill' \
    'strip undesa'
    ),
    format_instructions=parser.get_format_instructions()
)

#prompt = prompt_template.invoke({"topic":" Tire Rack is embarking on a modernization journey, evolving from a legacy data environment to a scalable, cloud-native data ecosystem. We are a forward-thinking, data-driven organization committed to leveraging modern architecture and engineering practices to deliver innovative solutions across the e-Commerce sector. Join us at a pivotal time as we transform how data powers our decisions, products, and services. We are seeking a Data Engineer to help drive our digital transformation. In this role, you’ll play a key part in re-architecting legacy systems, building cloud-first data pipelines, and modernizing how we collect, store, and deliver data across the company. This is a hands-on, impact-driven opportunity to shape scalable solutions from the ground up and enable analytics and intelligence in a rapidly evolving environment. You’ll work closely with engineers, analysts, and stakeholders to build the foundation for next-generation data platforms.Required QualificationsBachelor’s or Master’s degree in Computer Science, Engineering, or a related field or the equivalent through a combination of education and related work experience.3 years minimum related work experience.Strong understanding of data modeling, schema design, ETL/ELT, and data warehousing concepts.Proficient in SQL and scripting/programming languages such as Python, Java, or Scala.Experience with relational and non-relational databases (e.g., PostgreSQL, DB2, NoSQL).Knowledge of cloud-based data platforms such as AWS, GCP, or Azure.Familiarity with CI/CD, Git, containerization " })
#response = chat.invoke(prompt)
#skills = parser.parse(response.content)




 
def extract_skills(target:str) -> list:
    
     for i in target:
             prompt = prompt_template.invoke({"topic":i})
             response = chat.invoke(prompt)
             skills = parser.parse(response.content)
             return skills



df['skills'] = df['description'].apply(lambda x: extract_skills(x))

print(df['skills'].head(5))

df.to_csv("skills_linked_job.csv",header=1)

s3_client.upload_file("skills_linked_job.csv", "freshjoblanding" , Key= "skills_linkedin_jobs.csv")

