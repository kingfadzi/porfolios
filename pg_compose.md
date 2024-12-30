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

3. **Export UID and GID**
    ```bash
    export HOST_UID=$(id -u)
    export HOST_GID=$(id -g)
    ```

4. **Create `docker-postgres-compose.yaml`**
    ```yaml
    version: '3.8'

    services:
      postgres:
        build:
          context: .
          dockerfile: Dockerfile-postgres
          args:
            USER_ID: ${HOST_UID}
            GROUP_ID: ${HOST_GID}
        container_name: postgres13d
        ports:
          - "5422:5432"
        volumes:
          - ./pgdata:/var/lib/pgsql/data
        environment:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: airflow
    ```

5. **Build and Start Container**
    ```bash
    docker-compose -f docker-postgres-compose.yaml up -d --build
    ```

6. **Verify Container is Running**
    ```bash
    docker-compose -f docker-postgres-compose.yaml ps
    ```

7. **Check Logs**
    ```bash
    docker-compose -f docker-postgres-compose.yaml logs postgres
    ```

8. **Connect to PostgreSQL**
    ```bash
    psql -h localhost -p 5422 -U postgres -d airflow
    ```
    - **Password:** `postgres`

## Additional Commands

- **Stop and Remove Containers**
    ```bash
    docker-compose -f docker-postgres-compose.yaml down -v
    ```

- **Rebuild Without Cache**
    ```bash
    docker-compose -f docker-postgres-compose.yaml build --no-cache
    ```

- **Access Container Shell**
    ```bash
    docker exec -it postgres13d bash
    ```

## Troubleshooting

- **Permission Issues:**
    ```bash
    ls -ld ./pgdata
    ```
    - Ensure permissions are `drwx------` and owned by your user.

- **SELinux (AlmaLinux):**
    ```bash
    setenforce 0
    ```
    - **Note:** Revert with `setenforce 1` after testing.

- **Reset PostgreSQL Password Inside Container:**
    ```bash
    docker exec -it postgres13d bash
    psql -U postgres -d airflow
    ALTER ROLE postgres WITH PASSWORD 'postgres';
    \q
    exit
    docker-compose -f docker-postgres-compose.yaml restart postgres
    ```
