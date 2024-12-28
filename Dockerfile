# FROM registry.access.redhat.com/ubi8/ubi:latest
FROM rockylinux:8

# Set environment variables
ENV AIRFLOW_HOME=/root/airflow
ENV AIRFLOW_DAGS_FOLDER=/root/airflow/dags
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8

# Accept build arguments for pip configuration
ARG GLOBAL_CERT
ARG GLOBAL_INDEX
ARG GLOBAL_INDEX_URL

# Install system dependencies
RUN dnf update -y && \
    dnf module enable -y postgresql:13 && \
    dnf module reset -y python36 && \
    dnf module enable -y python39 && \
    dnf install -y \
        bash \
        python3.11 \
        python3-pip \
        python3-devel \
        git \
        wget \
        postgresql-server \
        postgresql-libs \
        postgresql && \
    dnf clean all

# Set Python 3.11 as default and ensure pip is installed
RUN alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    alternatives --set python3 /usr/bin/python3.11 && \
    python3 -m ensurepip && \
    python3 -m pip install --no-cache-dir --upgrade pip

# Configure self-signed certificate for pip
RUN echo -e "[global]\ncert = ${GLOBAL_CERT}\nindex-url = ${GLOBAL_INDEX_URL}" > /etc/pip.conf

# Install Python dependencies
RUN python3 -m pip install --no-cache-dir \
    apache-airflow[postgres] \
    psycopg2-binary \
    gitpython
RUN pip3 install --no-cache-dir \
    apache-airflow-providers-postgres \
    psycopg2-binary \
    requests \
    pandas \
    numpy \
    lizard \
    checkov \
    sqlalchemy

# Initialize PostgreSQL database
USER postgres
RUN initdb -D /var/lib/pgsql/data || echo "Database already initialized"
RUN echo "host all all 0.0.0.0/0 md5" >> /var/lib/pgsql/data/pg_hba.conf && \
    echo "listen_addresses='*'" >> /var/lib/pgsql/data/postgresql.conf
USER root

# Prepare directories
RUN mkdir -p /mnt/cloned_repositories
RUN mkdir -p /root/.syft
RUN mkdir -p /root/.grype
RUN mkdir -p /root/.cache/trivy

# airflow config
COPY ./dags ${AIRFLOW_DAGS_FOLDER}
COPY ./modular ${AIRFLOW_DAGS_FOLDER}/modular
COPY ./airflow.cfg ${AIRFLOW_HOME}/airflow.cfg

# go-enry
COPY ./tools/go-enry/go-enry /usr/local/bin/go-enry

# cloc
COPY ./tools/cloc/cloc /usr/local/bin/cloc

# grype
COPY ./tools/grype/grype /usr/local/bin/grype
COPY ./tools/grype/config.yaml /root/.grype/
COPY ./tools/grype/listing.json /root/.grype/
COPY ./tools/grype/db /root/.cache/grype/

# syft
COPY ./tools/syft/syft /usr/local/bin/syft
COPY ./tools/syft/config.yaml /root/.syft/

# trivy
COPY ./tools/trivy/trivy /usr/local/bin/trivy
COPY ./tools/trivy/db /root/.cache/trivy

# Add and make start_services.sh executable
COPY ./tools/start_services.sh /usr/local/bin/start_services.sh
RUN chmod +x /usr/local/bin/start_services.sh

# Make binaries and scripts executable
RUN chmod +x /usr/local/bin/*

# Configure working directory and expose ports
WORKDIR ${AIRFLOW_HOME}
EXPOSE 8088 5432

# Use the script to start PostgreSQL and Airflow
CMD ["/usr/local/bin/start_services.sh"]

# Set entrypoint for CLI access
ENTRYPOINT ["/bin/bash"]
