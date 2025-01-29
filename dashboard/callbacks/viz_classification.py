import plotly.express as px

def viz_classification(filtered_df):

    fig = px.bar(
        filtered_df,
        x="classification_label",
        y="repo_count",
        text="repo_count"
    )

    fig.update_traces(
        textposition="outside",
        textfont_size=10
    )

    # Update layout
    fig.update_layout(
        showlegend=False,
        title={"x": 0.5},
        xaxis_title="",
        yaxis_title="Repository Count",
        dragmode=False
    )

    return fig
