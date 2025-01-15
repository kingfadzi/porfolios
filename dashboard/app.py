from dash import Dash
from layouts.layout_main import main_layout
from app_callbacks import register_callbacks, register_dropdown_callbacks
import dash_bootstrap_components as dbc
import plotly.io as pio
from data.cache_instance import cache  # Import the cache instance

# Initialize Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # Flask server

# Configure Flask-Caching
server.config["CACHE_TYPE"] = "simple"  # Use 'redis' for production
server.config["CACHE_DEFAULT_TIMEOUT"] = 3600  # Cache timeout in seconds
cache.init_app(server)  # Initialize the cache with the Flask server

pio.templates.default = "plotly_white"

# Set layout
app.layout = main_layout()

# Register callbacks
register_callbacks(app)
register_dropdown_callbacks(app)

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
