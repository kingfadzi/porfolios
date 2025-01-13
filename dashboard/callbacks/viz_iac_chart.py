import plotly.express as px

def viz_iac_chart(filtered_df):
    """
    Create a bar chart for repositories by IaC type.
    """
    return px.bar(
        filtered_df,
        x="iac_type",
        y="repo_count",
        title="Repositories by IaC Type",
        labels={"iac_type": "IaC Type", "repo_count": "Repository Count"},
        color="iac_type",
    ).update_layout(
        xaxis=dict(categoryorder="total descending"),  # Sort by repo_count
        template="plotly_white",
        title={"x": 0.5},
        dragmode=False,
    )