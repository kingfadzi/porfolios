from git import Repo
from datetime import datetime
import pytz
from sqlalchemy.dialects.postgresql import insert
from models import Session, Repository, RepoMetrics

def calculate_and_persist_repo_metrics(repo_dir, repo, session):
    repo_obj = Repo(repo_dir)
    default_branch = repo_obj.active_branch.name

    total_size = sum(blob.size for blob in repo_obj.tree(default_branch).traverse() if blob.type == 'blob')
    file_count = sum(1 for blob in repo_obj.tree(default_branch).traverse() if blob.type == 'blob')
    total_commits = sum(1 for _ in repo_obj.iter_commits(default_branch))
    contributors = set(commit.author.email for commit in repo_obj.iter_commits(default_branch))
    last_commit_date = max(commit.committed_datetime for commit in repo_obj.iter_commits(default_branch))
    first_commit_date = min(commit.committed_datetime for commit in repo_obj.iter_commits(default_branch))
    repo_age_days = (datetime.utcnow().replace(tzinfo=pytz.utc) - first_commit_date).days

    session.execute(
        insert(RepoMetrics).values(
            repo_id=repo.repo_id,
            repo_size_bytes=total_size,
            file_count=file_count,
            total_commits=total_commits,
            number_of_contributors=len(contributors),
            last_commit_date=last_commit_date,
            repo_age_days=repo_age_days,
            active_branch_count=len(repo_obj.branches)
        ).on_conflict_do_update(
            index_elements=['repo_id'],
            set_={"repo_size_bytes": total_size, "file_count": file_count, "updated_at": datetime.utcnow()}
        )
    )
    session.commit()

if __name__ == "__main__":
    session = Session()
    repositories = session.query(Repository).filter_by(status="ANALYZED").limit(1).all()
    for repo in repositories:
        repo_dir = f"/mnt/tmpfs/cloned_repositories/{repo.repo_slug}"
        calculate_and_persist_repo_metrics(repo_dir, repo, session)
    session.close()
