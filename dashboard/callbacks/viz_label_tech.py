import plotly.express as px

def viz_label_tech(filtered_df):
    """
    Create a stacked bar chart for label_key (category) vs. label_value (technology),
    showing the number of repositories (repo_count) in each segment.
    """
    # In case you need further grouping, do it here:
    # aggregated_df = filtered_df.groupby(["label_key", "label_value"], as_index=False)["repo_count"].sum()
    # If your SQL already handles the grouping, you can use 'filtered_df' directly.
    aggregated_df = filtered_df

    fig = px.bar(
        aggregated_df,
        x="label_key",
        y="repo_count",
        color="label_value",
        barmode="stack",  # stacked bar
        color_discrete_sequence=px.colors.qualitative.Plotly,  # optional: default color palette
    )

    fig.update_layout(
        dragmode=False,
        xaxis_title="Category (label_key)",
        yaxis_title="Repository Count",
        legend_title="Technology (label_value)",
    )

    return fig