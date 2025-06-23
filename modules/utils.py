import secrets
import platform
import logging
import json
import os
from flask import flash
from modules.apps import apps as app_configs

USER_CONFIG_FILE = "data/user_config.json"
APP_CONFIG_FILE = "data/app_config.json"

logger = logging.getLogger(__name__)
def generate_random_uuid(length):
    return secrets.token_hex(length)

def load_app_config():
    try:
        with open(APP_CONFIG_FILE, 'r') as f:
            config = json.load(f)
        config.setdefault("app_enabled", {})
        config.setdefault("device_name", platform.node())
        for app in app_configs:
            config["app_enabled"].setdefault(app['id'], False)
        return config
    except Exception as e:
        flash(f"Error loading app config: {str(e)}", "danger")
        logging.error(f"Error loading app_config.json: {str(e)}")
        return {
            "memory_profiles": {},
            "app_memory_profiles": {},
            "app_enabled": {app['id']: False for app in app_configs},
            "device_name": platform.node()
        }

def build_environment(app_config_item, config_data):
    env = {}
    for env_var, value in app_config_item.get('environment_map', {}).items():
        if '{' in value:
            for field in app_config_item.get('config_fields', []):
                placeholder = '{' + field + '}'
                if placeholder in value:
                    value = value.replace(placeholder, config_data.get(field, ''))
            env[env_var] = value
        else:
            env[env_var] = config_data.get(value, '')
    return env

def get_system_info():
    os_type = platform.system()
    machine = platform.machine().lower()
    arch_map = {
        'x86_64': 'amd64',
        'amd64': 'amd64',
        'aarch64': 'arm64',
        'arm64': 'arm64'
    }
    architecture = arch_map.get(machine, 'amd64')
    app_config = load_app_config()
    device_name = app_config.get('device_name', platform.node())
    return {
        'os_type': os_type,
        'architecture': architecture,
        'device_name': device_name
    }

def load_user_config():
    try:
        if os.path.exists(USER_CONFIG_FILE):
            with open(USER_CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        flash(f"Error loading user config: {str(e)}", "danger")
        logging.error(f"Error loading user_config.json: {str(e)}")
        return {}

def save_user_config(config):
    try:
        with open(USER_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        logging.info("Saved user_config.json successfully")
    except Exception as e:
        flash(f"Error saving user config: {str(e)}", "danger")
        logging.error(f"Error saving user_config.json: {str(e)}")

def save_app_config_to_file(config):
    try:
        with open(APP_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        logging.info("Saved app_config.json successfully")
    except Exception as e:
        flash(f"Error saving app config: {str(e)}", "danger")
        logging.error(f"Error saving app_config.json: {str(e)}")

def get_memory_limit_bytes(app_id):
    app_config = load_app_config()
    profile_id = app_config.get("app_memory_profiles", {}).get(app_id, "little_memory")
    profile = app_config.get("memory_profiles", {}).get(profile_id, {"limit_mb": 100})
    return profile["limit_mb"] * 1024 * 1024