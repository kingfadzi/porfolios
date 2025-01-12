import plotly.express as px
import pandas as pd

def create_bar_chart(filtered_df):
    """
    Create a bar chart for Active vs Inactive repositories.
    Ensures 'Active' is green and 'Inactive' is red.
    """
    color_map = {"Active": "green", "Inactive": "red"}  # Define custom colors

    return px.bar(
        filtered_df,
        x="activity_status",
        y="repo_count",
        color="activity_status",
        title="Active vs Inactive Repositories",
        color_discrete_map=color_map,  # Apply color map
    ).update_layout(
        dragmode=False,  # Disable panning and zooming
        title={"x": 0.5},
    )


def create_pie_chart(filtered_df):
    """
    Create a pie chart for repository classification.
    """
    return px.pie(
        filtered_df,
        names="classification_label",
        values="repo_count",
        title="Repository Classification",
    ).update_layout(
        dragmode=False,  # Disable panning and zooming
        title={"x": 0.5},
    )


def create_language_chart(filtered_df):
    """
    Create a bar chart for Repositories by Main Language.
    Enables panning only.
    """
    return px.bar(
        filtered_df,
        x="main_language",
        y="repo_count",
        title="Repositories by Main Language",
    ).update_layout(
        dragmode="pan",  # Enable panning only
        title={"x": 0.5},
    )


def create_heatmap(filtered_df):
    """
    Create a heatmap for Commit Buckets vs Contributor Buckets.
    Disables both panning and zooming.
    """
    heatmap_data = filtered_df.pivot(
        index="contributor_bucket", 
        columns="commit_bucket", 
        values="repo_count"
    ).fillna(0)

    return px.imshow(
        heatmap_data,
        text_auto=True,
        title="Repositories by Commits and Contributors",
    ).update_layout(
        dragmode=False,  # Disable panning and zooming
        title={"x": 0.5},
    )