FROM apache/airflow:2.9.1-python3.11

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

USER airflow

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

COPY src/ /opt/airflow/src/
COPY great_expectations/ /opt/airflow/great_expectations/
COPY dags/ /opt/airflow/dags/

ENV PYTHONPATH=/opt/airflow
