import logging
import os
import random
import time
from flask import Flask, jsonify
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)

_handlers = [logging.StreamHandler()]
_log_file = os.environ.get('LOG_FILE', '/var/log/app/app.log')
try:
    os.makedirs(os.path.dirname(_log_file), exist_ok=True)
    _handlers.append(logging.FileHandler(_log_file))
except (OSError, PermissionError):
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=_handlers
)
logger = logging.getLogger(__name__)


@app.route("/")
def home():
    logger.info("Home endpoint accessed")
    return jsonify({"message": "LogGuard App Running", "status": "ok"})


@app.route("/order")
def order():
    time.sleep(random.uniform(0.1, 0.5))
    if random.random() < 0.3:
        logger.error("Order processing failed - payment gateway timeout")
        return jsonify({"error": "Order failed"}), 500
    order_id = random.randint(1000, 9999)
    logger.info(f"Order {order_id} processed successfully")
    return jsonify({"order_id": order_id, "status": "success"})


@app.route("/login")
def login():
    if random.random() < 0.2:
        logger.warning("Failed login attempt detected")
        return jsonify({"error": "Invalid credentials"}), 401
    logger.info("User logged in successfully")
    return jsonify({"status": "logged_in"})


@app.route("/health")
def health():
    return jsonify({"status": "up"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
