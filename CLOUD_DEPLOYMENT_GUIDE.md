# Cloud Deployment Guide for APE Streamlit App

## Overview

This guide explains how to deploy the APE Streamlit application to various cloud platforms while maintaining the project structure where Streamlit is a subdirectory of a larger project.

## Project Structure

```
/project-root/
├── simulation/          # Core simulation modules
├── protocols/          # Protocol definitions
├── streamlit_app_parquet/  # Streamlit application
│   ├── app.py
│   ├── pages/
│   ├── utils/
│   └── output/
└── README.md
```

## Deployment Options

### 1. Streamlit Cloud (Recommended for Streamlit apps)

**Requirements:**
- GitHub repository
- `requirements.txt` in the root or app directory

**Steps:**
1. Create `.streamlit/config.toml` in your repo root:
   ```toml
   [server]
   headless = true
   port = 8501

   [deploy]
   mainModule = "streamlit_app_parquet/app.py"
   ```

2. Create `requirements.txt` at the root with all dependencies

3. In Streamlit Cloud dashboard:
   - Connect your GitHub repo
   - Set "Main file path" to `streamlit_app_parquet/app.py`
   - Deploy

### 2. Heroku

**Requirements:**
- Heroku CLI installed
- `Procfile` at root
- `requirements.txt`

**Steps:**
1. Create `Procfile` at root:
   ```
   web: sh -c 'cd "$PWD" && streamlit run streamlit_app_parquet/app.py --server.port $PORT'
   ```

2. Create `runtime.txt`:
   ```
   python-3.12.0
   ```

3. Deploy:
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

### 3. Google Cloud Run

**Requirements:**
- Docker
- Google Cloud SDK

**Steps:**
1. Create `Dockerfile` at root:
   ```dockerfile
   FROM python:3.12-slim

   WORKDIR /app

   # Copy entire project
   COPY . .

   # Install dependencies
   RUN pip install -r requirements.txt

   EXPOSE 8080

   # Run from project root
   CMD streamlit run streamlit_app_parquet/app.py \
       --server.port 8080 \
       --server.address 0.0.0.0
   ```

2. Build and deploy:
   ```bash
   gcloud run deploy ape-streamlit \
     --source . \
     --region us-central1 \
     --allow-unauthenticated
   ```

### 4. AWS Elastic Beanstalk

**Requirements:**
- EB CLI
- `.ebextensions/` directory

**Steps:**
1. Create `.ebextensions/python.config`:
   ```yaml
   option_settings:
     aws:elasticbeanstalk:container:python:
       WSGIPath: streamlit_app_parquet/app.py
     aws:elasticbeanstalk:application:environment:
       STREAMLIT_SERVER_PORT: 8501
   ```

2. Create `Procfile`:
   ```
   web: streamlit run streamlit_app_parquet/app.py --server.port 8501
   ```

3. Deploy:
   ```bash
   eb init -p python-3.12 ape-app
   eb create ape-env
   eb deploy
   ```

## Environment Variables

For all deployments, you may need to set:

```bash
# If your app needs to know it's in production
STREAMLIT_ENV=production

# For path resolution
PROJECT_ROOT=/app  # or wherever your code is deployed

# For data persistence (if using cloud storage)
DATA_BUCKET=your-bucket-name
```

## Data Persistence

Since Parquet files are generated during runtime:

### Option 1: Cloud Storage
- Use S3, GCS, or Azure Blob Storage
- Modify `utils/paths.py` to support cloud paths
- Example for S3:
  ```python
  import boto3
  
  def get_parquet_results_dir():
      if os.environ.get('STREAMLIT_ENV') == 'production':
          return f"s3://{os.environ['DATA_BUCKET']}/parquet_results"
      return local_path
  ```

### Option 2: Database
- Store results in PostgreSQL/MySQL
- Use SQLAlchemy for abstraction

### Option 3: Temporary Storage
- Accept that data is ephemeral
- Good for demos/POCs

## Path Resolution

The `utils/paths.py` module handles path resolution across environments:

```python
# Works locally and in cloud
from utils.paths import get_parquet_results_dir

parquet_dir = get_parquet_results_dir()
```

## Testing Deployment Locally

Before deploying, test with Docker:

```bash
# Build
docker build -t ape-streamlit .

# Run
docker run -p 8501:8501 ape-streamlit

# Test
open http://localhost:8501
```

## Common Issues

### 1. Module Import Errors
**Solution:** Ensure `sys.path` includes project root:
```python
import sys
sys.path.append('/app')  # or appropriate path
```

### 2. Missing Simulation Module
**Solution:** Either:
- Deploy entire project (recommended)
- Refactor to make Streamlit standalone

### 3. File Permissions
**Solution:** Ensure output directories are writable:
```python
os.makedirs(output_dir, exist_ok=True, mode=0o755)
```

## Recommendations

1. **For Production:** Use Streamlit Cloud or Google Cloud Run
2. **For Internal Tools:** Use Heroku or AWS EB
3. **For Development:** Use Docker locally
4. **Data Storage:** Always use cloud storage for production

## Security Considerations

1. Never commit sensitive data or API keys
2. Use environment variables for configuration
3. Implement authentication if needed:
   ```python
   # In app.py
   if os.environ.get('REQUIRE_AUTH'):
       check_password()
   ```

4. Use HTTPS in production (most platforms handle this)

## Monitoring

Add logging for production:

```python
import logging

# Configure based on environment
if os.environ.get('STREAMLIT_ENV') == 'production':
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

1. Choose your deployment platform
2. Set up CI/CD with GitHub Actions
3. Configure monitoring and alerts
4. Set up data persistence strategy