#flywheel/csv-import

# Start with python 3.7
FROM python:3.7-slim-stretch as base
MAINTAINER Flywheel <support@flywheel.io>

# Install pandas
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# Flywheel spec (v0)
WORKDIR /flywheel/v0

# Copy executables into place
COPY run.py \
     PT_classifier.py \
     OPHTHA_classifier.py \
     MR_classifier.py \
     dicom_processor.py \
     common_utils.py \
     CT_classifier.py /flywheel/v0/
RUN chmod +x ./run.py
COPY manifest.json .

# Add a default ENTRYPOINT
ENTRYPOINT ["/flywheel/v0/run.py"]
