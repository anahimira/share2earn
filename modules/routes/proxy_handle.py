from modules.docker_handle import *
from docker.errors import ImageNotFound
from modules.utils import *
from modules.routes.auth import auth
from flask import Response, request, Blueprint, redirect, url_for
import re

proxy_handle_bp = Blueprint("proxy_handle", __name__)

@proxy_handle_bp.route('/stop_all_proxy_apps')
@auth.login_required
def stop_all_proxy_apps():
    client = get_docker_client()
    if client is None:
        flash("Docker is not installed or the daemon is not running. Please install Docker.", "danger")
        return redirect(url_for('install_docker.install_docker'))

    app_config_data = load_app_config()
    device_name = app_config_data.get('device_name', 'vanhbaka')
    user_config = load_user_config()
    proxies = user_config.get('proxies', [])
    proxy_apps = [app for app in app_configs if
                  app.get('supports_proxy', False) and app_config_data.get('proxy_app_enabled', {}).get(app['id'],
                                                                                                        False)]

    stopped_count = 0
    for app in proxy_apps:
        app_id = app['id']
        for proxy in proxies:
            sanitized_proxy = re.sub(r'[^a-zA-Z0-9_.-]', '_',
                                     proxy.replace('://', '_').replace('/', '_').replace(':', '_'))
            if not sanitized_proxy[0].isalnum():
                sanitized_proxy = 'tun' + sanitized_proxy
            sanitized_proxy = sanitized_proxy[:50]
            container_name = f"{device_name}-{app_id}_{sanitized_proxy}"
            try:
                container = client.containers.get(container_name)
                if container.status == 'running':
                    container.stop()
                    stopped_count += 1
                    logging.info(f"Stopped proxy container: {container_name}")
            except docker.errors.NotFound:
                continue  # Container doesn't exist, skip silently
            except Exception as e:
                logging.error(f"Error stopping proxy container {container_name}: {str(e)}")
                flash(f"Error stopping proxy container {container_name}: {str(e)}", "danger")

    if stopped_count > 0:
        flash(f"Stopped {stopped_count} proxy app containers.", "success")
    else:
        flash("No running proxy app containers found.", "info")

    return redirect(url_for('proxy.run_proxy'))

@proxy_handle_bp.route('/stop_all_tun_containers', endpoint="stop_all_tun_containers")
@auth.login_required
def stop_all_tun_containers():
    def generate():
        client = get_docker_client()
        if client is None:
            yield "Docker is not installed or the daemon is not running. Please install Docker.\n"
            return

        containers = client.containers.list(all=True, filters={'name': '^tun_'})
        yield f"Found {len(containers)} tun containers to stop.\n"

        for container in containers:
            try:
                if container.status == 'running':
                    container.stop()
                    yield f"Stopped container {container.name}.\n"
                else:
                    yield f"Container {container.name} is not running.\n"
            except Exception as e:
                yield f"Error stopping container {container.name}: {str(e)}\n"

        yield "All tun containers have been processed.\n"

    return Response(generate(), mimetype='text/plain')


@proxy_handle_bp.route('/run_all_tun_containers', endpoint="run_all_tun_containers")
@auth.login_required
def run_all_tun_containers():
    proxy_handler = request.args.get('proxy_handler')
    if not proxy_handler or proxy_handler not in ['tun2socks', 'tun2proxy']:
        return "Invalid or missing proxy handler.", 400

    def generate():
        user_config = load_user_config()
        online_proxies = [p for p in user_config.get('proxies', []) if
                          user_config.get('proxy_metadata', {}).get(p, {}).get('status') == 'online']
        yield f"Found {len(online_proxies)} online proxies.\n"

        client = get_docker_client()
        if client is None:
            yield "Docker is not installed or the daemon is not running. Please install Docker.\n"
            return

        for proxy in online_proxies:
            yield f"Processing proxy: {proxy}\n"
            if proxy_handler == "tun2socks":
                image = "ghcr.io/xjasonlyu/tun2socks:latest"
                env = {"PROXY": proxy,
                       "EXTRA_COMMANDS": "ip rule add iif lo ipproto udp dport 53 lookup main;"}
                cmd = None
            else:
                image = "ghcr.io/tun2proxy/tun2proxy:v0.7.10"
                env = {}
                cmd = [
                    f"--proxy {proxy} --dns virtual --sysctl net.ipv6.conf.default.disable_ipv6=0"
                ]

            try:
                client.images.get(image)
            except ImageNotFound:
                yield f"Pulling image {image} for {proxy_handler}...\n"
                client.images.pull(image)
                yield "Image pulled successfully.\n"

            sanitized_proxy = re.sub(r'[^a-zA-Z0-9_.-]', '_',
                                     proxy.replace('://', '_').replace('/', '_').replace(':', '_'))
            if not sanitized_proxy[0].isalnum():
                sanitized_proxy = 'tun' + sanitized_proxy
            sanitized_proxy = sanitized_proxy[:50]
            tun_container_name = f"tun_{sanitized_proxy}"

            try:
                container = client.containers.get(tun_container_name)
                if container.status == 'running':
                    yield f"Tun container for proxy {proxy} is already running.\n"
                    continue
                else:
                    yield f"Removing stopped container {tun_container_name}...\n"
                    container.remove()
            except docker.errors.NotFound:
                pass

            try:
                client.containers.run(
                    image,
                    name=tun_container_name,
                    detach=True,
                    cap_add=["NET_ADMIN"],
                    volumes={"/dev/net/tun": {"bind": "/dev/net/tun", "mode": "rw"},
                             "/etc/resolv.conf": {"bind": "/etc/resolv.conf", "mode": "ro"}},
                    environment=env,
                    command=cmd,
                    network_mode="bridge",
                    dns=[
                        "1.1.1.1",
                        "8.8.8.8",
                        "1.0.0.1",
                        "8.8.4.4"
                    ]
                )
                yield f"Started tun container for proxy {proxy}.\n"
            except Exception as e:
                yield f"Failed to start tun container for proxy {proxy}: {str(e)}\n"

        yield "All tun containers have been processed.\n"

    return Response(generate(), mimetype='text/plain')
def run_proxy_container(app, tun_container_name, container_name, user_config, app_config, global_settings):
    client = get_docker_client()
    if client is None:
        yield "Docker is not available.\n"
        return

    yield f"Preparing to run {app['name']} for proxy...\n"

    # Check if container exists
    try:
        container = client.containers.get(container_name)
        yield f"Container {container_name} already exists.\n"
        if container.status == 'running':
            yield f"Stopping container {container_name}...\n"
            container.stop()
        yield f"Removing container {container_name}...\n"
        container.remove()
    except docker.errors.NotFound:
        pass
    except Exception as e:
        yield f"Error handling existing container: {str(e)}\n"
        return
    # Prepare run parameters
    run_params = {}
    app_id = app['id']
    app_data = user_config.get(app_id, {})
    command_str = None

    # Build command
    if 'command' in app:
        run_params['command'] = app['command'].split()
    elif app.get('config_type') == "command" and 'command_template' in app:
        command_str1 = app['command_template']
        for field in app.get('config_fields', []):
            command_str1 = command_str1.replace('{' + field + '}', app_data.get(field, ''))
        command_str = command_str1
        run_params['command'] = command_str1.split()

    # Environment variables
    if 'environment_map' in app:
        run_params['environment'] = build_environment(app, app_data)

    if 'auto_set_cmd' in app:
        cmd_str = command_str
        for field in app['auto_set_cmd']:
            cmd_str = cmd_str.replace('{' + field + '}',
                                        container_name + str(generate_random_uuid(8)))
        run_params['command'] = cmd_str

    # Volumes
    if 'volume_mounts' in app:
        volumes = {}
        for mount in app['volume_mounts']:
            parts = mount.split(':')
            if len(parts) == 2:
                host_path, container_path = parts
                volumes[os.path.abspath(host_path)] = {'bind': container_path, 'mode': 'rw'}
        run_params['volumes'] = volumes

    # Capabilities
    if 'capabilities' in app:
        run_params['cap_add'] = app['capabilities']

    # Resource limits
    profile_id = app_config.get("app_memory_profiles", {}).get(app_id, "little_memory")
    profile = app_config.get("memory_profiles", {}).get(profile_id, {"limit_mb": 100})
    run_params['mem_limit'] = profile["limit_mb"] * 1024 * 1024

    if 'cpu_limit' in global_settings:
        run_params['nano_cpus'] = int(global_settings['cpu_limit'] * 1e9)
    if 'memory_reservation' in global_settings:
        run_params['mem_reservation'] = f"{global_settings['memory_reservation']}m"
    run_params['log_config'] = (
        {'type': 'json-file', 'config': {'max-size': '100k'}}
        if global_settings.get('enable_logs', False)
        else {'type': 'none'}
    )
    run_params['restart_policy'] = {'Name': app.get('restart_policy', 'always')}

    # Set network to the tun container
    run_params['network'] = f"container:{tun_container_name}"

    # Check and pull image
    try:
        client.images.get(app['docker_image'])
    except ImageNotFound:
        yield f"Pulling image for {app['name']}...\n"
        try:
            client.images.pull(app['docker_image'], platform="linux/amd64")
            yield "Image pulled successfully.\n"
        except Exception as e:
            yield f"Error pulling image: {str(e)}\n"
            return

    # Run the container
    logger.debug(run_params)
    try:
        client.containers.run(
            app['docker_image'],
            name=container_name,
            detach=True,
            **run_params
        )
        yield f"Successfully started {app['name']} for proxy.\n"
    except Exception as e:
        yield f"Error starting container: {str(e)}\n"


@proxy_handle_bp.route('/run_all_proxies_container', methods=['POST'], endpoint="run_all_proxies_container")
@auth.login_required
def run_all_proxies_container():
    # Access request.form within the request context
    proxy_handler = request.form.get('proxy_handler')

    # Validate proxy_handler
    if not proxy_handler or proxy_handler not in ['tun2socks', 'tun2proxy']:
        flash("Invalid or missing proxy handler. Please select tun2socks or tun2proxy.", "danger")
        return redirect(url_for('run_proxy'))

    def generate():
        user_config = load_user_config()
        online_proxies = [p for p in user_config.get('proxies', []) if
                          user_config.get('proxy_metadata', {}).get(p, {}).get('status') == 'online']
        yield f"Found {len(online_proxies)} online proxies.\n"

        app_config = load_app_config()
        proxy_apps = [app for app in app_configs if app.get('supports_proxy', False)]
        enabled_proxy_apps = [app for app in proxy_apps if
                              app_config.get('proxy_app_enabled', {}).get(app['id'], False)]
        yield f"Found {len(enabled_proxy_apps)} enabled proxy apps.\n"

        client = get_docker_client()
        if client is None:
            yield "Docker is not installed or the daemon is not running. Please install Docker.\n"
            return

        global_settings = user_config.get('global_settings', {})
        for proxy in online_proxies:
            yield f"Processing proxy: {proxy}\n"
            if proxy_handler == "tun2socks":
                image = "ghcr.io/xjasonlyu/tun2socks:latest"
                env = {"PROXY": proxy,
                       "EXTRA_COMMANDS": "ip rule add iif lo ipproto udp dport 53 lookup main;"}
                cmd = None
            else:
                image = "ghcr.io/tun2proxy/tun2proxy:v0.7.10"
                env = {}
                cmd = [
                    f"--proxy {proxy} --dns virtual --sysctl net.ipv6.conf.default.disable_ipv6=0"
                ]

            try:
                client.images.get(image)
            except ImageNotFound:
                yield f"Pulling image {image} for {proxy_handler}...\n"
                client.images.pull(image)
                yield "Image pulled successfully.\n"

            sanitized_proxy = re.sub(r'[^a-zA-Z0-9_.-]', '_',
                                     proxy.replace('://', '_').replace('/', '_').replace(':', '_'))
            if not sanitized_proxy[0].isalnum():
                sanitized_proxy = 'tun' + sanitized_proxy
            sanitized_proxy = sanitized_proxy[:50]
            tun_container_name = f"tun_{sanitized_proxy}"
            try:
                client.containers.run(
                    image,
                    name=tun_container_name,
                    detach=True,
                    cap_add=["NET_ADMIN"],
                    volumes={"/dev/net/tun": {"bind": "/dev/net/tun", "mode": "rw"},
                             "/etc/resolv.conf": {"bind": "/etc/resolv.conf", "mode": "ro"}},
                    environment=env,
                    command=cmd,
                    network_mode="bridge",
                    dns=[
                        "1.1.1.1",
                        "8.8.8.8",
                        "1.0.0.1",
                        "8.8.4.4"
                    ]
                )
                yield f"Started tun container for proxy {proxy}.\n"
            except Exception as e:
                yield f"Failed to start tun container for proxy {proxy}: {str(e)}\n"
                continue

            for app in enabled_proxy_apps:
                app_container_name = f"{app_config['device_name']}-{app['id']}_{sanitized_proxy}"
                try:
                    for message in run_proxy_container(app, tun_container_name, app_container_name, user_config,
                                                       app_config, global_settings):
                        yield message
                    yield f"Started app {app['name']} for proxy {proxy}.\n"
                except Exception as e:
                    yield f"Failed to start app {app['name']} for proxy {proxy}: {str(e)}\n"

        yield "All enabled proxy apps have been processed.\n"

    return Response(generate(), mimetype='text/plain')