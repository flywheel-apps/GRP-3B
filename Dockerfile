#flywheel/csv-import

# Start with python 3.7
FROM python:3.7 as base
MAINTAINER Flywheel <support@flywheel.io>

# Install pandas
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# Flywheel spec (v0)
WORKDIR /flywheel/v0

# Make a target for testing locally
FROM base as testing
COPY tests ./tests
RUN pip install -r tests/requirements.txt

# Copy executables into place
COPY classification_from_label.py .
RUN chmod +x classification_from_label.py
COPY run.py ./run.py
RUN chmod +x ./run.py
COPY manifest.json .

# Add a default ENTRYPOINT
ENTRYPOINT ["/flywheel/v0/run.py"]
