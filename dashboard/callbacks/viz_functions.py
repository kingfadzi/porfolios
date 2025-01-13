import plotly.express as px
import pandas as pd

def create_bar_chart(filtered_df):
    """
    Create a bar chart for Active vs Inactive repositories.
    Ensures accurate totals in the title and proper aggregation of data.
    """
    # Aggregate data by activity_status
    aggregated_df = filtered_df.groupby("activity_status", as_index=False)["repo_count"].sum()

    # Calculate total count
    total_count = aggregated_df["repo_count"].sum()

    # Normalize the activity_status values to ensure case matches the color_map
    aggregated_df["activity_status"] = aggregated_df["activity_status"].str.capitalize()

    # Define custom colors for Active and Inactive
    color_map = {"Active": "green", "Inactive": "red"}

    return px.bar(
        aggregated_df,
        x="activity_status",
        y="repo_count",
        color="activity_status",
        title=f"Active vs Inactive Repositories (Total: {total_count})",  # Add total to title
        color_discrete_map=color_map,  # Apply color map
    ).update_layout(
        dragmode=False,
        title={"x": 0.5},  # Center the title
    )
    
def create_pie_chart(filtered_df):
    """
    Create a pie chart for repository classification.
    Includes total in the chart title and hover text.
    """
    # Calculate total count
    total_count = filtered_df["repo_count"].sum()

    return px.pie(
        filtered_df,
        names="classification_label",
        values="repo_count",
        title=f"Repository Classification (Total: {total_count})",  # Add total to title
    ).update_traces(
        textinfo="percent+value",  # Show percentage and value on the chart
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percent: %{percent}",  # Custom hover text
    ).update_layout(
        dragmode=False,
        title={"x": 0.5},  # Center the title
    )


def create_language_chart(filtered_df):
    """
    Create a bar chart for Repositories by Main Language.
    Includes total in the chart title.
    """
    # Calculate total count
    total_count = filtered_df["repo_count"].sum()

    return px.bar(
        filtered_df,
        x="main_language",
        y="repo_count",
        title=f"Repositories by Main Language (Total: {total_count})",  # Add total to title
    ).update_layout(
        dragmode="pan",  # Enable panning
        title={"x": 0.5},  # Center the title
    )


def create_heatmap(filtered_df):
    """
    Create a heatmap for Commit Buckets vs Contributor Buckets.
    Includes total in the chart title and annotations.
    """
    # Calculate total count
    total_count = filtered_df["repo_count"].sum()

    # Pivot data for the heatmap
    heatmap_data = filtered_df.pivot(
        index="contributor_bucket", 
        columns="commit_bucket", 
        values="repo_count"
    ).fillna(0)

    return px.imshow(
        heatmap_data,
        text_auto=True,  # Add values as annotations
        title=f"Repositories by Commits and Contributors (Total: {total_count})",  # Add total to title
    ).update_layout(
        dragmode=False,
        title={"x": 0.5},  # Center the title
    )