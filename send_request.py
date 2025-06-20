import sys
import requests
import configparser
import os
import logging
from logging.handlers import RotatingFileHandler

# -------------------------------------------------------------------------------------------------------
# --- Logging Configuration ---

# Log file path
log_file = os.path.join(os.path.dirname(__file__), 'send_request.log')

# Configure root logger (everything at INFO level)
logging.basicConfig(
    level=logging.INFO,  # Log only INFO and above
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S",
    handlers=[
        RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3),
        logging.StreamHandler(sys.stdout)  # Logs to console
    ]
)

# Get logger instance
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------------
# --- End Point Settings ---

# INI file path
ini_path = os.path.join(os.path.dirname(__file__), 'config.ini')
# Read INI file
config = configparser.ConfigParser()
config.read(ini_path)
# Get service URL
end_point = config['SERVICE']['EndPoint']

# -------------------------------------------------------------------------------------------------------
# --- Functions ---

def send_data(data_dict):
    """
    Sends the given data dictionary as a JSON payload to the server endpoint.
    """
    try:
        response = requests.post(end_point, json=data_dict)
        response.raise_for_status()  # Raise an error for bad responses
        logger.info("Request successful: %s", response.json())  # Log response content
    except requests.exceptions.RequestException as e:
        logger.error("Error sending request: %s", e, exc_info=True)  # Log full traceback
        sys.exit(1)


if __name__ == "__main__":
    plugin_data = {
        'application_number': sys.argv[1],
        'lga_name': sys.argv[2],
        'block_number': sys.argv[3],
        'parcel_number': sys.argv[4]
    }
    send_data(plugin_data)
