#
# This file is used to build the Docker image of the application
#
# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Create required directories
RUN mkdir -p /opt/modules && \
    mkdir -p /tmp/bold-public-portal/cache

# Create modules directory and add modules
WORKDIR /opt/modules/barcode-core-data-model
ADD https://us-east-1.linodeobjects.com/bold-reference-files-public/field_definitions.tsv /opt/modules/barcode-core-data-model/
ADD https://us-east-1.linodeobjects.com/bold-reference-files-public/mapping_BCDM_to_DWC.tsv /opt/modules/barcode-core-data-model/

# Set the working directory in the container
WORKDIR /app

# Install any needed dependencies specified in requirements.txt
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY src /app

# Expose the application port
EXPOSE 8000

# Run uvicorn when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
