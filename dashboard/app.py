import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine
import dash_bootstrap_components as dbc
import plotly.io as pio

# Set a global theme for Plotly charts
pio.templates.default = "plotly_white"

# Database connection
engine = create_engine("postgresql://postgres:postgres@192.168.1.188:5422/gitlab-usage")

# Load data
query = "SELECT * FROM combined_repo_metrics"
df = pd.read_sql(query, engine)

# Dash app initialization with the LUX Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])
app.title = "Repository Metrics Dashboard"

# Get unique filter values
host_names = df['host_name'].dropna().unique()
languages = df['main_language'].dropna().unique()

# App layout
app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                html.H1("Repository Metrics Dashboard", className="text-center text-primary mb-4"),
                width=12,
            )
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Filter by Host Name:", className="form-label"),
                        dcc.Dropdown(
                            id="host-name-filter",
                            options=[{"label": name, "value": name} for name in host_names],
                            multi=True,
                            placeholder="Select Host Name(s)",
                            className="form-select",
                        ),
                    ],
                    width=6,
                ),
                dbc.Col(
                    [
                        html.Label("Filter by Main Language:", className="form-label"),
                        dcc.Dropdown(
                            id="language-filter",
                            options=[{"label": lang, "value": lang} for lang in languages],
                            multi=True,
                            placeholder="Select Language(s)",
                            className="form-select",
                        ),
                    ],
                    width=6,
                ),
            ],
            className="mb-4",
        ),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="active-inactive-bar", config={"displayModeBar": False}), width=6),
                dbc.Col(dcc.Graph(id="classification-pie", config={"displayModeBar": False}), width=6),
            ],
            className="mb-4",
        ),
        dbc.Row(
            dbc.Col(dcc.Graph(id="heatmap-viz", config={"displayModeBar": False}), width=12),
        ),
    ],
    fluid=True,
)

# Callbacks for interactivity
@app.callback(
    [
        Output("active-inactive-bar", "figure"),
        Output("classification-pie", "figure"),
        Output("heatmap-viz", "figure"),
    ],
    [Input("host-name-filter", "value"), Input("language-filter", "value")],
)
def update_charts(selected_hosts, selected_languages):
    # Filter data
    filtered_df = df.copy()
    if selected_hosts:
        filtered_df = filtered_df[filtered_df["host_name"].isin(selected_hosts)]
    if selected_languages:
        filtered_df = filtered_df[filtered_df["main_language"].isin(selected_languages)]
    
    # Bar chart: Active vs Inactive
    bar_fig = px.bar(
        filtered_df,
        x="activity_status",
        color="activity_status",
        title="Active vs Inactive Repositories",
        labels={"activity_status": "Activity Status"},
        barmode="group"
    )

    # Pie chart: Classification Labels
    pie_fig = px.pie(
        filtered_df,
        names="classification_label",
        title="Repository Classification",
        hole=0.4,
    )

    # Heatmap: Number of Repos by Commit and Contributor Buckets
    # Create buckets for commits and contributors
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

    # Aggregate the data
    heatmap_data = (
        filtered_df.groupby(["commit_bucket", "contributor_bucket"])
        .size()
        .reset_index(name="repo_count")
    )

    # Pivot the data to create a matrix for the heatmap
    heatmap_matrix = heatmap_data.pivot(
        index="contributor_bucket", 
        columns="commit_bucket", 
        values="repo_count"
    ).fillna(0)  # Replace NaNs with 0

    # Create the heatmap
    heatmap_fig = px.imshow(
        heatmap_matrix,
        text_auto=True,
        title="Number of Repositories by Commits and Contributors",
        labels={"x": "Commit Buckets", "y": "Contributor Buckets", "color": "Repo Count"},
        color_continuous_scale="Viridis",
    )

    heatmap_fig.update_layout(
        title={"x": 0.5, "font": {"size": 20}},
        xaxis={"side": "bottom", "title": "Commit Buckets"},
        yaxis={"title": "Contributor Buckets"},
        plot_bgcolor="white",
        margin={"t": 50, "l": 50, "r": 50, "b": 50},
    )

    return bar_fig, pie_fig, heatmap_fig

# Run the app
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)