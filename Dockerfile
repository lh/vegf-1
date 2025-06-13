# APE Application Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
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
RUN mkdir -p simulation_results protocols/v2/temp

# Create non-root user for security
RUN useradd -m -u 1000 apeuser && \
    chown -R apeuser:apeuser /app

# Switch to non-root user
USER apeuser

# Expose Streamlit default port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Run the application
CMD ["streamlit", "run", "APE.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0"]