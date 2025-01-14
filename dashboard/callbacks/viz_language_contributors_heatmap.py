import plotly.express as px

def viz_language_contributors_heatmap(filtered_df):
    """
    Create a heatmap for programming languages and contributor buckets.
    """
    # Debugging: Check the structure of the DataFrame
    print("Columns in the DataFrame:", filtered_df.columns)

    # Pivot the data for heatmap
    heatmap_data = filtered_df.pivot(
        index="contributor_bucket",
        columns="language",  # Updated to match the alias in the query
        values="repo_count"
    ).fillna(0)

    return px.imshow(
        heatmap_data,
        text_auto=True,  # Display values inside heatmap cells
        labels={
            "x": "Programming Language",
            "y": "Contributor Bucket",
            "color": "Repository Count",
        },
        color_continuous_scale="Viridis",  # Choose a color scale
    ).update_layout(
        title={"x": 0.5},  # Center the title
        template="plotly_white",
    )
