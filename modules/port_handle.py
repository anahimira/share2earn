import socket

def is_free_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return True
        except OSError:
            return False

def find_free_port(port):
    while not is_free_port(port):
        port += 1
    return port