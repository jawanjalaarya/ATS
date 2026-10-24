FROM python:3.12-slim

# Create non-root user for security (UID/GID 1000)
RUN groupadd -r -g 1000 app && useradd -r -u 1000 -g app app

# Set working directory
WORKDIR /app

# Install Python dependencies first (layer caching optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

# Copy application source code
COPY . .

# Create persistent data directory (including resumes) and set ownership
RUN mkdir -p /app/data/resumes && chown -R app:app /app

# Make entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Expose application port
EXPOSE 8000

# Switch to non-root user
USER app

# Entrypoint runs migrations then starts server
ENTRYPOINT ["/app/docker-entrypoint.sh"]
