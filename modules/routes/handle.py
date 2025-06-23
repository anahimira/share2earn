import os
import re

import docker
from docker.errors import ImageNotFound
from flask import Blueprint, Response, flash, redirect, url_for, request

from modules.apps import apps as app_configs
from modules.docker_handle import get_docker_client, is_container_running, is_proxy_container_running
from modules.port_handle import find_free_port
from modules.routes.auth import auth
from modules.utils import logger, load_app_config, load_user_config, build_environment, get_memory_limit_bytes, generate_random_uuid

handle_bp = Blueprint("handle", __name__, url_prefix="/handle")


@handle_bp.route('/run_all', endpoint="run_all")
@auth.login_required
def run_all():
    def run_all_generator():
        client = get_docker_client()
        if client is None:
            yield "Docker is not installed or the daemon is not running. Please install Docker.\n"
            return

        config = load_user_config()
        app_configs_data = load_app_config()
        global_settings = config.get('global_settings', {})
        unconfigured_apps = []

        # Identify unconfigured apps
        for app_config_item in app_configs:
            if 'sub_apps' in app_config_item:
                for sub_app in app_config_item['sub_apps']:
                    if sub_app['config_fields'] and (
                            app_config_item['id'] not in config or
                            sub_app['id'] not in config.get(app_config_item['id'], {}) or
                            any(field not in config[app_config_item['id']][sub_app['id']] for field in
                                sub_app['config_fields'])
                    ):
                        unconfigured_apps.append(f"{app_config_item['name']} - {sub_app['name']}")
            elif 'config_fields' in app_config_item and (
                    app_config_item['id'] not in config or
                    any(field not in config[app_config_item['id']] for field in app_config_item['config_fields'])
            ):
                unconfigured_apps.append(app_config_item['name'])

        # Process each app
        for app_config_item in app_configs:
            app_id = app_config_item['id']
            app_name = app_config_item['name']
            docker_image = app_config_item['docker_image']
            app_config_data = config.get(app_id, {})

            if not app_configs_data.get("app_enabled", {}).get(app_id, False):
                continue  # Skip disabled apps

            if app_name in unconfigured_apps or any(f"{app_name} - " in ua for ua in unconfigured_apps):
                yield f"{app_name} requires configuration. Skipping.\n"
                continue

            if is_container_running(app_id):
                yield f"{app_name} is already running.\n"
                continue

            yield f"Preparing to start {app_name}...\n"

            container_name = f"{app_configs_data['device_name']}-{app_id}"
            try:
                container = client.containers.get(container_name)
                container.restart()
                yield f"{app_name} started successfully."
                continue
            except docker.errors.NotFound:
                pass

            try:
                run_params = {}
                command_str = None
                # Build command
                if 'command' in app_config_item:
                    run_params['command'] = app_config_item['command'].split()
                elif app_config_item.get('config_type') == "command" and 'command_template' in app_config_item:
                    command_str1 = app_config_item['command_template']
                    for field in app_config_item.get('config_fields', []):
                        command_str1 = command_str1.replace('{' + field + '}', app_config_data.get(field, ''))
                    command_str = command_str1
                    run_params['command'] = command_str1.split()

                # Environment variables
                if 'sub_apps' in app_config_item:
                    env = {}
                    for sub_app in app_config_item['sub_apps']:
                        sub_app_id = sub_app['id']
                        if sub_app_id in config.get(app_id, {}):
                            logger.debug(f"Processing sub-app {sub_app_id} for {app_id}")
                            for env_var, config_key in sub_app.get('environment_map', {}).items():
                                value = config[app_id][sub_app_id].get(config_key, '')
                                env[env_var] = value
                                logger.debug(f"Setting env var {env_var}={value} for {sub_app_id}")
                        else:
                            logger.debug(f"No config found for sub-app {sub_app_id} in {app_id}")
                    if not env:
                        logger.warning(f"No environment variables set for {app_id} sub-apps")
                    run_params['environment'] = env
                elif 'environment_map' in app_config_item:
                    run_params['environment'] = build_environment(app_config_item, app_config_data)

                if 'auto_set_cmd' in app_config_item:
                    cmd_str = command_str
                    for field in app_config_item['auto_set_cmd']:
                         cmd_str = cmd_str.replace('{' + field + '}', app_configs_data['device_name'] + str(generate_random_uuid(8)))
                    run_params['command'] = cmd_str.split()

                # Port mappings
                if 'port_mappings' in app_config_item:
                    ports = {}
                    for container_port_str, config_key in app_config_item['port_mappings'].items():
                        host_port = app_config_data.get(config_key)
                        if host_port:
                            ports[int(container_port_str)] = find_free_port(int(host_port))
                        else:
                            ports[int(container_port_str)] = find_free_port(int(config_key))
                    run_params['ports'] = ports

                # Volumes
                if 'volume_mounts' in app_config_item:
                    volumes = {}
                    for mount in app_config_item['volume_mounts']:
                        parts = mount.split(':')
                        if len(parts) == 2:
                            host_path, container_path = parts
                            volumes[os.path.abspath(host_path)] = {'bind': container_path, 'mode': 'rw'}
                    run_params['volumes'] = volumes

                # Capabilities
                if 'capabilities' in app_config_item:
                    run_params['cap_add'] = app_config_item['capabilities']

                # Apply memory limit (max memory) per app
                run_params['mem_limit'] = get_memory_limit_bytes(app_id)

                # Apply global settings
                if 'cpu_limit' in global_settings:
                    run_params['nano_cpus'] = int(global_settings['cpu_limit'] * 1e9)
                if 'memory_reservation' in global_settings:
                    run_params['mem_reservation'] = f"{global_settings['memory_reservation']}m"
                run_params['log_config'] = (
                    {'type': 'json-file', 'config': {'max-size': '100k'}}
                    if global_settings.get('enable_logs', False)
                    else {'type': 'none'}
                )

                run_params['restart_policy'] = {'Name': app_config_item.get('restart_policy', 'always')}

                # Check and pull image if necessary
                try:
                    client.images.get(docker_image)
                except ImageNotFound:
                    yield f"Pulling image for {app_name}...\n"
                    client.images.pull(docker_image, platform="linux/amd64")
                    yield f"Image {docker_image} pulled successfully.\n"

                # Start container
                client.containers.run(
                    docker_image,
                    name=container_name,
                    detach=True,
                    **run_params
                )
                yield f"{app_name} started successfully.\n"
            except Exception as e:
                yield f"Error starting {app_name}: {str(e)}\n"

        yield "All enabled apps have been processed.\n"

    return Response(run_all_generator(), mimetype='text/plain')


@handle_bp.route('/stop_all')
@auth.login_required
def stop_all():
    client = get_docker_client()
    if client is None:
        flash("Docker is not installed or the daemon is not running. Please install Docker.", "danger")
        return redirect(url_for('install_docker.install_docker'))
    app_config_data = load_app_config()
    for app_config in app_configs:
        if is_container_running(app_config['id']):
            try:
                container_name = f"{app_config_data['device_name']}-{app_config['id']}"
                containers = client.containers.list(all=True, filters={'name': container_name})
                if containers:
                    container = containers[0]
                    container.stop()
                    flash(f"Container {app_config['name']} stopped.", "success")
                    logger.info(f"Stopped container for {app_config['id']}")
            except Exception as e:
                flash(f"Error stopping {app_config['name']}: {str(e)}", "danger")
                logger.error(f"Error stopping {app_config['id']}: {str(e)}")
    return redirect(url_for('index.index'))


@handle_bp.route('/restart/<container_id>')
@auth.login_required
def restart(container_id):
    client = get_docker_client()
    if client is None:
        flash("Docker is not installed or the daemon is not running. Please install Docker.", "danger")
        return redirect(url_for('install_docker'))
    try:
        container = client.containers.get(container_id)
        app_config_data = load_app_config()
        device_name = app_config_data.get('device_name', 'vanhbaka')
        # Extract app_id from container name (format: {device_name}-{app_id})
        app_id = container.name.split(f"{device_name}-")[-1] if f"{device_name}-" in container.name else None
        container.restart()
        flash(f"✅ Container '{container.name}' restarted successfully!", "success")
        logger.info(f"Restarted container: {container_id}")
        # Redirect based on request origin
        if request.args.get('_from') == 'manage':
            return redirect(url_for('manage.manage'))
        elif request.args.get('_from') == 'app_detail_proxy':
            app_id = container.name.split(f"{device_name}-")[-1].split('_')[0]
            return redirect(url_for('proxy.proxy_app_detail', app_id=app_id))
        elif app_id and any(app['id'] == app_id for app in app_configs):
            return redirect(url_for('app_details.app_detail', app_id=app_id))
        else:
            flash("Could not determine app ID for redirection.", "warning")
            return redirect(url_for('manage.manage'))
    except Exception as e:
        flash(f"❌ Error restarting container: {str(e)}", "danger")
        logger.error(f"Error restarting container {container_id}: {str(e)}")
        return redirect(url_for('manage.manage'))


@handle_bp.route('/start_app/<app_id>', endpoint="start_app")
@auth.login_required
def start_app(app_id):
    proxy = request.args.get('proxy', None)

    def start_app_generator():
        client = get_docker_client()
        if client is None:
            yield "Docker is not installed or the daemon is not running. Please install Docker.\n"
            return

        app_info = next((app_config for app_config in app_configs if app_config['id'] == app_id), None)
        if not app_info:
            yield f"App with ID {app_id} not found.\n"
            return

        user_config = load_user_config()
        app_config_data = load_app_config()

        if not proxy:
            if not app_config_data.get("app_enabled", {}).get(app_id, False):
                yield f"{app_info['name']} is disabled. Enable it first.\n"
                return
        elif not app_config_data.get("proxy_app_enabled"):
            yield f"{app_info['name']} is disabled. Enable it first.\n"
            return

        if 'config_fields' in app_info and not all(
                field in user_config.get(app_id, {}) for field in app_info['config_fields']):
            yield f"Please configure {app_info['name']} before running.\n"
            return

        container_name = f"{app_config_data['device_name']}-{app_id}"


        if proxy:
            if proxy not in user_config.get('proxies', []):
                yield f"Proxy {proxy} not found in configuration.\n"
                return
            sanitized_proxy = re.sub(r'[^a-zA-Z0-9_.-]', '_',
                                     proxy.replace('://', '_').replace('/', '_').replace(':', '_'))
            if not sanitized_proxy[0].isalnum():
                sanitized_proxy = 'tun' + sanitized_proxy
            sanitized_proxy = sanitized_proxy[:50]
            container_name += f"_{sanitized_proxy}"
            tun_container_name = f"tun_{sanitized_proxy}"
            if not app_info.get('supports_proxy', False):
                yield f"{app_info['name']} does not support proxy configuration.\n"
                return

            try:
                tun_container = client.containers.get(tun_container_name)
                if tun_container.status != "running":
                    yield "Tun container is not running please run it in the proxy apps page!\n"
                    return
            except:
                yield "Tun container is not running please run it in the proxy apps page!\n"
                return

        if proxy:
            if is_proxy_container_running(app_id):
                yield f"{app_info['name']} is already running.\n"
                return
        elif is_container_running(app_id):
            yield f"{app_info['name']} is already running.\n"
            return

        try:
            yield "Checking if container exists...\n"
            try:
                container = client.containers.get(container_name)
                if container.status == 'running':
                    yield f"{app_info['name']} is already running.\n"
                    return
                else:
                    yield "Starting existing container...\n"
                    container.start()
                    yield f"{app_info['name']} started successfully.\n"
                    return
            except docker.errors.NotFound:
                yield "Container not found. Creating new container...\n"

            run_params = {}
            command_str = None

            if 'command' in app_info:
                run_params['command'] = app_info['command'].split()
            elif app_info.get('config_type') == "command" and 'command_template' in app_info:
                command_str1 = app_info['command_template']
                for field in app_info.get('config_fields', []):
                    command_str1 = command_str1.replace('{' + field + '}', user_config.get(app_id, {}).get(field, ''))
                command_str = command_str1
                run_params['command'] = command_str1.split()

            try:
                if 'auto_set_cmd' in app_info:
                    cmd_str = command_str

                    for field in app_info['auto_set_cmd']:
                        cmd_str = cmd_str.replace('{' + field + '}',
                                                  app_config_data['device_name'] + str(generate_random_uuid(8)))
                    run_params['command'] = cmd_str.split()
            except Exception as e:
                print(e)




            if 'sub_apps' in app_info:
                env = {}
                for sub_app in app_info['sub_apps']:
                    sub_app_id = sub_app['id']
                    if sub_app_id in user_config.get(app_id, {}):
                        logger.debug(f"Processing sub-app {sub_app_id} for {app_id}")
                        for env_var, config_key in sub_app.get('environment_map', {}).items():
                            value = user_config[app_id][sub_app_id].get(config_key, '')
                            env[env_var] = value
                            logger.debug(f"Setting env var {env_var}={value} for {sub_app_id}")
                if not env:
                    logger.warning(f"No environment variables set for {app_id} sub-apps")
                run_params['environment'] = env
            elif 'environment_map' in app_info:
                run_params['environment'] = build_environment(app_info, user_config.get(app_id, {}))

            if proxy:
                sanitized_proxy = re.sub(r'[^a-zA-Z0-9_.-]', '_',
                                         proxy.replace('://', '_').replace('/', '_').replace(':', '_'))
                if not sanitized_proxy[0].isalnum():
                    sanitized_proxy = 'tun' + sanitized_proxy
                sanitized_proxy = sanitized_proxy[:50]
                tun_container_name = f"tun_{sanitized_proxy}"
                try:
                    client.containers.get(tun_container_name)
                    run_params['network'] = f"container:{tun_container_name}"
                except docker.errors.NotFound:
                    yield f"Tun container for proxy {proxy} not found. Please run proxy containers first.\n"
                    return

            if 'port_mappings' in app_info and not proxy:
                ports = {}
                for container_port_str, config_key in app_info['port_mappings'].items():
                    host_port = user_config.get(app_id, {}).get(config_key) or config_key
                    ports[int(container_port_str)] = find_free_port(int(host_port))
                run_params['ports'] = ports

            if 'volume_mounts' in app_info:
                volumes = {os.path.abspath(host_path): {'bind': container_path, 'mode': 'rw'}
                           for mount in app_info['volume_mounts']
                           for host_path, container_path in [mount.split(':')]}
                run_params['volumes'] = volumes

            if 'capabilities' in app_info:
                run_params['cap_add'] = app_info['capabilities']

            run_params['mem_limit'] = get_memory_limit_bytes(app_id)
            global_settings = user_config.get('global_settings', {})
            if 'cpu_limit' in global_settings:
                run_params['nano_cpus'] = int(global_settings['cpu_limit'] * 1e9)
            if 'memory_reservation' in global_settings:
                run_params['mem_reservation'] = f"{global_settings['memory_reservation']}m"
            run_params['log_config'] = (
                {'type': 'json-file', 'config': {'max-size': '100k'}}
                if global_settings.get('enable_logs', False)
                else {'type': 'none'}
            )
            run_params['restart_policy'] = {'Name': app_info.get('restart_policy', 'always')}

            try:
                client.images.get(app_info['docker_image'])
            except ImageNotFound:
                yield f"Pulling image for {app_info['name']}...\n"
                client.images.pull(app_info['docker_image'], platform="linux/amd64")
                yield "Image pulled successfully.\n"

            yield "Starting new container...\n"
            client.containers.run(
                app_info['docker_image'],
                name=container_name,
                detach=True,
                **run_params
            )
            yield f"{app_info['name']} started successfully.\n"
        except Exception as e:
            yield f"Error starting {app_info['name']}: {str(e)}\n"

    return Response(start_app_generator(), mimetype='text/plain')

@handle_bp.route('/stop/<container_id>')
@auth.login_required
def stop(container_id):
    client = get_docker_client()
    if client is None:
        flash("Docker is not installed or the daemon is not running. Please install Docker.", "danger")
        return redirect(url_for('install_docker'))
    try:
        container = client.containers.get(container_id)
        app_config_data = load_app_config()
        device_name = app_config_data.get('device_name', 'vanhbaka')
        # Extract app_id from container name (format: {device_name}-{app_id})
        app_id = container.name.split(f"{device_name}-")[-1] if f"{device_name}-" in container.name else None
        if container.status == 'running':
            container.stop()
            flash(f"✅ Container '{container.name}' stopped successfully!", "success")
            logger.info(f"Stopped container: {container_id}")
        else:
            flash(f"Container '{container.name}' is already stopped.", "warning")
            logger.warning(f"Container already stopped: {container_id}")
        # Redirect based on request origin
        if request.args.get('_from') == 'manage':
            return redirect(url_for('manage.manage'))
        elif request.args.get('_from') == 'app_detail_proxy':
            app_id = container.name.split(f"{device_name}-")[-1].split('_')[0]
            return redirect(url_for('proxy.proxy_app_detail', app_id=app_id))
        elif app_id and any(app['id'] == app_id for app in app_configs):
            return redirect(url_for('app_details.app_detail', app_id=app_id))
        else:
            flash("Could not determine app ID for redirection.", "warning")
            return redirect(url_for('manage.manage'))
    except Exception as e:
        flash(f"❌ Error stopping container: {str(e)}", "danger")
        logger.error(f"Error stopping container {container_id}: {str(e)}")
        return redirect(url_for('manage.manage'))

@handle_bp.route('/delete/<container_id>')
@auth.login_required
def delete(container_id):
    client = get_docker_client()
    if client is None:
        flash("Docker is not installed or the daemon is not running. Please install Docker.", "danger")
        return redirect(url_for('install_docker'))
    try:
        container = client.containers.get(container_id)
        app_config_data = load_app_config()
        device_name = app_config_data.get('device_name', 'vanhbaka')
        # Extract app_id from container name (format: {device_name}-{app_id})
        app_id = container.name.split(f"{device_name}-")[-1] if f"{device_name}-" in container.name else None
        if container.status == 'running':
            flash(f"Container '{container.name}' is running. Please stop it before deleting.", "warning")
            logger.warning(f"Attempted to delete running container: {container_id}")
        else:
            container.remove(force=True)
            flash(f"✅ Container '{container.name}' deleted successfully!", "success")
            logger.info(f"Deleted container: {container_id}")
        if request.args.get('_from') == 'manage':
            return redirect(url_for('manage.manage'))
        elif request.args.get('_from') == 'app_detail_proxy':
            app_id = container.name.split(f"{device_name}-")[-1].split('_')[0]
            return redirect(url_for('proxy.proxy_app_detail', app_id=app_id))
        elif app_id and any(app['id'] == app_id for app in app_configs):
            return redirect(url_for('app_details.app_detail', app_id=app_id))
        else:
            flash("Could not determine app ID for redirection.", "warning")
            return redirect(url_for('manage.manage'))
    except Exception as e:
        flash(f"❌ Error deleting container: {str(e)}", "danger")
        logger.error(f"Error deleting container {container_id}: {str(e)}")
    return redirect(url_for('manage.manage'))
