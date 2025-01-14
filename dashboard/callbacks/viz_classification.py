import plotly.express as px

def viz_classification(filtered_df):
    """
    Create a pie chart for repository classification.
    """
    return px.pie(
        filtered_df,
        names="classification_label",
        values="repo_count",
    ).update_traces(
        textinfo="percent+value",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percent: %{percent}",
    ).update_layout(dragmode=False, title={"x": 0.5})
