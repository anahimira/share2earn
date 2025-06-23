from modules.routes.misc import misc
from modules.routes.index import index_page
from modules.routes.auto_restart import auto_restart
from modules.routes.app_details import app_details
from modules.routes.settings import settings_bp
from modules.routes.install_docker import install_docker_bp
from modules.routes.handle import handle_bp
from modules.routes.stats import stats_bp
from modules.routes.manage import manage_bp
from modules.routes.proxy import proxy_bp
from modules.routes.proxy_handle import proxy_handle_bp

blueprints = [proxy_handle_bp, index_page, misc, auto_restart, app_details, settings_bp, install_docker_bp, handle_bp, stats_bp, manage_bp, proxy_bp]