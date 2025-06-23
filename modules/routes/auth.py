from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from init import config

users = {
    config['DASHBOARD_USERNAME']: generate_password_hash(config['DASHBOARD_PASSWORD'])
}

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username