FROM registry.access.redhat.com/ubi8/ubi:latest

# Set environment variables
ENV AIRFLOW_HOME=/usr/local/airflow

# Install system dependencies and PostgreSQL
RUN yum update -y && \
    yum install -y \
        python3 \
        python3-pip \
        python3-devel \
        postgresql \
        postgresql-server \
        git \
        wget && \
    yum module enable -y go-toolset && \
    yum install -y go-toolset && \
    yum clean all

# Upgrade pip and install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir \
        apache-airflow \
        gitpython

# Create Airflow home directory
RUN mkdir -p ${AIRFLOW_HOME}

WORKDIR ${AIRFLOW_HOME}

# Expose port for Airflow Webserver
EXPOSE 8080

# Set entrypoint for CLI access
ENTRYPOINT ["/bin/bash"]
