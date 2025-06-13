# APE Deployment Guide

This guide covers how to deploy the APE (AMD Protocol Explorer) application.

## Quick Start

### Local Development
```bash
# Install all dependencies (including dev tools)
pip install -r requirements-dev.txt

# Run the application
streamlit run APE.py
```

### Production Deployment
```bash
# Install production dependencies only
pip install -r requirements.txt

# Run with production settings
streamlit run APE.py \
  --server.port 80 \
  --server.maxUploadSize 1000 \
  --server.enableCORS false \
  --server.enableXsrfProtection true
```

## Directory Structure

### Production Files (Include in deployment)
```
├── APE.py                    # Main application entry
├── pages/                    # Streamlit pages
│   ├── 1_Protocol_Manager.py
│   ├── 2_Simulations.py
│   └── 3_Analysis.py
├── ape/                      # Core application modules
│   ├── components/
│   ├── core/
│   ├── utils/
│   └── visualizations/
├── assets/                   # Static assets (logos, etc.)
├── protocols/                # Protocol YAML files
├── simulation_results/       # Results storage
├── visualization/            # Central styling system
├── simulation_v2/            # V2 simulation engine
├── .streamlit/               # Streamlit configuration
├── requirements.txt          # Production dependencies
└── README.md                # User documentation
```

### Development Files (Exclude from deployment)
```
├── dev/                     # All development tools
├── tests*/                  # Test suites
├── scripts*/                # Dev scripts
├── literature_extraction/   # Research tools
├── archive/                 # Old implementations
├── meta/                    # Project documentation
├── docs/                    # Technical docs
├── requirements-dev.txt     # Dev dependencies
├── CLAUDE*.md              # AI instructions
├── *.log                   # Log files
├── __pycache__/            # Python cache
└── .git/                   # Version control
```

## Docker Deployment

### Dockerfile
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY APE.py .
COPY pages/ ./pages/
COPY ape/ ./ape/
COPY assets/ ./assets/
COPY protocols/ ./protocols/
COPY visualization/ ./visualization/
COPY simulation_v2/ ./simulation_v2/
COPY .streamlit/ ./.streamlit/

# Create directories for runtime
RUN mkdir -p simulation_results

# Expose Streamlit port
EXPOSE 8501

# Run the application
CMD ["streamlit", "run", "APE.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=true"]
```

### Build and Run
```bash
# Build the Docker image
docker build -t ape-app .

# Run the container
docker run -p 8501:8501 \
  -v $(pwd)/simulation_results:/app/simulation_results \
  ape-app
```

## Cloud Deployment

### Streamlit Cloud
1. Push code to GitHub (excluding dev files via .gitignore)
2. Connect repository to Streamlit Cloud
3. Set Python version: 3.11
4. Deploy with requirements.txt

### AWS/GCP/Azure
Use the Docker container with your cloud provider's container service:
- AWS: ECS or App Runner
- GCP: Cloud Run
- Azure: Container Instances

### Environment Variables
Set these for production:
```bash
STREAMLIT_SERVER_PORT=80
STREAMLIT_SERVER_ENABLE_CORS=false
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true
STREAMLIT_SERVER_MAX_UPLOAD_SIZE=1000
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

## Security Considerations

1. **File Upload Limits**: Set appropriate limits for protocol file uploads
2. **Resource Limits**: Configure memory and CPU limits for simulations
3. **Authentication**: Add authentication layer if needed (e.g., using streamlit-authenticator)
4. **HTTPS**: Always use HTTPS in production
5. **Secrets**: Never commit secrets; use environment variables

## Performance Optimization

1. **Caching**: Streamlit's built-in caching is configured for key functions
2. **Memory**: Monitor memory usage, especially for large simulations
3. **Storage**: Implement cleanup for old simulation results
4. **CDN**: Serve static assets through CDN if needed

## Monitoring

1. **Health Check**: `/healthz` endpoint (configure in load balancer)
2. **Logs**: Application logs to stdout/stderr
3. **Metrics**: Monitor CPU, memory, and response times
4. **Alerts**: Set up alerts for errors and resource usage

## Backup and Recovery

1. **Simulation Results**: Regular backups of simulation_results/
2. **Protocols**: Version control for protocol files
3. **Database**: If using external storage, implement backup strategy

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed
   - Check Python version (3.11+ required)

2. **Memory Issues**
   - Increase container memory limits
   - Implement result pagination

3. **File Upload Issues**
   - Check file size limits
   - Verify write permissions on protocols/v2/temp/

### Debug Mode
Run with debug logging:
```bash
streamlit run APE.py --logger.level=debug
```

## Updates and Maintenance

1. **Zero-Downtime Updates**: Use rolling deployments
2. **Version Tags**: Tag Docker images with version numbers
3. **Rollback Plan**: Keep previous version available
4. **Testing**: Run tests before deployment

## Support

For issues or questions:
1. Check application logs
2. Review this deployment guide
3. Consult technical documentation in docs/
4. Submit issues to the repository