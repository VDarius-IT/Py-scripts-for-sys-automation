import os
import logging
from datetime import datetime
import yaml

# Configure logging
logging.basicConfig(
    filename='system_automation.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def load_config(config_path='config/app_config.yaml'):
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            log_event("Configuration loaded successfully")
            return config
    except FileNotFoundError:
        log_event(f"Config file not found: {config_path}", "ERROR")
        return {}
    except yaml.YAMLError as e:
        log_event(f"Invalid YAML in config file: {str(e)}", "ERROR")
        return {}

def validate_path(path):
    """Verify that a path exists and is accessible"""
    try:
        if os.path.exists(path):
            logging.debug(f"Path validated: {path}")
            return True
        logging.warning(f"Path does not exist: {path}")
        return False
    except Exception as e:
        logging.error(f"Path validation error: {str(e)}", "ERROR")
        return False

def is_path_writable(path):
    """Check if the current user has write permissions for the path"""
    try:
        test_file = os.path.join(path, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return True
    except Exception as e:
        log_event(f"Path write test failed: {str(e)}", "ERROR")
        return False

def log_event(message, level="INFO"):
    """Log events with standardized format"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    
    if level == "DEBUG":
        logging.debug(log_entry)
    elif level == "WARNING":
        logging.warning(log_entry)
    elif level == "ERROR":
        logging.error(log_entry)
    else:
        logging.info(log_entry)

def get_config_value(config, key_path, default=None):
    """Safely retrieve configuration values from YAML config"""
    try:
        parts = key_path.split('.')
        value = config
        for part in parts:
            value = value[part]
        return value
    except (KeyError, TypeError, AttributeError):
        log_event(f"Config error: {key_path} not found in configuration", "ERROR")
        return default
