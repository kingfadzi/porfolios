from dash import html
import dash_bootstrap_components as dbc
from layouts.layout_filters import filter_layout
from layouts.layout_charts import chart_layout

def main_layout(host_names, languages, app_ids, classification_labels):
    return dbc.Container(
        [
            dbc.Row(
                dbc.Col(
                    html.H1("Repository Metrics Dashboard", className="text-center text-primary mb-4"),
                    width=12,
                )
            ),
            dbc.Row(
                [
                    filter_layout(host_names, languages, app_ids, classification_labels),
                    chart_layout(),
                ],
            ),
        ],
        fluid=True,
    )