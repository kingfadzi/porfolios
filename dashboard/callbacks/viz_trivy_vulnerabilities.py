import plotly.express as px

def viz_trivy_vulnerabilities(filtered_df):
    """
    Create a bar chart for vulnerabilities grouped by severity.
    """
    return px.bar(
        filtered_df,
        x="severity",
        y="repo_count",
        labels={
            "severity": "Severity Level",
            "repo_count": "Repository Count",
        },
        color="severity",  # Color bars by severity
    ).update_layout(
        template="plotly_white",
        title={"x": 0.5},  # Center the title
        dragmode=False,
        showlegend=False
    )
