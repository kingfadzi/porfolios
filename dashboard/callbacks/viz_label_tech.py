import plotly.express as px

def viz_label_tech(filtered_df):

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
