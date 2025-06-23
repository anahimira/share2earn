from modules.utils import logger, get_system_info
import platform, os, tempfile, stat, subprocess
from modules.docker_handle import get_docker_client
from flask import render_template, redirect, url_for, flash, Blueprint, request
from modules.routes.auth import auth


install_docker_bp = Blueprint('install_docker', __name__)

@install_docker_bp.route('/install_docker')
@auth.login_required
def install_docker():
    system_info = get_system_info()
    architecture = system_info['architecture']
    os_type = system_info['os_type'].lower()

    if os_type == 'windows':
        install_instructions = """
            <p>Docker Desktop is required to run Docker on Windows. Please follow these steps:</p>
            <ol>
                <li>Download Docker Desktop from <a href="https://www.docker.com/products/docker-desktop/" target="_blank">Docker's official website</a>.</li>
                <li>Run the installer and follow the prompts to install Docker Desktop.</li>
                <li>Ensure WSL 2 is enabled (Docker Desktop will guide you through this if needed).</li>
                <li>Start Docker Desktop from the Start menu or system tray.</li>
                <li>Verify installation by running <code>docker --version</code> in Command Prompt or PowerShell.</li>
                <li>Ensure Docker Desktop is running before using this dashboard.</li>
            </ol>
            <p>After installing and starting Docker Desktop, refresh this page or return to the dashboard.</p>
        """
        logger.debug(f"Rendering install_docker for Windows with architecture: {architecture}")
        return render_template('install_docker.html', architecture=architecture,
                               install_instructions=install_instructions, is_windows=True)
    else:
        if architecture == 'amd64':
            install_script = """#!/bin/bash
# Install Docker on Ubuntu/Debian for amd64
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
"""
        elif architecture == 'arm64':
            install_script = """#!/bin/bash
# Install Docker on Ubuntu/Debian for arm64
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=arm64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
"""
        else:
            install_script = "# Unsupported architecture. Please install Docker manually following the official documentation: https://docs.docker.com/engine/install/"
            flash(f"Architecture '{architecture}' is not supported for automatic Docker installation.", "danger")

        logger.debug(f"Rendering install_docker for {os_type} with architecture: {architecture}")
        return render_template('install_docker.html', architecture=architecture, install_script=install_script,
                               is_windows=False)

@install_docker_bp.route('/execute_docker_install', methods=['POST'])
@auth.login_required
def execute_docker_install():
    if platform.system().lower() == 'windows':
        flash("Automatic installation is not supported on Windows. Please install Docker Desktop manually.", "danger")
        return redirect(url_for('install_docker.install_docker'))

    install_script = request.form.get('install_script')
    if not install_script or install_script.startswith("# Unsupported"):
        flash("Cannot execute installation: unsupported architecture or invalid script.", "danger")
        return redirect(url_for('install_docker.install_docker'))

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as temp_file:
            temp_file.write(install_script)
            temp_file_path = temp_file.name

        os.chmod(temp_file_path, stat.S_IRWXU)
        result = subprocess.run([temp_file_path], capture_output=True, text=True)
        os.unlink(temp_file_path)

        if result.returncode == 0:
            flash(
                "Docker installation script executed successfully! Please restart the script to apply group changes.",
                "success")
            client = get_docker_client()  # Update client after installation
        else:
            flash(f"Error executing Docker installation script: {result.stderr}", "danger")
            logger.error(f"Docker install error: {result.stderr}")
    except Exception as e:
        flash(f"Error during installation: {str(e)}", "danger")
        logger.error(f"Docker install exception: {str(e)}")

    return redirect(url_for('install_docker.install_docker'))