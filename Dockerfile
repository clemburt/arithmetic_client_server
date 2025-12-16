# Use official Python 3.12 Alpine base image for small size and latest Python version
FROM python:3.12-alpine

# Set the working directory inside the container
WORKDIR /app

# Install system build dependencies required for installing packages
RUN apk add --no-cache build-base gcc libffi-dev musl-dev curl jq

# Install PDM (Python Development Master) globally
RUN pip install pdm

# Copy the full project into the container
COPY . /app

# Install only production dependencies
RUN pdm install --prod

# Set environment variables for module resolution and virtual environment
ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

# Default command (can be overridden by docker run args)
CMD ["sekoia", "--help"]