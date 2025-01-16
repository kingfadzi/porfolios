from sqlalchemy import create_engine, Column, String, PrimaryKeyConstraint
from sqlalchemy.orm import declarative_base, sessionmaker

# Define SQLAlchemy ORM models
Base = declarative_base()

class ComponentMapping(Base):
    __tablename__ = "component_mapping"
    component_id = Column(String, primary_key=True)
    mapping_type = Column(String, nullable=False)
    project_key = Column(String, nullable=True)
    repo_slug = Column(String, nullable=True)
    identifier = Column(String, nullable=True)
    transaction_cycle = Column(String, nullable=True)
    component_name = Column(String, nullable=True)


class BusinessAppMapping(Base):
    __tablename__ = "business_app_mapping"
    component_id = Column(String, nullable=False)
    transaction_cycle = Column(String, nullable=False)
    component_name = Column(String, nullable=False)
    business_app_identifier = Column(String, nullable=False)
    __table_args__ = (PrimaryKeyConstraint('component_id', 'business_app_identifier'),)


class VersionControlMapping(Base):
    __tablename__ = "version_control_mapping"
    component_id = Column(String, nullable=False)
    project_key = Column(String, nullable=False)
    repo_slug = Column(String, nullable=False)
    __table_args__ = (PrimaryKeyConstraint('component_id', 'project_key', 'repo_slug'),)


class RepoBusinessMapping(Base):
    __tablename__ = "repo_business_mapping"
    component_id = Column(String, nullable=False)
    project_key = Column(String, nullable=False)
    repo_slug = Column(String, nullable=False)
    business_app_identifier = Column(String, nullable=False)
    __table_args__ = (PrimaryKeyConstraint('component_id', 'project_key', 'repo_slug', 'business_app_identifier'),)


# Database setup
engine = create_engine("postgresql://postgres:postgres@192.168.1.188:5422/gitlab-usage")
Session = sessionmaker(bind=engine)
session = Session()


def populate_business_app_mapping():
    components = session.query(ComponentMapping).filter_by(mapping_type="ba").all()
    for component in components:
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
    session.commit()


def populate_version_control_mapping():
    components = session.query(ComponentMapping).filter_by(mapping_type="vs").all()
    for component in components:
        existing = session.query(VersionControlMapping).filter_by(
            component_id=component.component_id,
            project_key=component.project_key,
            repo_slug=component.repo_slug
        ).first()
        if not existing:
            session.add(VersionControlMapping(
                component_id=component.component_id,
                project_key=component.project_key,
                repo_slug=component.repo_slug
            ))
    session.commit()


def populate_repo_business_mapping():
    version_controls = session.query(ComponentMapping).filter_by(mapping_type="vs").all()
    business_apps = session.query(ComponentMapping).filter_by(mapping_type="ba").all()

    for vc in version_controls:
        for ba in business_apps:
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
    session.commit()


def main():
    populate_business_app_mapping()
    populate_version_control_mapping()
    populate_repo_business_mapping()


if __name__ == "__main__":
    main()
