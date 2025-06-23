from flask import render_template, flash, Blueprint, request, redirect, url_for
from modules.utils import logger, save_app_config_to_file, load_app_config, load_user_config, save_user_config
from modules.routes.auth import auth

settings_bp = Blueprint("settings", __name__)

@settings_bp.route('/settings', methods=['GET', 'POST'])
@auth.login_required
def settings():
    app_config = load_app_config()
    user_config = load_user_config()
    profiles = app_config.get("memory_profiles", {})
    global_settings = user_config.get('global_settings', {})

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            profile_name = request.form.get('profile_name')
            try:
                limit_mb = int(request.form.get('limit_mb'))
                if limit_mb < 50:
                    flash("Memory limit must be at least 50 MB.", "danger")
                elif profile_name:
                    profile_id = profile_name.lower().replace(" ", "_")
                    if profile_id not in profiles:
                        profiles[profile_id] = {"name": profile_name, "limit_mb": limit_mb}
                        app_config["memory_profiles"] = profiles
                        save_app_config_to_file(app_config)
                        flash(f"Profile '{profile_name}' added successfully!", "success")
                        logger.info(f"Added memory profile: {profile_id}")
                    else:
                        flash("Profile name already exists.", "danger")
                else:
                    flash("Profile name is required.", "danger")
            except ValueError:
                flash("Please enter a valid number for the memory limit.", "danger")
        elif action == 'delete':
            profile_id = request.form.get('profile_id')
            if profile_id in ['little_memory', 'medium_memory', 'high_memory']:
                flash("Default profiles cannot be deleted.", "danger")
            elif profile_id in profiles:
                del profiles[profile_id]
                app_config["memory_profiles"] = profiles
                for app_id in app_config.get("app_memory_profiles", {}):
                    if app_config["app_memory_profiles"][app_id] == profile_id:
                        app_config["app_memory_profiles"][app_id] = "little_memory"
                save_app_config_to_file(app_config)
                flash(f"Profile deleted successfully!", "success")
                logger.info(f"Deleted memory profile: {profile_id}")
            else:
                flash("Profile not found.", "danger")

    return render_template('settings.html', profiles=profiles, global_settings=global_settings)

@settings_bp.route('/save_global_settings', methods=['POST'])
@auth.login_required
def save_global_settings():
    user_config = load_user_config()
    global_settings = {}

    cpu_limit = request.form.get('cpu_limit')
    if cpu_limit:
        try:
            global_settings['cpu_limit'] = float(cpu_limit)
        except ValueError:
            flash("Invalid CPU limit value.", "danger")
            return redirect(url_for('settings.settings'))

    memory_reservation = request.form.get('memory_reservation')
    if memory_reservation:
        try:
            global_settings['memory_reservation'] = int(memory_reservation)
        except ValueError:
            flash("Invalid memory reservation value.", "danger")
            return redirect(url_for('settings.settings'))

    global_settings['enable_logs'] = request.form.get('enable_logs') == 'on'

    user_config['global_settings'] = global_settings
    save_user_config(user_config)
    flash("Global settings saved successfully!", "success")
    return redirect(url_for('settings.settings'))