import plotly.express as px

def viz_language_contributors_heatmap(filtered_df):
    heatmap_data = filtered_df.pivot(
        index="contributor_bucket",
        columns="language",
        values="repo_count"
    ).fillna(0)

    return px.imshow(
        heatmap_data,
        text_auto=True,
        labels={
            "x": "Language",
            "y": "Number of contributors",
            "color": "Repository Count",
        },
        color_continuous_scale="Viridis",
    ).update_layout(
        title={"x": 0.5},
        template="plotly_white",
        dragmode=False,
    )
