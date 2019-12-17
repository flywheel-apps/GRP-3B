#flywheel/csv-import

# Start with python 3.7
FROM python:3.7 as base
MAINTAINER Flywheel <support@flywheel.io>

# Install pandas
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# Flywheel spec (v0)
WORKDIR /flywheel/v0

# Copy executables into place
COPY dicom_processor.py .
RUN chmod +x dicom_processor.py
COPY common_utils.py .
RUN chmod +x common_utils.py
COPY MR_classifier.py .
RUN chmod +x MR_classifier.py
COPY CT_classifier.py .
RUN chmod +x CT_classifier.py
COPY run.py ./run.py
RUN chmod +x ./run.py
COPY manifest.json .

# Add a default ENTRYPOINT
ENTRYPOINT ["/flywheel/v0/run.py"]
