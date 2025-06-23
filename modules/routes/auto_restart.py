from flask import jsonify, request, Blueprint
from modules.utils import load_app_config, save_app_config_to_file
from modules.routes.auth import auth

auto_restart = Blueprint('auto_restart', __name__)


@auto_restart.route('/get_auto_restart', methods=['GET'], endpoint="get_auto_restart")
@auth.login_required
def get_auto_restart():
    container_name = request.args.get('container_name')
    if not container_name:
        return jsonify({'hours': None})
    app_config = load_app_config()
    auto_restart_config = app_config.get('auto_restart', {})
    hours = auto_restart_config.get(container_name)
    return jsonify({'hours': hours})


@auto_restart.route('/disable_auto_restart', methods=['POST'], endpoint="disable_auto_restart")
@auth.login_required
def disable_auto_restart():
    data = request.get_json()
    container_name = data.get('container_name')
    if not container_name:
        return jsonify({'success': False, 'error': 'Missing container_name'})
    app_config = load_app_config()
    auto_restart_config = app_config.get('auto_restart', {})
    if container_name in auto_restart_config:
        del auto_restart_config[container_name]
        app_config['auto_restart'] = auto_restart_config
        save_app_config_to_file(app_config)
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'No auto-restart configuration found'})


@auto_restart.route('/save_auto_restart', methods=['POST'], endpoint="save_auto_restart")
@auth.login_required
def save_auto_restart():
    data = request.get_json()
    container_name = data.get('container_name')
    hours = data.get('hours')
    if not container_name or not hours:
        return jsonify({'success': False, 'error': 'Missing container_name or hours'})
    try:
        hours = int(hours)
        if hours < 1:
            raise ValueError
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid hours value'})

    app_config = load_app_config()
    app_config.setdefault('auto_restart', {})[container_name] = hours
    save_app_config_to_file(app_config)
    return jsonify({'success': True})
