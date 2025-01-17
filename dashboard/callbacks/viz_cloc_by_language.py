import plotly.express as px

def viz_cloc_by_language(filtered_df):
    """
    Create a stacked bar chart for CLOC metrics grouped by main_language.
    """
    # Debugging: Print DataFrame columns and head
    print("DataFrame Columns:", filtered_df.columns.tolist())
    print(filtered_df.head())

    # Proceed only if 'main_language' exists
    if 'main_language' not in filtered_df.columns:
        raise KeyError("The DataFrame does not contain a 'main_language' column.")

    # Reshape the data for stacked bar chart
    melted_df = filtered_df.melt(
        id_vars="main_language",
        value_vars=["blank_lines", "comment_lines", "total_lines_of_code", "source_code_file_count"],
        var_name="metric",
        value_name="count"
    )

    # Create the stacked bar chart
    fig = px.bar(
        melted_df,
        x="main_language",
        y="count",
        color="metric",
        labels={
            "main_language": "Language",  # Corrected label
            "count": "Lines of code",
            "metric": "Metric Type",
        },
        barmode="stack",  # Stacked bars
    ).update_layout(
        template="plotly_white",
        xaxis=dict(categoryorder="total descending"),  # Sort by total count
        dragmode="False",
    )

    return fig
