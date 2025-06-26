import json
import os
import logging
from logging_module.logging_config import setup_logging

# Configurar logging
setup_logging()

def save_metadata(metadata_path, metadata):
    try:
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        logging.info(f"Metadata saved")
    except Exception as e:
        logging.error(f"Error saving metadata to {metadata_path}: {e}")

def load_metadata(metadata_path):
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            logging.info(f"Metadata loaded from {metadata_path}: {metadata}")
            return metadata
        except Exception as e:
            logging.error(f"Error loading metadata from {metadata_path}: {e}")
            return {"paths": [], "timestamps": []}
    logging.warning(f"Metadata path {metadata_path} does not exist. Returning default metadata.")
    return {"paths": [], "timestamps": []}