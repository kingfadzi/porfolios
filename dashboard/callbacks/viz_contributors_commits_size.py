import plotly.express as px

def viz_contributors_vs_commits(filtered_df):
    """
    Create a scatter plot for contributors vs. commits with repository size as bubble size.
    """
    return px.scatter(
        filtered_df,
        x="contractors",
        y="commits",
        size="repo_size",
        size_max=60,  # Set maximum bubble size
        title="Scatter Plot: Contributors vs. Commits",
        labels={
            "contractors": "Number of Contributors",
            "commits": "Total Commits",
            "repo_size": "Repository Size (Bytes)",
        },
        color="repo_size",  # Optional: color bubbles based on repo size
    ).update_layout(
        template="plotly_white",
        dragmode="pan",
        title={"x": 0.5},  # Center the title
    )