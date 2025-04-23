from app import app
import os
from prometheus_flask_exporter import PrometheusMetrics

metrics_app = PrometheusMetrics(app)

if "gunicorn" in os.environ.get("SERVER_SOFTWARE", ""):
	metrics_app.start_http_server(5788)

if __name__ == "__main__":
	app.run('0.0.0.0', 5770, debug=True)
