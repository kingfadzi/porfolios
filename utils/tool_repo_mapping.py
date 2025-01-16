#!/usr/bin/env python3

import re
from modular.models import Session, Base, ComponentMapping

def parse_web_url(url):
    patterns = [
        re.compile(r'^https?://[^/]+(:\d+)?/projects/(?P<project>[^/]+)/repos/(?P<slug>[^/]+)/browse$'),
        re.compile(r'^ssh://git@[^:]+:7999/(?P<project>[^/]+)/(?P<slug>[^/]+)\.git$'),
        re.compile(r'^https?://[^/]+/scm/(?P<project>[^/]+)/(?P<slug>[^/]+)\.git$'),
        re.compile(r'^git@[^:]+:(?P<group_repo_path>.+)\.git$'),
        re.compile(r'^https?://[^/]+/(?P<group_repo_path>.+)\.git$'),
        re.compile(r'^git@[^:]+:(?P<group_repo_path_no_dot>.+?)(?:\.git)?$'),
        re.compile(r'^https?://[^/]+/(?P<group_repo_path_no_dot>.+?)(?:\.git)?$'),
        re.compile(r'^git@github\.com:(?P<project>[^/]+)/(?P<slug>[^/]+)\.git$'),
        re.compile(r'^https?://github\.com/(?P<project>[^/]+)/(?P<slug>[^/]+)\.git$')
    ]
    for pat in patterns:
        m = pat.match(url or "")
        if m:
            gd = m.groupdict()
            if 'project' in gd and 'slug' in gd:
                return gd['project'], gd['slug']
            path = gd.get('group_repo_path') or gd.get('group_repo_path_no_dot')
            if path:
                parts = path.split('/')
                if len(parts) > 1:
                    return '/'.join(parts[:-1]), parts[-1]
                return None, parts[0] if parts else None
    return None, None

def main():
    session = Session()
    rows = session.query(ComponentMapping).filter_by(mapping_type='version_control').all()
    for row in rows:
        if row.web_url:
            pkey, slug = parse_web_url(row.web_url)
            print(f"web_url: {row.web_url}, project_key: {pkey}, repo_slug: {slug}")
            if pkey:
                row.project_key = pkey
            if slug:
                row.repo_slug = slug
    session.commit()
    session.close()

if __name__ == "__main__":
    main()
