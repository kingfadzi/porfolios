import plotly.express as px

def viz_label_tech(df):
    fig = px.bar(
        df,
        x="label_key",
        y="repo_count",
        color="label_value",
        barmode="stack",
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    fig.update_layout(
        dragmode=False,
        xaxis_title="", 
        yaxis_title="Repository Count",  
        legend_title_text=None
    )
    return fig