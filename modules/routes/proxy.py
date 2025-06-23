from modules.utils import *
from modules.docker_handle import *
from modules.routes.auth import auth
from flask import render_template, redirect, url_for, flash, Blueprint, request, jsonify
from datetime import datetime, timedelta
from modules.proxy_handle import run_check_proxies, check_proxy_live
import re

proxy_bp = Blueprint('proxy', __name__)


@proxy_bp.route('/proxy_app/<app_id>')
@auth.login_required
def proxy_app_detail(app_id):
    logging.debug(f"Accessing proxy_app_detail for app_id: {app_id}")
    app_info = next((app_config for app_config in app_configs if app_config['id'] == app_id), None)
    if not app_info:
        flash(f"App with ID {app_id} not found.", "danger")
        logging.error(f"App not found: {app_id}")
        return redirect(url_for('run_proxy'))

    client = get_docker_client()
    user_config = load_user_config()
    app_config = load_app_config()
    proxies = user_config.get('proxies', [])
    proxy_metadata = user_config.get('proxy_metadata', {})

    # Prepare proxy container data
    proxy_containers = []
    selected_container = None
    selected_proxy = request.args.get('proxy', None)

    for proxy in proxies:
        sanitized_proxy = re.sub(r'[^a-zA-Z0-9_.-]', '_', proxy.replace('://', '_').replace('/', '_').replace(':', '_'))
        if not sanitized_proxy[0].isalnum():
            sanitized_proxy = 'tun' + sanitized_proxy
        sanitized_proxy = sanitized_proxy[:50]
        container_name = f"{app_config['device_name']}-{app_id}_{sanitized_proxy}"
        status = 'not_created'
        container_id = None
        try:
            container = client.containers.get(container_name)
            status = container.status
            container_id = container.id
            if selected_proxy == proxy:
                selected_container = {
                    'proxy': proxy,
                    'status': status,
                    'container_id': container_id,
                    'container_name': container_name
                }
        except docker.errors.NotFound:
            if selected_proxy == proxy:
                selected_container = {
                    'proxy': proxy,
                    'status': 'not_created',
                    'container_id': None,
                    'container_name': container_name
                }

        proxy_containers.append({
            'proxy': proxy,
            'status': proxy_metadata.get(proxy, {}).get('status', 'checking'),
            'container_name': container_name,
            'container_status': status,
            'container_id': container_id
        })

    if client:
        app_info['container_name'] = f"{app_config['device_name']}-{app_id}"  # Base container name
        app_info['container_status'] = 'not_created'
        try:
            container = client.containers.get(app_info['container_name'])
            app_info['container_status'] = container.status
            app_info['container_id'] = container.id
        except docker.errors.NotFound:
            pass
    else:
        app_info['container_status'] = 'docker_unavailable'

    app_info['config'] = user_config.get(app_id, {})
    app_info['is_running'] = is_proxy_container_running(app_id)
    app_info['memory_profiles'] = app_config.get("memory_profiles", {})
    app_info['selected_profile'] = app_config.get("app_memory_profiles", {}).get(app_id, "little_memory")
    app_info['is_enabled'] = app_config.get("proxy_app_enabled", {}).get(app_id, False)
    app_info['proxy_containers'] = proxy_containers
    app_info['selected_container'] = selected_container
    selected_container = next((pc for pc in proxy_containers if pc.get("proxy") == selected_proxy), None)

    logging.debug(f"Rendering proxy_app_detail for {app_id} with enabled: {app_info['is_enabled']}")
    return render_template('apps/proxy_app_detail.html', app=app_info, proxy_containers=proxy_containers,
                           selected_proxy=selected_proxy, selected_container=selected_container)


@proxy_bp.route('/check_proxy/<path:proxy_address>', methods=['GET'], endpoint="check_proxy")
@auth.login_required
def check_proxy(proxy_address):
    user_config = load_user_config()
    proxies = user_config.get('proxies', [])
    if proxy_address not in proxies:
        return jsonify({'success': False, 'error': 'Proxy not found'}), 404
    timeout = user_config.get('proxy_check_timeout', 5)
    status = check_proxy_live(proxy_address, timeout)  # Assumes check_proxy() exists
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    proxy_metadata = user_config.get('proxy_metadata', {})
    proxy_metadata[proxy_address] = {
        'status': status,
        'last_checked': now
    }
    user_config['proxy_metadata'] = proxy_metadata
    save_user_config(user_config)
    return jsonify({'success': True, 'status': status, 'last_checked': now})

@proxy_bp.route('/remove_offline_proxies', methods=['POST'], endpoint="remove_offline_proxies")
@auth.login_required
def remove_offline_proxies():
    user_config = load_user_config()
    proxies = user_config.get('proxies', [])
    proxy_metadata = user_config.get('proxy_metadata', {})
    offline_proxies = [proxy for proxy in proxies if proxy_metadata.get(proxy, {}).get('status') == 'offline']
    removed_count = 0
    for proxy in offline_proxies:
        if proxy in proxies:
            proxies.remove(proxy)
            removed_count += 1
        if proxy in proxy_metadata:
            del proxy_metadata[proxy]
    user_config['proxies'] = proxies
    user_config['proxy_metadata'] = proxy_metadata
    save_user_config(user_config)
    if removed_count > 0:
        flash(f'Successfully removed {removed_count} offline proxies.', 'success')
    else:
        flash('No offline proxies were removed.', 'info')
    return redirect(url_for('proxy.proxy_page'))

@proxy_bp.route('/set_proxy_timeout', methods=['POST'])
@auth.login_required
def set_proxy_timeout():
    timeout = request.form.get('timeout')
    try:
        timeout = int(timeout)
        if timeout < 1 or timeout > 60:
            flash("Timeout must be between 1 and 60 seconds.", "danger")
        else:
            user_config = load_user_config()
            user_config['proxy_check_timeout'] = timeout
            save_user_config(user_config)
            flash("Proxy check timeout set successfully!", "success")
    except ValueError:
        flash("Invalid timeout value.", "danger")
    return redirect(url_for('proxy.proxy_page'))

@proxy_bp.route('/remove_proxy', methods=['POST'])
@auth.login_required
def remove_proxy():
    proxy_address = request.form.get('proxy_address')
    if not proxy_address:
        flash('No proxy address provided.', 'danger')
        return redirect(url_for('proxy.proxy_page'))

    user_config = load_user_config()
    proxies = user_config.get('proxies', [])
    proxies_meta_data = user_config.get('proxy_metadata', [])
    if proxy_address in proxies:
        proxies.remove(proxy_address)
        del proxies_meta_data[proxy_address]
        user_config['proxies'] = proxies
        user_config['proxy_metadata'] = proxies_meta_data
        save_user_config(user_config)
        flash('Proxy removed successfully!', 'success')
    else:
        flash('Proxy not found.', 'danger')

    return redirect(url_for('proxy.proxy_page'))

@proxy_bp.route('/check_proxies', methods=['GET'], endpoint="check_proxies")
@auth.login_required
def check_proxies_route():
    user_config = load_user_config()
    proxies = user_config.get('proxies', [])
    proxy_metadata = user_config.get('proxy_metadata', {})
    timeout = user_config.get('proxy_check_timeout', 5)
    now = datetime.now()
    to_check = []

    for proxy in proxies:
        metadata = proxy_metadata.get(proxy, {'status': 'checking', 'last_checked': None})
        last_checked_str = metadata['last_checked']
        if last_checked_str:
            try:
                last_checked = datetime.strptime(last_checked_str, '%Y-%m-%d %H:%M:%S')
                if now - last_checked > timedelta(minutes=30):
                    to_check.append(proxy)
            except ValueError:
                to_check.append(proxy)
        else:
            to_check.append(proxy)

    if to_check:
        statuses = run_check_proxies(to_check, timeout)
        status_dict = dict(zip(to_check, statuses))
        for proxy in to_check:
            proxy_metadata[proxy] = {
                'status': status_dict.get(proxy, 'offline'),
                'last_checked': now.strftime('%Y-%m-%d %H:%M:%S')
            }

    user_config['proxy_metadata'] = proxy_metadata
    save_user_config(user_config)

    proxy_data = [
        {
            'address': proxy,
            'status': proxy_metadata.get(proxy, {'status': 'checking'})['status'],
            'last_checked': proxy_metadata.get(proxy, {'last_checked': 'N/A'})['last_checked'] or 'N/A'
        }
        for proxy in proxies
    ]
    return jsonify(proxy_data)

@proxy_bp.route('/proxy', methods=['GET', 'POST'])
@auth.login_required
def proxy_page():
    if request.method == 'POST':
        proxies_text = request.form.get('proxies', '')
        new_proxies = [p.strip() for p in proxies_text.split('\n') if p.strip()]
        user_config = load_user_config()
        existing_proxies = user_config.get('proxies', [])
        for proxy in new_proxies:
            if proxy not in existing_proxies:
                existing_proxies.append(proxy)
        user_config['proxies'] = existing_proxies
        save_user_config(user_config)
        flash('Proxies added successfully!', 'success')
        return redirect(url_for('proxy.proxy_page'))
    else:
        user_config = load_user_config()
        proxies = user_config.get('proxies', [])
        proxy_metadata = user_config.get('proxy_metadata', {})
        timeout = user_config.get('proxy_check_timeout', 5)

        # Pagination parameters
        per_page_options = [10, 20, 50, 100]
        per_page = request.args.get('per_page', default=10, type=int)
        if per_page not in per_page_options:
            per_page = 10
        page = request.args.get('page', default=1, type=int)

        # Calculate pagination
        total_proxies = len(proxies)
        total_pages = (total_proxies + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        paginated_proxies = proxies[start:end]

        # Use last known status from proxy_metadata
        proxy_data = []
        for proxy in paginated_proxies:
            metadata = proxy_metadata.get(proxy, {'status': 'checking', 'last_checked': 'N/A'})
            proxy_data.append({
                'address': proxy,
                'status': metadata['status'],
                'last_checked': metadata['last_checked']
            })

        return render_template('proxy.html', proxies=proxy_data, timeout=timeout, page=page, total_pages=total_pages,
                               per_page=per_page, per_page_options=per_page_options)

@proxy_bp.route('/run_proxy')
@auth.login_required
def run_proxy():
    client = get_docker_client()
    if client is None:
        flash("Docker is not installed or the daemon is not running. Please install Docker.", "danger")
        return redirect(url_for('install_docker'))
    config = load_user_config()
    app_config = load_app_config()
    system_info = get_system_info()
    proxies = config.get('proxies', None)
    proxy_apps = [app for app in app_configs if app.get('supports_proxy', False)]
    for app_config_item in proxy_apps:
        app_config_item['is_running'] = is_proxy_container_running(app_config_item['id'])
        app_config_item['is_configured'] = all(
            field in config.get(app_config_item['id'], {}) for field in app_config_item.get('config_fields', []))
        app_config_item['is_enabled'] = app_config.get("proxy_app_enabled", {}).get(app_config_item['id'], False)
    logging.debug(f"Rendering run_proxy with apps: {[app['id'] for app in proxy_apps]}")
    return render_template('run_proxy.html', apps=proxy_apps, system_info=system_info, proxies=proxies)
