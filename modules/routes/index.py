from flask import render_template, redirect, url_for, flash, Blueprint
from modules.routes.auth import auth
from modules.utils import logger, load_app_config, get_system_info, load_user_config
from modules.apps import apps as app_configs
from modules.docker_handle import get_docker_client, is_container_running

index_page = Blueprint('index', __name__)

@index_page.route('/', endpoint='index')
@auth.login_required
def index():
    client = get_docker_client()
    if client is None:
        flash("Docker is not installed or the daemon is not running. Please install Docker.", "danger")
        return redirect(url_for('install_docker.install_docker'))
    config = load_user_config()
    app_config = load_app_config()
    system_info = get_system_info()
    for app_config_item in app_configs:
        app_config_item['is_running'] = is_container_running(app_config_item['id'])
        app_config_item['is_configured'] = all(
            field in config.get(app_config_item['id'], {}) for field in app_config_item.get('config_fields', []))
        app_config_item['is_enabled'] = app_config.get("app_enabled", {}).get(app_config_item['id'], False)
    logger.debug(f"Rendering index with apps: {[app['id'] for app in app_configs]}")
    return render_template('index.html', apps=app_configs, system_info=system_info)