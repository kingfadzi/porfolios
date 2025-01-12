from dash import Input, Output
from data.data_loader import (
    fetch_active_inactive_data,
    fetch_classification_data,
    fetch_language_data,
    fetch_heatmap_data,
)
from callbacks.viz_functions import create_bar_chart, create_pie_chart, create_language_chart, create_heatmap

def register_callbacks(app):
    @app.callback(
        [
            Output("active-inactive-bar", "figure"),
            Output("classification-pie", "figure"),
            Output("repos-by-language-bar", "figure"),
            Output("heatmap-viz", "figure"),
        ],
        [
            Input("host-name-filter", "value"),
            Input("language-filter", "value"),
            Input("app-id-filter", "value"),
            Input("classification-filter", "value"),
        ],
    )
    def update_charts(selected_hosts, selected_languages, app_id_input, selected_classifications):
        # Parse the app_id input
        if app_id_input:
            app_ids = [id.strip() for id in app_id_input.split(",")]
        else:
            app_ids = None

        # Create a dictionary of filters dynamically
        filters = {
            "host_name": selected_hosts,
            "main_language": selected_languages,
            "app_id": app_ids,
            "classification_label": selected_classifications,
        }

        # Fetch data for each visualization
        active_inactive_data = fetch_active_inactive_data(filters)
        classification_data = fetch_classification_data(filters)
        language_data = fetch_language_data(filters)
        heatmap_data = fetch_heatmap_data(filters)

        # Generate visualizations
        return (
            create_bar_chart(active_inactive_data),
            create_pie_chart(classification_data),
            create_language_chart(language_data),
            create_heatmap(heatmap_data),
        )