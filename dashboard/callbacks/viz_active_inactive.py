import plotly.express as px

def viz_active_inactive(filtered_df):
    """
    Create a bar chart for Active vs Inactive repositories.
    """
    aggregated_df = filtered_df.groupby("activity_status", as_index=False)["repo_count"].sum()
    aggregated_df["activity_status"] = aggregated_df["activity_status"].str.capitalize()
    color_map = {"Active": "green", "Inactive": "red"}
    return px.bar(
        aggregated_df,
        x="activity_status",
        y="repo_count",
        color="activity_status",
        title="Active vs Inactive Repositories",
        color_discrete_map=color_map,
    ).update_layout(dragmode=False, title={"x": 0.5})