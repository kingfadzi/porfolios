import plotly.express as px

def viz_multi_language_usage(df):
    """
    Create a bar chart visualizing the number of languages used per repository (buckets).
    """
    fig = px.bar(
        df,
        x="language_bucket",
        y="repo_count",
        color="language_bucket",
        labels={
            "language_bucket": "Number of Languages per Repo",
            "repo_count": "Repository Count"
        },
        
    )
    fig.update_layout(
        showlegend=False,
        template="plotly_white",
        xaxis=dict(categoryorder="total descending"),
        title_x=0.5,
        dragmode=False
    )
    return fig