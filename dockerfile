FROM python:3.8-slim-buster as prod

# Create app directory and set working directory
WORKDIR /app
RUN mkdir files

# Install dependencies
COPY ./src/requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY ./src/ /app/

# Set environment variables
ENV DB_PATH=/app/files/example_db.db \
    FLASK_APP=example_API.py \
    FLASK_ENV=production \
    PORT=5005

# Expose port
EXPOSE ${PORT}

# Run Flask app
CMD flask run --host=0.0.0.0 --port=${PORT}
