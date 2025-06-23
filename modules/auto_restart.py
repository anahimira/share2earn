from modules.docker_handle import get_docker_client
from modules.utils import load_app_config
from dateutil import parser
import datetime
import time
import logging

logger = logging.getLogger(__name__)

def auto_restart_loop():
    while True:
        app_config = load_app_config()
        auto_restart_config = app_config.get('auto_restart', {})
        client = get_docker_client()
        if client is None:
            time.sleep(60)
            continue
        for container_name, hours in auto_restart_config.items():
            try:
                container = client.containers.get(container_name)
                if container.status == 'running':
                    started_at_str = container.attrs['State']['StartedAt']
                    started_at = parser.isoparse(started_at_str)
                    now = datetime.datetime.now(datetime.timezone.utc)
                    elapsed_hours = (now - started_at).total_seconds() / 3600
                    if elapsed_hours >= hours:
                        container.restart()
                        logger.info(f"Auto-restarted container {container_name} after {elapsed_hours:.2f} hours")
            except Exception as e:
                logger.error(f"Error auto-restarting container {container_name}: {str(e)}")
        time.sleep(3600)  # Check every hour