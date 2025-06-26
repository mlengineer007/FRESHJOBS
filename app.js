const express = require('express');
const AWS = require('aws-sdk');
const csv = require('csv-parser');
const dotenv = require('dotenv');
const path = require('path');

dotenv.config();

const app = express();
app.set('view engine', 'ejs');
app.use(express.static('public'));

const s3 = new AWS.S3({
  region: process.env.AWS_REGION,
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
});

function parseCSVFromS3(bucket, key) {
  return new Promise((resolve, reject) => {
    const results = [];
    const params = { Bucket: bucket, Key: key };
    s3.getObject(params)
      .createReadStream()
      .pipe(csv())
      .on('data', (data) => {
        try {
          const postedAt = new Date(data.posted_at);
          data.posted_at = postedAt;
          const daysAgo = Math.floor((Date.now() - postedAt) / (1000 * 60 * 60 * 24));
          data.posted_ago = `${daysAgo} days ago`;
          results.push(data);
        } catch (err) {
          console.error("Date error:", err);
        }
      })
      .on('end', () => {
        results.sort((a, b) => new Date(b.posted_at) - new Date(a.posted_at));
        resolve(results);
      })
      .on('error', reject);
  });
}

app.get('/', async (req, res) => {
  const page = parseInt(req.query.page || 1);
  const perPage = 20;

  try {
    const jobs = await parseCSVFromS3(process.env.S3_BUCKET_NAME, process.env.S3_KEY);
    const paginatedJobs = jobs.slice((page - 1) * perPage, page * perPage);
    const hasNext = page * perPage < jobs.length;

    res.render('index', { jobs: paginatedJobs, page, hasNext });
  } catch (err) {
    console.error(err);
    res.status(500).send("Error loading jobs");
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
