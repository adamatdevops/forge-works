FROM apache/airflow:3.1.8

USER root
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

USER airflow

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Bake DAGs into image so KubernetesExecutor task pods have them
COPY --chown=airflow:root dags/ /opt/airflow/dags/
