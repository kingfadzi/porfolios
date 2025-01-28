import plotly.express as px

def viz_last_commit_buckets(df):
    if "commit_bucket" not in df.columns or "repo_count" not in df.columns:
        raise KeyError("Required columns 'commit_bucket' and 'repo_count' are missing in the DataFrame.")
    
    fig = px.bar(
        df,
        x="commit_bucket",
        y="repo_count",
        color="commit_bucket",
        labels={
            "commit_bucket": "Commit Recency",
            "repo_count": "Repository Count",
        },
    )
    fig.update_layout(
        showlegend=False,
        template="plotly_white",
        title_x=0.5,
        xaxis=dict(
            categoryorder="array",
            categoryarray=[
                "< 1 month", "1-3 months", "3-6 months", "6-9 months",
                "9-12 months", "12-18 months", "18-24 months", "24+ months"
            ],
        ),
        yaxis=dict(title="Repository Count"),
        dragmode=False,
    )
    return fig