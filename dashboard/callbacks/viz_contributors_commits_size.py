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

    # Determine the range of the repository sizes
    min_size = filtered_df["repo_size"].min()
    max_size = filtered_df["repo_size"].max()

    # Generate dynamic tick values and labels based on the filtered data range
    tickvals = []
    ticktext = []

    scales = [
        (1, "B"),
        (1024, "KB"),
        (1024**2, "MB"),
        (1024**3, "GB"),
        (1024**4, "TB"),
    ]

    for scale, label in scales:
        # Include tick if it lies within the filtered range
        if min_size <= scale <= max_size or scale == min_size or scale == max_size:
            tickvals.append(scale)
            ticktext.append(label)

    # If no ticks are generated (e.g., all values are identical), include at least one tick
    if len(tickvals) < 2:
        tickvals = [min_size, max_size]
        ticktext = [human_readable_size(min_size), human_readable_size(max_size)]

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