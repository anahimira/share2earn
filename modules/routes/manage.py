from modules.docker_handle import get_docker_client
from flask import flash, redirect, render_template, Blueprint, url_for
from modules.routes.auth import auth

manage_bp = Blueprint("manage", __name__)

@manage_bp.route('/manage')
@auth.login_required
def manage():
    client = get_docker_client()
    if client is None:
        flash("Docker is not installed or the daemon is not running. Please install Docker.", "danger")
        return redirect(url_for('install_docker'))
    containers = client.containers.list(all=True)
    for container in containers:
        container.is_running = container.status == 'running'
    return render_template('manage_containers.html', containers=containers)