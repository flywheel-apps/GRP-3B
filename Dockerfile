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
COPY classification_from_label.py .
RUN chmod +x classification_from_label.py
COPY classify_CT.py .
RUN chmod +x classify_CT.py
COPY run.py ./run.py
RUN chmod +x ./run.py
COPY manifest.json .

# Add a default ENTRYPOINT
ENTRYPOINT ["/flywheel/v0/run.py"]
