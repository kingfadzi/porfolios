# FROM registry.access.redhat.com/ubi8/ubi:latest
FROM almalinux:8

# Set environment variables
ENV AIRFLOW_HOME=/home/airflow/airflow
ENV AIRFLOW_DAGS_FOLDER=/home/airflow/airflow/dags
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8

# Accept build arguments for pip configuration and user IDs
ARG GLOBAL_CERT
ARG GLOBAL_INDEX
ARG GLOBAL_INDEX_URL
ARG HOST_UID=1000
ARG HOST_GID=1000

# Install system dependencies
RUN dnf update -y && \
    dnf module enable -y python39 && \
    dnf install -y \
        bash \
        nc \
        python3.11 \
        python3-pip \
        python3-devel \
        git \
        wget \
        postgresql-devel && \
    dnf clean all

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

# Configure pip with dynamic settings
RUN if [ -n "$GLOBAL_CERT" ]; then \
      echo -e "[global]\ncert = ${GLOBAL_CERT}\nindex-url = ${GLOBAL_INDEX_URL}" > /etc/pip.conf; \
    else \
      echo -e "[global]\nindex-url = ${GLOBAL_INDEX_URL}" > /etc/pip.conf; \
    fi

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


# Create a group and user with specified UID and GID
RUN groupadd -g ${HOST_GID} airflow && \
    useradd -m -u ${HOST_UID} -g airflow airflow

# Set ownership for Airflow directories
RUN mkdir -p $AIRFLOW_HOME && \
    mkdir -p /mnt/cloned_repositories && \
    mkdir -p /home/airflow/.syft && \
    mkdir -p /home/airflow/.grype && \
    mkdir -p /home/airflow/.cache/trivy && \
    chown -R airflow:airflow /home/airflow && \
    chown -R airflow:airflow /mnt/cloned_repositories

# Configure pip with dynamic settings
RUN mkdir -p /home/airflow/.pip && \
    if [ -n "$GLOBAL_CERT" ]; then \
      echo -e "[global]\ncert = ${GLOBAL_CERT}\nindex-url = ${GLOBAL_INDEX_URL}" > /home/airflow/.pip/pip.conf; \
    else \
      echo -e "[global]\nindex-url = ${GLOBAL_INDEX_URL}" > /home/airflow/.pip/pip.conf; \
    fi

# Install Python dependencies
RUN pip3 install --no-cache-dir \
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

# Airflow config
COPY --chown=airflow:airflow ./dags $AIRFLOW_DAGS_FOLDER
COPY --chown=airflow:airflow ./modular $AIRFLOW_DAGS_FOLDER/modular
COPY --chown=airflow:airflow ./airflow.cfg $AIRFLOW_HOME/airflow.cfg

# go-enry
COPY --chown=airflow:airflow ./tools/go-enry/go-enry /usr/local/bin/go-enry

# cloc
COPY --chown=airflow:airflow ./tools/cloc/cloc /usr/local/bin/cloc

# grype
COPY --chown=airflow:airflow ./tools/grype/grype /usr/local/bin/grype
COPY --chown=airflow:airflow ./tools/grype/config.yaml /home/airflow/.grype/
COPY --chown=airflow:airflow ./tools/grype/listing.json /home/airflow/.grype/
COPY --chown=airflow:airflow ./tools/grype/db /home/airflow/.cache/grype/

# syft
COPY --chown=airflow:airflow ./tools/syft/syft /usr/local/bin/syft
COPY --chown=airflow:airflow ./tools/syft/config.yaml /home/airflow/.syft/

# trivy
COPY --chown=airflow:airflow ./tools/trivy/trivy /usr/local/bin/trivy
COPY --chown=airflow:airflow ./tools/trivy/db /home/airflow/.cache/trivy/db

# Add and make start_services.sh executable
COPY --chown=airflow:airflow ./tools/start_services.sh /usr/local/bin/start_services.sh
RUN chmod +x /usr/local/bin/start_services.sh

# Make binaries and scripts executable
RUN chmod +x /usr/local/bin/*

# Switch to the airflow user
USER airflow

# Configure working directory and expose ports
WORKDIR $AIRFLOW_HOME
EXPOSE 8088

# Set ENTRYPOINT to start_services.sh
ENTRYPOINT ["/usr/local/bin/start_services.sh"]
