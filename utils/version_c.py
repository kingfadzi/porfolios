from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:postgres@192.168.1.188:5422/gitlab-usage")

def fetch_components():
    query = text("""
        SELECT *
        FROM component_mapping
        WHERE mapping_type = 'version_control'
    """)
    with engine.connect() as connection:
        results = connection.execute(query).fetchall()
    return results

components = fetch_components()
print(f"[INFO] Retrieved {len(components)} components with mapping_type='version_control'.")
