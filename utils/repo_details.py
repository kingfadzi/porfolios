#!/usr/bin/env python3

import re
from modular.models import Session, Base, Repository

def parse_git_url(url: str):
    patterns = [
        # Bitbucket SSH
        re.compile(r'^ssh://git@[^:]+:7999/(?P<project>[^/]+)/(?P<slug>[^/]+)\.git$'),
        # Bitbucket HTTPS
        re.compile(r'^https?://[^/]+/scm/(?P<project>[^/]+)/(?P<slug>[^/]+)\.git$'),
        # GitLab SSH (nested groups, including dots)
        re.compile(r'^git@[^:]+:(?P<group_repo_path>.+)\.git$'),
        # GitLab HTTPS (nested groups, including dots)
        re.compile(r'^https?://[^/]+/(?P<group_repo_path>.+)\.git$'),
        # GitHub SSH
        re.compile(r'^git@github\.com:(?P<project>[^/]+)/(?P<slug>[^/]+)\.git$'),
        # GitHub HTTPS
        re.compile(r'^https?://github\.com/(?P<project>[^/]+)/(?P<slug>[^/]+)\.git$')
    ]
    for pat in patterns:
        m = pat.match(url)
        if m:
            # For patterns that capture 'project' and 'slug' directly
            if 'project' in m.groupdict() and 'slug' in m.groupdict():
                return m.group('project'), m.group('slug')
            # For patterns that capture 'group_repo_path'
            parts = m.group('group_repo_path').split('/')
            return (
                '/'.join(parts[:-1]) if len(parts) > 1 else None,
                parts[-1] if parts else None
            )
    return None, None

def main():
    session = Session()
    repos = session.query(Repository).all()
    for r in repos:
        if r.clone_url_ssh:
            pkey, slug = parse_git_url(r.clone_url_ssh)
            print(f"URL: {r.clone_url_ssh}, PROJECT: {pkey}, SLUG: {slug}")
            if pkey:
                r.project_key = pkey
            if slug:
                r.repo_slug = slug
    session.commit()
    session.close()

if __name__ == "__main__":
    main()
