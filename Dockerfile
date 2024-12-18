FROM registry.access.redhat.com/ubi8/ubi:latest

# Set environment variables
ENV AIRFLOW_HOME=/usr/local/airflow
ENV global.cert=/path/to/cert.pem
ENV global.index=https://pypi.org/simple
ENV global.index-url=https://pypi.org/simple
ENV http_proxy=${HTTP_PROXY}
ENV https_proxy=${HTTPS_PROXY}

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
RUN mkdir -p /etc/pip/certs && \
    cp /path/to/self-signed-cert.pem /etc/pip/certs/ && \
    echo -e "[global]\ncert = /etc/pip/certs/self-signed-cert.pem\nindex-url = https://pypi.org/simple" > /etc/pip.conf

# Upgrade pip and install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir \
        apache-airflow \
        gitpython

# Create Airflow home directory
RUN mkdir -p ${AIRFLOW_HOME}

WORKDIR ${AIRFLOW_HOME}

# Expose port for Airflow Webserver
EXPOSE 8088

# Set entrypoint for CLI access
ENTRYPOINT ["/bin/bash"]
