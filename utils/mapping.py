from sqlalchemy import create_engine, text

# Database setup
engine = create_engine("postgresql://postgres:postgres@192.168.1.188:5422/gitlab-usage")


def truncate_tables():
    print("[INFO] Truncating tables...")
    with engine.connect() as connection:
        connection.execute("TRUNCATE TABLE business_app_mapping RESTART IDENTITY CASCADE;")
        connection.execute("TRUNCATE TABLE version_control_mapping RESTART IDENTITY CASCADE;")
        connection.execute("TRUNCATE TABLE repo_business_mapping RESTART IDENTITY CASCADE;")
    print("[INFO] Tables truncated.")


def populate_business_app_mapping():
    print("[INFO] Populating business_app_mapping...")
    query = text("""
        SELECT *
        FROM component_mapping
        WHERE mapping_type = 'ba'
    """)
    with engine.connect() as connection:
        rows = connection.execute(query).fetchall()
    print(f"[INFO] Retrieved {len(rows)} rows with mapping_type='ba'.")

    insert_query = text("""
        INSERT INTO business_app_mapping (component_id, transaction_cycle, component_name, business_app_identifier)
        VALUES (:component_id, :transaction_cycle, :component_name, :business_app_identifier)
    """)
    with engine.connect() as connection:
        for idx, row in enumerate(rows):
            connection.execute(insert_query, {
                "component_id": row["component_id"],
                "transaction_cycle": row["transaction_cycle"],
                "component_name": row["component_name"],
                "business_app_identifier": row["identifier"]
            })
            if idx % 100 == 0:
                print(f"[INFO] Processed {idx} rows for business_app_mapping...")
    print("[INFO] Finished populating business_app_mapping.")


def populate_version_control_mapping():
    print("[INFO] Populating version_control_mapping...")
    query = text("""
        SELECT *
        FROM component_mapping
        WHERE mapping_type = 'vs'
    """)
    with engine.connect() as connection:
        rows = connection.execute(query).fetchall()
    print(f"[INFO] Retrieved {len(rows)} rows with mapping_type='vs'.")

    insert_query = text("""
        INSERT INTO version_control_mapping (component_id, project_key, repo_slug, web_url)
        VALUES (:component_id, :project_key, :repo_slug, :web_url)
    """)
    with engine.connect() as connection:
        for idx, row in enumerate(rows):
            connection.execute(insert_query, {
                "component_id": row["component_id"],
                "project_key": row["project_key"],
                "repo_slug": row["repo_slug"],
                "web_url": row["web_url"]
            })
            if idx % 100 == 0:
                print(f"[INFO] Processed {idx} rows for version_control_mapping...")
    print("[INFO] Finished populating version_control_mapping.")


def populate_repo_business_mapping():
    print("[INFO] Populating repo_business_mapping...")
    query_version_control = text("""
        SELECT *
        FROM component_mapping
        WHERE mapping_type = 'vs'
    """)
    query_business_app = text("""
        SELECT *
        FROM component_mapping
        WHERE mapping_type = 'ba'
    """)

    with engine.connect() as connection:
        version_controls = connection.execute(query_version_control).fetchall()
        business_apps = connection.execute(query_business_app).fetchall()

    print(f"[INFO] Retrieved {len(version_controls)} version control mappings.")
    print(f"[INFO] Retrieved {len(business_apps)} business application mappings.")

    insert_query = text("""
        INSERT INTO repo_business_mapping (component_id, project_key, repo_slug, business_app_identifier)
        VALUES (:component_id, :project_key, :repo_slug, :business_app_identifier)
    """)
    with engine.connect() as connection:
        for idx_vc, vc in enumerate(version_controls):
            for ba in business_apps:
                if vc["component_id"] == ba["component_id"]:
                    connection.execute(insert_query, {
                        "component_id": vc["component_id"],
                        "project_key": vc["project_key"],
                        "repo_slug": vc["repo_slug"],
                        "business_app_identifier": ba["identifier"]
                    })
            if idx_vc % 100 == 0:
                print(f"[INFO] Processed {idx_vc} rows for repo_business_mapping...")
    print("[INFO] Finished populating repo_business_mapping.")


def main():
    print("[INFO] Starting data population script...")
    truncate_tables()
    populate_business_app_mapping()
    populate_version_control_mapping()
    populate_repo_business_mapping()
    print("[INFO] Data population script completed.")


if __name__ == "__main__":
    main()
