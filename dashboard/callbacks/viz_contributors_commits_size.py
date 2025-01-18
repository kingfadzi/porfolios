import plotly.express as px

def human_readable_size(size_in_bytes):
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024**2:
        return f"{size_in_bytes / 1024:.2f} KB"
    elif size_in_bytes < 1024**3:
        return f"{size_in_bytes / 1024**2:.2f} MB"
    elif size_in_bytes < 1024**4:
        return f"{size_in_bytes / 1024**3:.2f} GB"
    else:
        return f"{size_in_bytes / 1024**4:.2f} TB"

def viz_contributors_commits_size(filtered_df):
    filtered_df["repo_size"] = filtered_df["repo_size"].fillna(0)
    filtered_df["repo_size_human"] = filtered_df["repo_size"].apply(human_readable_size)

    max_size = filtered_df["repo_size"].max()
    scales = [(1, "B"), (1024, "KB"), (1024**2, "MB"), (1024**3, "GB"), (1024**4, "TB")]

    tickvals = [scale[0] for scale in scales if scale[0] <= max_size or scale[0] == 1]
    ticktext = [f"1 {scale[1]}" for scale in scales if scale[0] <= max_size or scale[0] == 1]

    return px.scatter(
        filtered_df,
        x="contractors",
        y="commits",
        size="repo_size",
        size_max=60,
        labels={
            "contractors": "Number of Contributors",
            "commits": "Total Commits",
            "repo_size": "Repository Size",
        },
        color="repo_size",
        hover_data={"repo_url": True, "repo_size_human": True},
    ).update_layout(
        template="plotly_white",
        dragmode="zoom",
        title={"x": 0.5},
        coloraxis_colorbar=dict(
            title="Repository Size",
            tickvals=tickvals,
            ticktext=ticktext,
        ),
    )