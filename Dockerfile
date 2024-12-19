FROM registry.access.redhat.com/ubi8/ubi:latest

# Set environment variables
ENV AIRFLOW_HOME=/usr/local/airflow
ENV AIRFLOW_DAGS_FOLDER=/usr/local/airflow/dags
ENV global.cert=/etc/pip/certs/self-signed-cert.pem
ENV global.index=https://pypi.org/simple
ENV global.index-url=https://pypi.org/simple
ENV http_proxy=${HTTP_PROXY}
ENV https_proxy=${HTTPS_PROXY}


# Copy self-signed certificate into the image
COPY self-signed-cert.pem /etc/pip/certs/self-signed-cert.pem

# Install system dependencies
RUN dnf update -y && \
    dnf install -y \
        python3 \
        python3-pip \
        python3-devel \
        git \
        wget \
        postgresql-server \
        postgresql && \
    dnf module enable -y go-toolset && \
    dnf install -y go-toolset && \
    dnf clean all

# Configure self-signed certificate for pip
RUN echo -e "[global]\ncert = /etc/pip/certs/self-signed-cert.pem\nindex-url = https://pypi.org/simple" > /etc/pip.conf


# Upgrade pip and install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir \
        apache-airflow \
        gitpython

# Install Airflow provider and other Python dependencies
RUN pip3 install --no-cache-dir \
    apache-airflow-providers-postgres \
    psycopg2-binary \
    requests \
    pandas \
    numpy \
    sqlalchemy

# Create Airflow home and dags directory
RUN mkdir -p ${AIRFLOW_DAGS_FOLDER}

# Copy DAG files from local filesystem to the container
COPY ./dags ${AIRFLOW_DAGS_FOLDER}

# Initialize and start PostgreSQL and Airflow
RUN initdb -D /var/lib/pgsql/data && \
    echo "host all  all    0.0.0.0/0  md5" >> /var/lib/pgsql/data/pg_hba.conf && \
    echo "listen_addresses='*'" >> /var/lib/pgsql/data/postgresql.conf

# Start PostgreSQL and Airflow
CMD bash -c "service postgresql-13 start && airflow db init && airflow webserver & airflow scheduler"

# Create Airflow home directory
RUN mkdir -p ${AIRFLOW_HOME}

WORKDIR ${AIRFLOW_HOME}

# Expose port for Airflow Webserver
EXPOSE 8088

# Set entrypoint for CLI access
ENTRYPOINT ["/bin/bash"]
