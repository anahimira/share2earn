import os
import logging
import json

from modules.apps import apps as app_configs

logger = logging.getLogger(__name__)

USER_CONFIG_FILE = "data/user_config.json"
APP_CONFIG_FILE = "data/app_config.json"

os.makedirs("data", exist_ok=True)

with open("dashboard_config.json", "r") as f:
    config = json.load(f)

def start_up():
    if not os.path.exists(APP_CONFIG_FILE):
        default_config = {
            "memory_profiles": {
                "little_memory": {"name": "Little Memory", "limit_mb": 100},
                "medium_memory": {"name": "Medium Memory", "limit_mb": 300},
                "high_memory": {"name": "High Memory", "limit_mb": 500}
            },
            "app_memory_profiles": {},
            "app_enabled": {app['id']: False for app in app_configs},
            "proxy_app_enabled": {app['id']: False for app in app_configs if app.get('supports_proxy', False)}
        }
        try:
            with open(APP_CONFIG_FILE, 'w') as f:
                json.dump(default_config, f, indent=4)
            logger.info("Initialized app_config.json with default profiles and app states")
        except Exception as e:
            logger.error(f"Failed to initialize app_config.json: {str(e)}")

    for app_config in app_configs:
        if 'volume_mounts' in app_config:
            for mount in app_config['volume_mounts']:
                parts = mount.split(':')
                if len(parts) == 2:
                    host_path, _ = parts
                    absolute_host_path = os.path.abspath(host_path)
                    os.makedirs(absolute_host_path, exist_ok=True)