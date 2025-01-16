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
    web_url = Column(String, nullable=True)  # Added web_url field


class BusinessAppMapping(Base):
    __tablename__ = "business_app_mapping"
    component_id = Column(Integer, nullable=False)
    transaction_cycle = Column(String, nullable=False)
    component_name = Column(String, nullable=False)
    business_app_identifier = Column(String, nullable=False)
    __table_args__ = (PrimaryKeyConstraint('component_id', 'business_app_identifier'),)


class VersionControlMapping(Base):
    __tablename__ = "version_control_mapping"
    component_id = Column(Integer, nullable=False)
    project_key = Column(String, nullable=False)
    repo_slug = Column(String, nullable=False)
    web_url = Column(String, nullable=True)  # Added web_url field
    __table_args__ = (PrimaryKeyConstraint('component_id', 'project_key', 'repo_slug'),)


class RepoBusinessMapping(Base):
    __tablename__ = "repo_business_mapping"
    component_id = Column(Integer, nullable=False)
    project_key = Column(String, nullable=False)
    repo_slug = Column(String, nullable=False)
    business_app_identifier = Column(String, nullable=False)
    __table_args__ = (PrimaryKeyConstraint('component_id', 'project_key', 'repo_slug', 'business_app_identifier'),)


# Database setup
engine = create_engine("postgresql://postgres:postgres@192.168.1.188:5422/gitlab-usage")
Session = sessionmaker(bind=engine)
session = Session()


def populate_business_app_mapping():
    print("[INFO] Starting populate_business_app_mapping...")
    components = session.query(ComponentMapping).filter_by(mapping_type="ba").all()
    print(f"[INFO] Retrieved {len(components)} components with mapping_type='ba'.")

    for idx, component in enumerate(components):
        existing = session.query(BusinessAppMapping).filter_by(
            component_id=component.component_id,
            business_app_identifier=component.identifier
        ).first()
        if not existing:
            session.add(BusinessAppMapping(
                component_id=component.component_id,
                transaction_cycle=component.transaction_cycle,
                component_name=component.component_name,
                business_app_identifier=component.identifier
            ))
        if idx % 100 == 0:
            print(f"[INFO] Processed {idx} rows in populate_business_app_mapping...")

    session.commit()
    print("[INFO] Finished populate_business_app_mapping.")


def populate_version_control_mapping():
    print("[INFO] Starting populate_version_control_mapping...")
    components = session.query(ComponentMapping).filter(
        ComponentMapping.mapping_type == "vs",
        ComponentMapping.project_key.isnot(None),
        ComponentMapping.repo_slug.isnot(None)
    ).all()
    print(f"[INFO] Retrieved {len(components)} components with non-null project_key, repo_slug, and web_url.")

    for idx, component in enumerate(components):
        existing = session.query(VersionControlMapping).filter_by(
            component_id=component.component_id,
            project_key=component.project_key,
            repo_slug=component.repo_slug
        ).first()
        if not existing:
            session.add(VersionControlMapping(
                component_id=component.component_id,
                project_key=component.project_key,
                repo_slug=component.repo_slug,
                web_url=component.web_url  # Include web_url
            ))
        if idx % 100 == 0:
            print(f"[INFO] Processed {idx} rows in populate_version_control_mapping...")

    session.commit()
    print("[INFO] Finished populate_version_control_mapping.")


def populate_repo_business_mapping():
    print("[INFO] Starting populate_repo_business_mapping...")
    version_controls = session.query(ComponentMapping).filter(
        ComponentMapping.mapping_type == "vs",
        ComponentMapping.project_key.isnot(None),
        ComponentMapping.repo_slug.isnot(None)
    ).all()
    business_apps = session.query(ComponentMapping).filter_by(mapping_type="ba").all()

    print(f"[INFO] Retrieved {len(version_controls)} version control mappings with non-null project_key and repo_slug.")
    print(f"[INFO] Retrieved {len(business_apps)} business application mappings.")

    for idx_vc, vc in enumerate(version_controls):
        for idx_ba, ba in enumerate(business_apps):
            if vc.component_id == ba.component_id:
                existing = session.query(RepoBusinessMapping).filter_by(
                    component_id=vc.component_id,
                    project_key=vc.project_key,
                    repo_slug=vc.repo_slug,
                    business_app_identifier=ba.identifier
                ).first()
                if not existing:
                    session.add(RepoBusinessMapping(
                        component_id=vc.component_id,
                        project_key=vc.project_key,
                        repo_slug=vc.repo_slug,
                        business_app_identifier=ba.identifier
                    ))
        if idx_vc % 10 == 0:
            print(f"[INFO] Processed {idx_vc} version control mappings...")

    session.commit()
    print("[INFO] Finished populate_repo_business_mapping.")


def main():
    print("[INFO] Starting the data population script...")
    populate_business_app_mapping()
    populate_version_control_mapping()
    populate_repo_business_mapping()
    print("[INFO] Data population script completed.")


if __name__ == "__main__":
    main()
