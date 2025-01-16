from sqlalchemy import create_engine, Column, Integer, String, PrimaryKeyConstraint
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class ComponentMapping(Base):
    __tablename__ = "component_mapping"
    component_id = Column(Integer, primary_key=True)
    mapping_type = Column(String, nullable=False)
    project_key = Column(String, nullable=True)
    repo_slug = Column(String, nullable=True)
    identifier = Column(String, nullable=True)
    transaction_cycle = Column(String, nullable=True)
    component_name = Column(String, nullable=True)
    web_url = Column(String, nullable=True)


class BusinessAppMapping(Base):
    __tablename__ = "business_app_mapping"
    id = Column(Integer, primary_key=True)
    component_id = Column(Integer, nullable=False)
    transaction_cycle = Column(String, nullable=False)
    component_name = Column(String, nullable=False)
    business_app_identifier = Column(String, nullable=False)


class VersionControlMapping(Base):
    __tablename__ = "version_control_mapping"
    id = Column(Integer, primary_key=True)
    component_id = Column(Integer, nullable=False)
    project_key = Column(String, nullable=False)
    repo_slug = Column(String, nullable=False)
    web_url = Column(String, nullable=True)


class RepoBusinessMapping(Base):
    __tablename__ = "repo_business_mapping"
    id = Column(Integer, primary_key=True)
    component_id = Column(Integer, nullable=False)
    project_key = Column(String, nullable=False)
    repo_slug = Column(String, nullable=False)
    business_app_identifier = Column(String, nullable=False)


engine = create_engine("postgresql://postgres:postgres@192.168.1.188:5422/gitlab-usage")
Session = sessionmaker(bind=engine)
session = Session()


def truncate_tables():
    print("[INFO] Truncating tables...")
    session.execute("TRUNCATE TABLE business_app_mapping RESTART IDENTITY CASCADE;")
    session.execute("TRUNCATE TABLE version_control_mapping RESTART IDENTITY CASCADE;")
    session.execute("TRUNCATE TABLE repo_business_mapping RESTART IDENTITY CASCADE;")
    session.commit()
    print("[INFO] Tables truncated.")


def populate_business_app_mapping():
    print("[INFO] Populating business_app_mapping...")
    components = session.query(ComponentMapping).filter_by(mapping_type="ba").all()
    print(f"[INFO] Retrieved {len(components)} components with mapping_type='ba'.")

    for idx, component in enumerate(components):
        session.add(BusinessAppMapping(
            component_id=component.component_id,
            transaction_cycle=component.transaction_cycle,
            component_name=component.component_name,
            business_app_identifier=component.identifier
        ))
        if idx % 100 == 0:
            print(f"[INFO] Processed {idx} rows for business_app_mapping...")

    session.commit()
    print("[INFO] Finished populating business_app_mapping.")


def populate_version_control_mapping():
    print("[INFO] Populating version_control_mapping...")
    components = session.query(ComponentMapping).filter(
        ComponentMapping.mapping_type == "vs",
        ComponentMapping.project_key.isnot(None),
        ComponentMapping.repo_slug.isnot(None)
    ).all()
    print(f"[INFO] Retrieved {len(components)} components with mapping_type='vs'.")

    for idx, component in enumerate(components):
        session.add(VersionControlMapping(
            component_id=component.component_id,
            project_key=component.project_key,
            repo_slug=component.repo_slug,
            web_url=component.web_url
        ))
        if idx % 100 == 0:
            print(f"[INFO] Processed {idx} rows for version_control_mapping...")

    session.commit()
    print("[INFO] Finished populating version_control_mapping.")


def populate_repo_business_mapping():
    print("[INFO] Populating repo_business_mapping...")
    version_controls = session.query(ComponentMapping).filter_by(mapping_type="vs").all()
    business_apps = session.query(ComponentMapping).filter_by(mapping_type="ba").all()

    print(f"[INFO] Retrieved {len(version_controls)} version control mappings.")
    print(f"[INFO] Retrieved {len(business_apps)} business application mappings.")

    for idx_vc, vc in enumerate(version_controls):
        for ba in business_apps:
            if vc.component_id == ba.component_id:
                session.add(RepoBusinessMapping(
                    component_id=vc.component_id,
                    project_key=vc.project_key,
                    repo_slug=vc.repo_slug,
                    business_app_identifier=ba.identifier
                ))
        if idx_vc % 100 == 0:
            print(f"[INFO] Processed {idx_vc} rows for repo_business_mapping...")

    session.commit()
    print("[INFO] Finished populating repo_business_mapping.")


def main():
    print("[INFO] Starting the data population script...")
    truncate_tables()
    populate_business_app_mapping()
    populate_version_control_mapping()
    populate_repo_business_mapping()
    print("[INFO] Data population script completed.")


if __name__ == "__main__":
    main()
