import plotly.express as px

def create_bar_chart(filtered_df):
    """
    Create a bar chart for Active vs Inactive repositories.
    """
    # Aggregate data by activity_status
    aggregated_df = filtered_df.groupby("activity_status", as_index=False)["repo_count"].sum()

    # Normalize the activity_status values
    aggregated_df["activity_status"] = aggregated_df["activity_status"].str.capitalize()

    # Define custom colors for Active and Inactive
    color_map = {"Active": "green", "Inactive": "red"}

    return px.bar(
        aggregated_df,
        x="activity_status",
        y="repo_count",
        color="activity_status",
        color_discrete_map=color_map,
    ).update_layout(
        dragmode=False,
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
    ).update_traces(
        textinfo="percent+value",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percent: %{percent}",
    ).update_layout(
        dragmode=False,
        title={"x": 0.5},
    )


def create_language_chart(filtered_df):
    """
    Create a bar chart for Repositories by Main Language.
    """
    return px.bar(
        filtered_df,
        x="main_language",
        y="repo_count",
    ).update_layout(
        dragmode="pan",
        title={"x": 0.5},
    )


def create_heatmap(filtered_df):
    """
    Create a heatmap for Commit Buckets vs Contributor Buckets.
    """
    # Pivot data for the heatmap
    heatmap_data = filtered_df.pivot(
        index="contributor_bucket",
        columns="commit_bucket",
        values="repo_count",
    ).fillna(0)

    return px.imshow(
        heatmap_data,
        text_auto=True,
    ).update_layout(
        dragmode=False,
        title={"x": 0.5},
    )
