import pandas as pd
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

    min_size = filtered_df["repo_size"].min()
    max_size = filtered_df["repo_size"].max()

    tickvals = [min_size, max_size / 4, max_size / 2, 3 * max_size / 4, max_size]
    ticktext = [human_readable_size(val) for val in tickvals]

    fig = px.scatter(
        filtered_df,
        x="contributors",
        y="commits",
        size="repo_size",
        size_max=60,
        color="repo_size",
        labels={
            "repo_size_human": "Size",
            "repo_age_human": "Age",
            "contributors": "Number of Contributors",
            "commits": "Total Commits",
            "web_url": "URL",
            "all_languages": "Languages Used",
            "total_lines_of_code": "LOC",
            "file_count": "File Count",
        },
        hover_data={
            "repo_size_human": True,
            "repo_size": False,
            "web_url": True,
            "repo_age_human": True,
            "app_id": True,
            "tc": True,
            "component_id": True,
            "all_languages": True,
            "file_count": True,
            "total_lines_of_code": True
        },
    )

    fig.update_layout(
        template="plotly_white",
        dragmode="zoom",
        autosize=True,
        margin=dict(l=50, r=150, t=50, b=50),
        coloraxis_colorbar=dict(
            title=dict(
                text="Repository Size",
                side="top",
                font=dict(size=14),
            ),
            tickvals=tickvals,
            ticktext=ticktext,
        ),
        legend=dict(
            font=dict(size=12),
            itemsizing="trace",
        ),
    )

    return fig
