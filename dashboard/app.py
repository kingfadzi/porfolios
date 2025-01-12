from dash import Dash
from layouts.layout_main import main_layout
from data.data_loader import load_data
from callbacks import register_callbacks
import dash_bootstrap_components as dbc
import plotly.io as pio

# Set Bootstrap theme and Plotly template
app = Dash(__name__, external_stylesheets=[dbc.themes.MINTY])  # Choose a theme
pio.templates.default = "plotly_white"  # Set global chart style

# Load data
df = load_data()

# Set layout
app.layout = main_layout(
    host_names=df['host_name'].dropna().unique(),
    languages=df['main_language'].dropna().unique(),
    app_ids=df['app_id'].dropna().unique(),
    classification_labels=df['classification_label'].dropna().unique(),
)

# Register callbacks
register_callbacks(app, df)

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)