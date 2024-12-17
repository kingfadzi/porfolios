# Step 1: Partial clone
git clone --filter=blob:none --no-checkout <repo-url> repo-analysis
cd repo-analysis

# Step 2: Gather metrics
du -sb .git | awk '{print $1}'               # Repo size
git ls-tree -r HEAD --name-only | wc -l      # File count
git rev-list --count HEAD                    # Total commits
git shortlog -s -n | wc -l                   # Number of contributors
git log -1 --format="%ci"                    # Last commit date
git log --reverse --format="%ci" | head -1   # First commit date
first_commit=$(git log --reverse --format="%ci" | head -1)
last_commit=$(git log -1 --format="%ci")
echo $(( ($(date -d "$last_commit" +%s) - $(date -d "$first_commit" +%s)) / 86400 )) # Repo age
git branch -r | wc -l                        # Active branch count

# Step 3: Temporary checkout for go-enry
git checkout HEAD -- .
go-enry -json . > languages.json
git clean -fd  # Clean up
