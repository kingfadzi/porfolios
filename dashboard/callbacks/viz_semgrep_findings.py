import plotly.express as px

def viz_semgrep_findings(filtered_df):
    """
    Create a bar chart for Semgrep findings grouped by category.
    """
    return px.bar(
        filtered_df,
        x="category",
        y="repo_count",
        labels={
            "category": "Finding Category",
            "repo_count": "Repository Count",
        },
        color="category",
    ).update_layout(
        template="plotly_white",
        title={"x": 0.5},
        dragmode="pan",
        showlegend=False
    )
