import plotly.express as px

def viz_classification(filtered_df):
    fig = px.pie(
        filtered_df,
        names="classification_label",
        values="repo_count",
    )
    fig.update_traces(
        textinfo="label+value+percent",
        textposition="outside",
        textfont_size=10
    )
    fig.update_layout(
        showlegend=False,               # Hide legend entirely
        title={"x": 0.5},
        dragmode=False,
    )
    return fig
