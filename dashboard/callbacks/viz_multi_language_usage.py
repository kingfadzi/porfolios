import plotly.express as px

def viz_language_usage_buckets(df):
    """
    Create a bar chart visualizing the number of languages used per repository (buckets).
    """
    fig = px.bar(
        df,
        x="language_bucket",
        y="repo_count",
        color="language_bucket",
        labels={
            "language_bucket": "Number of Languages (Bucket)",
            "repo_count": "Repository Count"
        },
        title="Repository Count by Language Usage Bucket"
    )
    fig.update_layout(
        showlegend=False,
        template="plotly_white",
        xaxis=dict(categoryorder="total descending"),
        title_x=0.5,
        dragmode=False
    )
    return fig