import plotly.express as px
import pandas as pd

def create_bar_chart(filtered_df):
    return px.bar(
        filtered_df,
        x="activity_status",
        y="repo_count",
        color="activity_status",
        title="Active vs Inactive Repositories",
    )

def create_pie_chart(filtered_df):
    return px.pie(
        filtered_df,
        names="classification_label",
        values="repo_count",
        title="Repository Classification",
    )

def create_language_chart(filtered_df):
    return px.bar(
        filtered_df,
        x="main_language",
        y="repo_count",
        title="Repositories by Main Language",
    )

def create_heatmap(filtered_df):
    heatmap_data = filtered_df.pivot(
        index="contributor_bucket", 
        columns="commit_bucket", 
        values="repo_count"
    ).fillna(0)

    return px.imshow(
        heatmap_data,
        text_auto=True,
        title="Repositories by Commits and Contributors",
    )