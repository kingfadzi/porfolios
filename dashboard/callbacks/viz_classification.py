import plotly.express as px

def viz_classification(filtered_df):
    fig = px.pie(
        filtered_df,
        names="classification_label",
        values="repo_count",
    )
    fig.update_traces(
        textinfo="percent+value",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percent: %{percent}",
    )
    fig.update_layout(
        title={"x": 0.5},
        dragmode=False,
        legend=dict(
            orientation="v",
            x=1.02,
            xanchor="left",
            y=1,
            yanchor="auto",
            font=dict(size=8)  # Smaller font size
        )
    )
    return fig
