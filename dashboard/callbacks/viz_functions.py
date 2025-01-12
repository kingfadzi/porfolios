import plotly.express as px
import pandas as pd

def create_bar_chart(filtered_df):
    return px.bar(
        filtered_df,
        x="activity_status",
        color="activity_status",
        title="Active vs Inactive Repositories",
        labels={"activity_status": "Activity Status"},
        barmode="group",
        color_discrete_sequence=px.colors.qualitative.Set1,
    ).update_layout(
        title={"x": 0.5},
        dragmode="pan",
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="#ffffff",
    )


def create_pie_chart(filtered_df):
    total_count = filtered_df.shape[0]

    pie_chart = px.pie(
        filtered_df,
        names="classification_label",
        title=f"Repository Classification (Total: {total_count})",
        hole=0.4,
    )

    pie_chart.update_traces(
        textinfo="percent+value",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percent: %{percent}",
    )

    pie_chart.update_layout(
        title={"x": 0.5},
        legend_title="Classification",
        legend=dict(
            orientation="h",
            x=0.5,
            xanchor="center",
            y=-0.1,
        ),
    )

    return pie_chart


def create_heatmap(filtered_df):
    filtered_df["commit_bucket"] = pd.cut(
        filtered_df["total_commits"],
        bins=[0, 50, 100, 500, 1000, 5000, 10000],
        labels=["0-50", "51-100", "101-500", "501-1000", "1001-5000", "5001+"],
        right=False,
    )
    filtered_df["contributor_bucket"] = pd.cut(
        filtered_df["number_of_contributors"],
        bins=[0, 1, 5, 10, 20, 50, 100],
        labels=["0-1", "2-5", "6-10", "11-20", "21-50", "51+"],
        right=False,
    )

    heatmap_data = (
        filtered_df.groupby(["commit_bucket", "contributor_bucket"])
        .size()
        .reset_index(name="repo_count")
    )
    heatmap_matrix = heatmap_data.pivot(
        index="contributor_bucket",
        columns="commit_bucket",
        values="repo_count",
    ).fillna(0)

    return px.imshow(
        heatmap_matrix,
        text_auto=True,
        title="Number of Repositories by Commits and Contributors",
        labels={"x": "Commit Buckets", "y": "Contributor Buckets", "color": "Repo Count"},
        color_continuous_scale="Viridis",
    ).update_layout(
        dragmode="pan",
    )


def create_language_bar_chart(filtered_df):
    language_data = filtered_df.groupby("main_language").size().reset_index(name="repo_count")
    return px.bar(
        language_data,
        x="main_language",
        y="repo_count",
        title="Number of Repositories by Main Language",
        labels={"main_language": "Main Language", "repo_count": "Repo Count"},
        color="main_language",
        color_discrete_sequence=px.colors.qualitative.Set3,
    ).update_layout(
        title={"x": 0.5},
        xaxis={"title": "Main Language"},
        yaxis={"title": "Repository Count"},
        dragmode="pan",
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="#ffffff",
    )