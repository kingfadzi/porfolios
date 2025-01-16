#!/usr/bin/env python3

import re
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

def parse_web_url(url: str):
    patterns = [
        # Bitbucket web
        re.compile(r'^https?://[^/]+(:\d+)?/projects/(?P<project>[^/]+)/repos/(?P<slug>[^/]+)/browse$'),
        # Bitbucket SSH
        re.compile(r'^ssh://git@[^:]+:7999/(?P<project>[^/]+)/(?P<slug>[^/]+)\.git$'),
        # Bitbucket HTTPS
        re.compile(r'^https?://[^/]+/scm/(?P<project>[^/]+)/(?P<slug>[^/]+)\.git$'),
        # GitLab SSH (nested)
        re.compile(r'^git@[^:]+:(?P<group_repo_path>.+)\.git$'),
        # GitLab HTTPS (nested)
        re.compile(r'^https?://[^/]+/(?P<group_repo_path>.+)\.git$'),
        # GitHub SSH
        re.compile(r'^git@github\.com:(?P<project>[^/]+)/(?P<slug>[^/]+)\.git$'),
        # GitHub HTTPS
        re.compile(r'^https?://github\.com/(?P<project>[^/]+)/(?P<slug>[^/]+)\.git$')
    ]
    for pat in patterns:
        m = pat.match(url or "")
        if m:
            gd = m.groupdict()
            if 'project' in gd and 'slug' in gd:
                return gd['project'], gd['slug']
            if 'group_repo_path' in gd:
                parts = gd['group_repo_path'].split('/')
                if len(parts) > 1:
                    return '/'.join(parts[:-1]), parts[-1]
                return None, parts[0] if parts else None
    return None, None

class ComponentMapping(Base):
    __tablename__ = "component_mapping"

    # Primary key so SQLAlchemy can handle updates
    id = Column(Integer, primary_key=True, autoincrement=True)

    component_id = Column(String)
    component_name = Column(String)
    tc = Column(String)
    mapping_type = Column(String)
    instance_url = Column(String)
    tool_type = Column(String)
    name = Column(String)
    identifier = Column(String)
    web_url = Column(String)
    project_key = Column(String)
    repo_slug = Column(String)

def main():
    engine = create_engine("postgresql://user:pass@localhost/dbname")
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create or update the DB schema (dev use). In prod, use migrations.
    Base.metadata.create_all(engine)

    rows = session.query(ComponentMapping).filter_by(mapping_type='version_control').all()
    for row in rows:
        pkey, slug = parse_web_url(row.web_url)
        if pkey or slug:
            print(f"URL: {row.web_url}, project_key: {pkey}, repo_slug: {slug}")
        if pkey:
            row.project_key = pkey
        if slug:
            row.repo_slug = slug

    session.commit()
    session.close()

if __name__ == "__main__":
    main()
