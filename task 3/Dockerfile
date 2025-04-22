# Pinned slim Python base image
FROM python:3.9-slim-bullseye

# Set the working dir inside the container
WORKDIR /app

# Copy dependency configuration
COPY ./requirements.txt /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the operator files into the container
COPY ./operator /app/operator

# Add a non-root user for security purpose
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

# Run the operator with kopf
CMD ["kopf", "run", "--verbose", "/app/operator/rds_operator.py"]
