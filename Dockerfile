FROM registry.access.redhat.com/ubi8/ubi:latest

# Set environment variables
ENV AIRFLOW_HOME=/usr/local/airflow
ENV AIRFLOW_DAGS_FOLDER=/usr/local/airflow/dags
ENV global.cert=/etc/pip/certs/self-signed-cert.pem
ENV global.index=https://pypi.org/simple
ENV global.index-url=https://pypi.org/simple
ENV http_proxy=${HTTP_PROXY}
ENV https_proxy=${HTTPS_PROXY}

ENV AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="postgresql+psycopg2://postgres:postgres@localhost:5432/airflow"

# Copy self-signed certificate into the image
COPY self-signed-cert.pem /etc/pip/certs/self-signed-cert.pem

# Install system dependencies
RUN dnf update -y && \
    dnf module enable -y postgresql:13 && \
    dnf module reset -y python36 && \
    dnf module enable -y python39 && \
    dnf install -y \
        python3.11 \
        python3-pip \
        python3-devel \
        git \
        wget \
        postgresql-server \
        postgresql && \
    dnf clean all

# Configure self-signed certificate for pip
RUN echo -e "[global]\ncert = /etc/pip/certs/self-signed-cert.pem\nindex-url = https://pypi.org/simple" > /etc/pip.conf

# Ensure pip is installed and upgraded for Python 3.11
RUN python3.11 -m ensurepip && \
    python3.11 -m pip install --upgrade pip && \
    rm -f /usr/bin/pip3 && \
    ln -s /usr/local/bin/pip3 /usr/bin/pip3

# Set Python 3.11 as default
RUN alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    alternatives --set python3 /usr/bin/python3.11 && \
    python3 --version

# Upgrade pip and install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir \
        apache-airflow \
        gitpython

# Generate airflow.cfg
RUN airflow db init

# Configure Airflow for parallelism
RUN sed -i 's/^executor = SequentialExecutor/executor = LocalExecutor/' ${AIRFLOW_HOME}/airflow.cfg && \
    sed -i 's/^parallelism = .*/parallelism = 16/' ${AIRFLOW_HOME}/airflow.cfg && \
    sed -i 's/^dag_concurrency = .*/dag_concurrency = 8/' ${AIRFLOW_HOME}/airflow.cfg && \
    sed -i 's/^worker_concurrency = .*/worker_concurrency = 8/' ${AIRFLOW_HOME}/airflow.cfg

# Install Airflow provider and other Python dependencies
RUN pip3 install --no-cache-dir \
    apache-airflow-providers-postgres \
    psycopg2-binary \
    requests \
    pandas \
    numpy \
    sqlalchemy

# Initialize PostgreSQL database
USER postgres
RUN initdb -D /var/lib/pgsql/data || echo "Database already initialized"

# Configure PostgreSQL
RUN echo "host all all 0.0.0.0/0 md5" >> /var/lib/pgsql/data/pg_hba.conf && \
    echo "listen_addresses='*'" >> /var/lib/pgsql/data/postgresql.conf

# Switch back to root to copy DAGs and set permissions
USER root
RUN mkdir -p ${AIRFLOW_DAGS_FOLDER} && \
    chown -R postgres:postgres ${AIRFLOW_DAGS_FOLDER}
COPY ./dags ${AIRFLOW_DAGS_FOLDER}

# Script to start both services
COPY start_services.sh /usr/local/bin/start_services.sh
RUN chmod +x /usr/local/bin/start_services.sh

# Use the script to start PostgreSQL and Airflow
CMD ["/usr/local/bin/start_services.sh"]

WORKDIR ${AIRFLOW_HOME}
EXPOSE 8088 5432

# Set entrypoint for CLI access
ENTRYPOINT ["/bin/bash"]
