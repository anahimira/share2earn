from flask import Flask
import logging
import threading
from init import start_up, config
from modules.auto_restart import auto_restart_loop
from modules.routes import blueprints

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, template_folder='templates', static_folder='templates/static')
app.secret_key = 's2e'

for bp in blueprints:
    app.register_blueprint(bp)

start_up()

if __name__ == '__main__':
    auto_restart_thread = threading.Thread(target=auto_restart_loop, daemon=True)
    auto_restart_thread.start()
    app.run(host='0.0.0.0', port=config['DASHBOARD_PORT'])
