import docker
import time
from docker.errors import APIError
from modules.utils import logger, load_app_config


def get_docker_client(max_retries=3, delay=2):
    """
    Initialize Docker client with retries to handle daemon startup delay.
    Returns client if successful, None if connection fails.
    """
    for attempt in range(max_retries):
        try:
            client = docker.from_env()
            client.ping()  # Verify daemon is running
            logger.debug(f"Successfully connected to Docker daemon on attempt {attempt + 1}")
            return client
        except docker.errors.DockerException as e:
            logger.error(f"Attempt {attempt + 1}/{max_retries} failed to connect to Docker daemon: {str(e)}")
            if "CreateFile" in str(e):
                logger.error("Likely cause: Docker Desktop is not running or not installed on Windows")
            elif "connect" in str(e).lower():
                logger.error("Likely cause: Docker daemon is not accessible (check DOCKER_HOST or named pipe)")
            if attempt < max_retries - 1:
                logger.debug(f"Retrying after {delay} seconds...")
                time.sleep(delay)
    logger.error(f"Failed to connect to Docker daemon after {max_retries} attempts")
    return None

def is_container_running(app_id):
    client = get_docker_client()
    app_config = load_app_config()
    device_name = app_config.get("device_name", "device")
    container_name = f"{device_name}-{app_id}"
    try:
        container = client.containers.get(container_name)
        return container.status == 'running'
    except docker.errors.NotFound:
        return False

def is_container_exits(app_id):
    client = get_docker_client()
    app_config = load_app_config()
    device_name = app_config.get("device_name", "device")
    container_name = f"{device_name}-{app_id}"
    try:
        client.containers.get(container_name)
        return True
    except docker.errors.NotFound:
        return False

def is_proxy_container_running(app_id: str) -> bool:
    client = get_docker_client()
    device_name = load_app_config().get("device_name", "device")

    prefix = f"{device_name}-{app_id}_"

    return bool(
        client.containers.list(
            filters={"name": prefix, "status": "running"},
            limit=1,
        )
    )