import plotly.express as px

def viz_main_language(filtered_df):
    """
    Create a bar chart for Repositories by Main Language.
    """
    return px.bar(
        filtered_df,
        x="main_language",
        y="repo_count",
    ).update_layout(dragmode="pan", title={"x": 0.5})
