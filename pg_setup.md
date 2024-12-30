## Setup Steps

1. **Make Entrypoint Executable**

    ```bash
    chmod +x docker-entrypoint.sh
    ```

2. **Create Data Directory**

    ```bash
    mkdir -p ./pgdata
    chmod 700 ./pgdata
    ```

3. **Determine UID and GID**

    ```bash
    UID=$(id -u)
    GID=$(id -g)
    ```

4. **Build Docker Image**

    ```bash
    docker build --no-cache -t postg --build-arg USER_ID=$UID --build-arg GROUP_ID=$GID .
    ```

5. **Remove Existing Container (if any)**

    ```bash
    docker rm -f postgres13d
    ```

6. **Run Docker Container**

    ```bash
    docker run -d \
        --name postgres13d \
        -p 5432:5432 \
        -v $(pwd)/pgdata:/var/lib/pgsql/data \
        -e POSTGRES_USER=someuser \
        -e POSTGRES_PASSWORD=somepassword \
        -e POSTGRES_DB=somedatabase \
        postg
    ```

7. **Verify Container is Running**

    ```bash
    docker ps
    ```

8. **Check Container Logs**

    ```bash
    docker logs postgres13d
    ```

9. **Connect to PostgreSQL**

    ```bash
    psql -h localhost -p 5432 -U someuser -d somedatabase
    ```

