import plotly.express as px

def viz_active_inactive(filtered_df):
    """
    Create a bar chart for Active vs Inactive repositories with a host_name dimension and custom color mapping.
    """
    # Aggregate by activity_status and host_name
    aggregated_df = filtered_df.groupby(
        ["activity_status", "host_name"], as_index=False
    )["repo_count"].sum()
    aggregated_df["activity_status"] = aggregated_df["activity_status"].str.capitalize()

    # Define color map for activity_status
    color_map = {"Active": "green", "Inactive": "red"}

    # Create the bar chart
    fig = px.bar(
        aggregated_df,
        x="activity_status",
        y="repo_count",
        color="host_name",  # Use host_name as the color dimension
        barmode="stack",  # Stacked bar chart
        color_discrete_sequence=px.colors.qualitative.Plotly,  # Default color palette for host_name
    )

    # Update bar colors for activity_status
    for trace in fig.data:
        if trace.name in color_map:
            trace.marker.color = color_map[trace.name]

    fig.update_layout(
        dragmode=False,
        title={"text": "Active vs Inactive Repositories by Host Name", "x": 0.5},
        xaxis_title="Activity Status",
        yaxis_title="Repository Count",
        legend_title="Host Name",
    )

    return fig
