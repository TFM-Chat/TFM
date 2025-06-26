# logging_config.py
import logging
from logging.handlers import RotatingFileHandler

log_filename = "application.log"
log_handler = RotatingFileHandler(log_filename, maxBytes=1024*1024, backupCount=5)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        log_handler,
                        logging.StreamHandler()
                    ])

def setup_logging():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            log_handler,
                            logging.StreamHandler()
                        ])