from flask import render_template, redirect, url_for, flash, Blueprint
from modules.routes.auth import auth
from modules.docker_handle import get_docker_client, is_container_running
from modules.apps import apps as app_configs
from modules.utils import logger, load_app_config, load_user_config
import docker

app_details = Blueprint("app_details", __name__)


@app_details.route('/app/<app_id>')
@auth.login_required
def app_detail(app_id):
    logger.debug(f"Accessing app_detail for app_id: {app_id}")
    app_info = next((app_config for app_config in app_configs if app_config['id'] == app_id), None)
    if not app_info:
        flash(f"App with ID {app_id} not found.", "danger")
        logger.error(f"App not found: {app_id}")
        return redirect(url_for('index'))
    client = get_docker_client()
    if client:
        app_config = load_app_config()
        container_name = f"{app_config['device_name']}-{app_id}"
        app_info['container_name'] = container_name
        try:
            container = client.containers.get(container_name)
            app_info['container_status'] = container.status
            app_info['container_id'] = container.id
        except docker.errors.NotFound:
            app_info['container_status'] = 'not_created'
    else:
        app_info['container_status'] = 'docker_unavailable'
    config = load_user_config()
    app_config = load_app_config()
    app_info['config'] = config.get(app_id, {})
    app_info['is_running'] = is_container_running(app_id)
    app_info['memory_profiles'] = app_config.get("memory_profiles", {})
    app_info['selected_profile'] = app_config.get("app_memory_profiles", {}).get(app_id, "little_memory")
    app_info['is_enabled'] = app_config.get("app_enabled", {}).get(app_id, False)
    logger.debug(f"Rendering app_detail for {app_id} with enabled: {app_info['is_enabled']}")
    return render_template('apps/app_detail.html', app=app_info)