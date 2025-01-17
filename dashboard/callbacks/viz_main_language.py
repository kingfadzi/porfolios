import plotly.express as px

def viz_main_language(filtered_df):
    """
    Create a bar chart for Repositories by Main Language with custom axis labels.
    """
    return px.bar(
        filtered_df,
        x="main_language",
        y="repo_count",
        labels={
            "main_language": "Language",
            "repo_count": "Repository Count"
        },
    ).update_layout(
        dragmode=False,
        xaxis_title="Language",
        yaxis_title="Repository Count",
    )
