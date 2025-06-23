from flask import Flask, render_template, redirect, url_for, flash, jsonify, request, Blueprint, Response
from modules.routes.auth import auth
from modules.apps import apps as app_configs
from modules.docker_handle import get_docker_client
from modules.utils import logger, load_app_config, save_app_config_to_file, load_user_config, save_user_config, generate_random_uuid
from docker.errors import APIError

misc = Blueprint('misc', __name__)


@misc.route('/flash_message')
@auth.login_required
def flash_message():
    category = request.args.get('category', 'info')
    message = request.args.get('message', '')
    flash(message, category)
    referer = request.headers.get('Referer', url_for('index.index'))
    return redirect(referer)


@misc.route('/container_logs/<container_id>')
@auth.login_required
def get_container_logs(container_id):
    client = get_docker_client()
    if client is None:
        return jsonify({"success": False, "error": "Docker is not installed or the daemon is not running."}), 500
    try:
        container = client.containers.get(container_id)
        logs = container.logs(tail=250).decode('utf-8')
        return jsonify({"success": True, "logs": logs})
    except APIError as e:
        logger.error(f"APIError caught: {str(e)}")
        if "Not Implemented" in str(e):
            return jsonify({"success": False,
                            "error": "Logging is disabled for this container. Please enable logs in settings and "
                                     "detele this container and run again to apply the change!"}), 403
        else:
            return jsonify({"success": False, "error": f"Error fetching logs: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected exception caught: {type(e).__name__} - {str(e)}")
        if isinstance(e, Response) and e.status_code == 501 and "Not Implemented" in str(e.data):
            return jsonify({"success": False,
                            "error": "Logging is disabled for this container. Please enable logs in settings and "
                                     "detele this container and run again to apply the change!"}), 403
        return jsonify({"success": False, "error": f"Error fetching logs: {str(e)}"}), 500


@misc.route('/update_device_name', methods=['POST'], endpoint="update_device_name")
@auth.login_required
def update_device_name():
    new_device_name = request.form.get('device_name', '').strip()
    if not new_device_name:
        flash("Device name cannot be empty.", "danger")
        return redirect(url_for('index.index'))

    app_config = load_app_config()
    app_config['device_name'] = new_device_name
    save_app_config_to_file(app_config)
    flash("Device name updated successfully!", "success")
    return redirect(url_for('index.index'))

@misc.route('/save_app_config', methods=['POST'])
@auth.login_required
def save_app_config():
    logger.debug(f"Saving config with form data: {request.form}")
    app_id = request.form.get('app_id')
    if not app_id:
        flash("App ID not provided.", "danger")
        logger.error("App ID not provided in form data")
        return redirect(url_for('index.index'))

    app_info = next((app_config for app_config in app_configs if app_config['id'] == app_id), None)
    if not app_info:
        flash(f"App with ID {app_id} not found.", "danger")
        logger.error(f"App not found in save_app_config: {app_id}")
        return redirect(url_for('index.index'))

    user_config = load_user_config()
    app_config = load_app_config()

    # Handle sub-apps
    if 'sub_apps' in app_info:
        sub_app_id = request.form.get('sub_app_id')
        sub_app = next((sa for sa in app_info['sub_apps'] if sa['id'] == sub_app_id), None)
        if not sub_app:
            flash(f"Sub-app with ID {sub_app_id} not found.", "danger")
            logger.error(f"Sub-app not found: {sub_app_id}")
            return redirect(url_for('app_details.app_detail', app_id=app_id))

        user_config.setdefault(app_id, {}).setdefault(sub_app_id, {})
        for field in sub_app['config_fields']:
            value = request.form.get(field, '')
            user_config[app_id][sub_app_id][field] = value
            logger.debug(f"Saving {field} for {app_id}/{sub_app_id}: {value}")
    else:
        # Save user config fields for non-sub-app cases
        if 'config_fields' in app_info:
            user_config[app_id] = user_config.get(app_id, {})
            for field in app_info['config_fields']:
                value = request.form.get(field, '')
                user_config[app_id][field] = value
                logger.debug(f"Saving {field} for {app_id}: {value}")

    save_user_config(user_config)

    # Save memory profile
    memory_profile = request.form.get('memory_profile', 'little_memory')
    if memory_profile in app_config.get("memory_profiles", {}):
        app_config.setdefault("app_memory_profiles", {})[app_id] = memory_profile
        logger.debug(f"Saving memory profile for {app_id}: {memory_profile}")

    # Save enabled state
    enabled = request.form.get('enabled', 'off') == 'on'
    app_config.setdefault("app_enabled", {})[app_id] = enabled
    if app_info.get('supports_proxy', False):
        app_config.setdefault("proxy_app_enabled", {})[app_id] = request.form.get('proxy_enabled', 'off') == 'on'
    logger.debug(f"Saving enabled state for {app_id}: {enabled}")

    save_app_config_to_file(app_config)

    flash(f"Configuration for {app_info['name']} saved successfully!", "success")
    if app_id == 'earnapp':
        uuid = user_config.get(app_id, {}).get('uuid', '')
        if uuid:
            claim_url = f"https://earnapp.com/r/sdk-node-{uuid}"
            flash(f'Visit <a href="{claim_url}" target="_blank">{claim_url}</a> to claim your node.', "info")
    if request.form.get('is_proxy_app') == 'True':
        return redirect(url_for('proxy.proxy_app_detail', app_id=app_id))
    else:
        return redirect(url_for('app_details.app_detail', app_id=app_id))

@misc.route('/generate_uuid/<app_id>')
@auth.login_required
def generate_uuid(app_id):
    if app_id != 'earnapp' and app_id != "proxyrack":
        flash("UUID generation is only available for EarnApp.", "danger")
        logger.warning(f"Invalid UUID generation attempt for {app_id}")
        return redirect(url_for('index.index'))

    if app_id == "earnapp":
        random_uuid = generate_random_uuid(16)
        config = load_user_config()
        config.setdefault('earnapp', {})['uuid'] = random_uuid
        save_user_config(config)
        flash(f"Random UUID generated: {random_uuid}. Replace with a registered UUID for earning.", "success")
        claim_url = f"https://earnapp.com/r/sdk-node-{random_uuid}"
        flash(f'Visit <a href="{claim_url}" target="_blank">{claim_url}</a> to claim your node.', "info")
        return redirect(url_for('app_details.app_detail', app_id='earnapp'))
    elif app_id == "proxyrack":
        random_uuid = generate_random_uuid(32)
        config = load_user_config()
        config.setdefault('proxyrack', {})['uuid'] = random_uuid
        save_user_config(config)
        flash(f"Random UUID generated: {random_uuid}. Use this UUID to add your node in the ProxyRack dashboard.",
              "success")
        return redirect(url_for('app_details.app_detail', app_id='proxyrack'))

@misc.route('/toggle_app/<app_id>')
@auth.login_required
def toggle_app(app_id):
    client = get_docker_client()
    if client is None:
        flash("Docker is not installed or the daemon is not running. Please install Docker.", "danger")
        return redirect(url_for('install_docker.install_docker'))
    logger.debug(f"Toggling app: {app_id}")
    app_info = next((app_config for app_config in app_configs if app_config['id'] == app_id), None)
    if not app_info:
        flash(f"App with ID {app_id} not found.", "danger")
        logger.error(f"App not found in toggle_app: {app_id}")
        return redirect(url_for('index.index'))
    config = load_user_config()
    if 'config_fields' in app_info and (
            app_id not in config or any(field not in config[app_id] for field in app_info['config_fields'])):
        flash(f"Please configure {app_info['name']} before running.", "warning")
        logger.warning(f"Configuration required for {app_id}")
        return redirect(url_for('index.index'))
    try:
        container_name = f"{app_id}-container"
        containers = client.containers.list(all=True, filters={'name': container_name})
        if containers:
            container = containers[0]
            if container.status == 'running':
                container.stop()
                flash(f"Container {app_info['name']} stopped.", "success")
                logger.info(f"Stopped container for {app_id}")
            else:
                flash(f"Container {app_info['name']} is not running.", "warning")
                logger.warning(f"Container not running for {app_id}")
        else:
            flash(f"No container found for {app_info['name']}. Enable and use 'Run All' to start.", "warning")
            logger.warning(f"No container found for {app_id}")
    except Exception as e:
        flash(f"Error toggling container: {str(e)}", "danger")
        logger.error(f"Error toggling container {app_id}: {str(e)}")
    return redirect(url_for('app_details.app_detail', app_id=app_id))
