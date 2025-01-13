from dash import Dash
from layouts.layout_main import main_layout
from app_callbacks import register_callbacks, register_dropdown_callbacks
import dash_bootstrap_components as dbc
import plotly.io as pio

# Set Bootstrap theme and Plotly template
app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
pio.templates.default = "plotly_white"

# Set layout
app.layout = main_layout()

# Register callbacks
register_callbacks(app)
register_dropdown_callbacks(app)

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
