# FROM registry.access.redhat.com/ubi8/ubi:latest
FROM almalinux:8

# Set environment variables
ENV AIRFLOW_HOME=/home/airflow/airflow
ENV AIRFLOW_DAGS_FOLDER=/home/airflow/airflow/dags

# Accept build arguments for pip configuration and user IDs
ARG GLOBAL_INDEX
ARG GLOBAL_INDEX_URL
ARG HOST_UID=1000
ARG HOST_GID=1000

ARG GRADLE_DISTRIBUTIONS_BASE_URL="https://services.gradle.org/distributions/"
ARG GRADLE_VERSIONS="4.10.3 5.6.4 6.9.4 7.6.1 8.8 8.12"
ARG DEFAULT_GRADLE_VERSION=8.12

COPY keys/ /tmp/keys/

RUN if [ -f "/tmp/keys/tls-ca-bundle.pem" ]; then \
      mkdir -p /etc/ssl/certs && \
      cp /tmp/keys/tls-ca-bundle.pem /etc/ssl/certs/ && \
      echo -e "[global]\ncert = /etc/ssl/certs/tls-ca-bundle.pem" > /etc/pip.conf; \
    else \
      echo "[global]" > /etc/pip.conf; \
    fi && \
    [ -n "$GLOBAL_INDEX" ] && echo "index = ${GLOBAL_INDEX}" >> /etc/pip.conf; \
    echo "index-url = ${GLOBAL_INDEX_URL}" >> /etc/pip.conf

# Install system dependencies (merged duplicate blocks)
RUN dnf update -y && \
    dnf module reset -y python36 && \
    dnf install -y \
        bash \
        nc \
        glibc-langpack-en \
        python3.11 \
        python3-pip \
        python3-devel \
        git \
        wget && \
    dnf clean all

ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Set Python 3.11 as default and ensure pip is installed
RUN alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    alternatives --set python3 /usr/bin/python3.11 && \
    python3 -m ensurepip && \
    python3 -m pip install --no-cache-dir --upgrade pip


# Install Python dependencies (merged duplicate pip installs)
RUN python3 -m pip install --no-cache-dir \
    apache-airflow[postgres] \
    psycopg2-binary \
    gitpython \
    apache-airflow-providers-postgres \
    requests \
    pandas \
    numpy \
    lizard \
    semgrep \
    python-dotenv \
    checkov \
    sqlalchemy

# Install multiple JDK versions
RUN dnf install -y \
    java-1.8.0-openjdk-devel \
    java-11-openjdk-devel \
    java-17-openjdk-devel \
    java-21-openjdk-devel \
  && dnf clean all

RUN alternatives --install /usr/bin/java java /usr/lib/jvm/java-1.8.0/bin/java 1080 \
 && alternatives --install /usr/bin/java java /usr/lib/jvm/java-11/bin/java 1110 \
 && alternatives --install /usr/bin/java java /usr/lib/jvm/java-17/bin/java 1170 \
 && alternatives --install /usr/bin/java java /usr/lib/jvm/java-21/bin/java 1210

RUN alternatives --set java /usr/lib/jvm/java-17/bin/java

ENV JAVA_8_HOME="/usr/lib/jvm/java-1.8.0"
ENV JAVA_11_HOME="/usr/lib/jvm/java-11"
ENV JAVA_17_HOME="/usr/lib/jvm/java-17"
ENV JAVA_21_HOME="/usr/lib/jvm/java-21"

# default JAVA_HOME set to 17
ENV JAVA_HOME="${JAVA_17_HOME}"
ENV PATH="${JAVA_HOME}/bin:${PATH}"

RUN dnf install -y unzip wget \
 && mkdir -p /opt/gradle \
 && for VERSION in $GRADLE_VERSIONS; do \
      echo "Installing Gradle $VERSION..."; \
      wget "${GRADLE_DISTRIBUTIONS_BASE_URL}gradle-${VERSION}-bin.zip" -O /tmp/gradle-${VERSION}-bin.zip; \
      unzip -qo /tmp/gradle-${VERSION}-bin.zip -d /opt/gradle; \
      rm /tmp/gradle-${VERSION}-bin.zip; \
      ln -s "/opt/gradle/gradle-${VERSION}/bin/gradle" "/usr/local/bin/gradle-${VERSION}"; \
    done \
 && dnf clean all

ENV GRADLE_HOME="/opt/gradle/gradle-${DEFAULT_GRADLE_VERSION}"
ENV PATH="$GRADLE_HOME/bin:$PATH"

RUN dnf -y update && \
    dnf -y install dnf-plugins-core && \
    # Reset existing Maven module, enable the 3.8 stream, then install
    dnf module reset -y maven && \
    dnf module enable -y maven:3.8 && \
    dnf module install -y maven && \
    # Clean up
    dnf clean all

# Ensure the airflow group exists, rename if GID is already taken
RUN existing_group=$(getent group ${HOST_GID} | cut -d: -f1) && \
    if [ -z "$existing_group" ]; then \
        groupadd -g ${HOST_GID} airflow; \
    else \
        groupmod -n airflow "$existing_group"; \
    fi

# Ensure the airflow user exists, rename if UID is already taken
RUN existing_user=$(getent passwd ${HOST_UID} | cut -d: -f1) && \
    if [ -z "$existing_user" ]; then \
        useradd -m -u ${HOST_UID} -g airflow airflow; \
    else \
        usermod -l airflow "$existing_user"; \
    fi

# Set ownership for Airflow directories
RUN mkdir -p $AIRFLOW_HOME && \
    mkdir -p /home/airflow/cloned_repositories && \
    mkdir -p /home/airflow/output && \
    mkdir -p /home/airflow/.ssh && \
    mkdir -p /home/airflow/.syft && \
    mkdir -p /home/airflow/.grype && \
    mkdir -p /home/airflow/.trivy && \
    mkdir -p /home/airflow/.ssh && \
    mkdir -p /home/airflow/.cache/trivy && \
    mkdir -p /home/airflow/.semgrep/semgrep-rules && \
    chown -R airflow:airflow /home/airflow && \
    chmod 700 /home/airflow/.ssh

# Configure pip with dynamic settings (user-level)
RUN mkdir -p /home/airflow/.pip && \
    if [ -n "$GLOBAL_CERT" ]; then \
      echo -e "[global]\ncert = ${GLOBAL_CERT}\nindex-url = ${GLOBAL_INDEX_URL}" > /home/airflow/.pip/pip.conf; \
    else \
      echo -e "[global]\nindex-url = ${GLOBAL_INDEX_URL}" > /home/airflow/.pip/pip.conf; \
    fi

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
COPY --chown=airflow:airflow ./tools/grype/5 /home/airflow/.cache/grype/db/5

# syft
COPY --chown=airflow:airflow ./tools/syft/syft /usr/local/bin/syft
COPY --chown=airflow:airflow ./tools/syft/config.yaml /home/airflow/.syft/

# trivy
COPY --chown=airflow:airflow ./tools/trivy/trivy /usr/local/bin/trivy
COPY --chown=airflow:airflow ./tools/trivy/db /home/airflow/.cache/trivy/db
COPY --chown=airflow:airflow ./tools/trivy/.trivyignore /home/airflow/.trivy/.trivyignore

# semgrep
COPY --chown=airflow:airflow ./tools/semgrep/semgrep-rules  /home/airflow/.semgrep/semgrep-rules
COPY --chown=airflow:airflow ./tools/semgrep/config.ini /home/airflow/.semgrep/

# kantra
COPY --chown=airflow:airflow ./tools/kantra/kantra /usr/local/bin/kantra
COPY --chown=airflow:airflow tools/kantra  /home/airflow/.kantra

# Add and make start_services.sh executable
COPY --chown=airflow:airflow ./tools/start_services.sh /usr/local/bin/start_services.sh
RUN chmod +x /usr/local/bin/start_services.sh

# Make binaries and scripts executable
RUN chmod +x /usr/local/bin/*

# Switch to the airflow user
USER airflow

# Configure working directory and expose ports
WORKDIR $AIRFLOW_HOME
EXPOSE 8080

# Set ENTRYPOINT to start_services.sh
ENTRYPOINT ["/usr/local/bin/start_services.sh"]
