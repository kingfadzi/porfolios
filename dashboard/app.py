import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine
import dash_bootstrap_components as dbc
import plotly.io as pio

# Set a global theme for all charts
pio.templates.default = "plotly_white"  # Choose your desired theme

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

    # Heatmap: Correlation between numeric metrics
    heatmap_data = filtered_df[
        ["total_lines_of_code", "repo_size_bytes", "total_commits", "number_of_contributors"]
    ].corr()
    heatmap_fig = px.imshow(
        heatmap_data,
        text_auto=True,
        title="Correlation Heatmap of Repository Metrics",
        labels=dict(color="Correlation"),
    )

    return bar_fig, pie_fig, heatmap_fig

# Run the app
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)