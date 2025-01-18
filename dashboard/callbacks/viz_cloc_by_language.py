import plotly.express as px

def viz_cloc_by_language(filtered_df):

    print("DataFrame Columns:", filtered_df.columns.tolist())
    print(filtered_df.head())

    # Create the stacked bar chart
    melted_df = filtered_df.melt(
        id_vars="main_language",
        value_vars=["blank_lines", "comment_lines", "total_lines_of_code", "source_code_file_count"],
        var_name="metric",
        value_name="count"
    )

    # Ensure hover and axis data show integers, not compact formats
    fig = px.bar(
        melted_df,
        x="main_language",
        y="count",
        color="metric",
        labels={
            "main_language": "Language",
            "count": "Lines of code",
            "metric": "Metric Type",
        },
        barmode="stack",
    ).update_layout(
        template="plotly_white",
        xaxis=dict(categoryorder="total descending"),
        dragmode=False,
        yaxis=dict(tickformat=",")  # Ensure y-axis values use commas, not compact formats
    )

    # Force hovertemplate to show numbers as integers with commas
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>%{y:,} lines<extra></extra>"
    )

    return fig
