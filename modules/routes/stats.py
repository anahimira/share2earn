import time, psutil
from flask import flash, Blueprint, jsonify, render_template
from modules.utils import logger
from modules.routes.auth import auth

stats_bp = Blueprint('stats', __name__)

network_history = []
last_network_sample_time = 0
NETWORK_SAMPLE_INTERVAL = 5
NETWORK_HISTORY_SIZE = 6

@stats_bp.route('/stats')
@auth.login_required
def stats():
    return render_template('stats.html')

@stats_bp.route('/api/stats')
@auth.login_required
def api_stats():
    global network_history, last_network_sample_time

    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        memory_used = round(mem.used / (1024 ** 3), 2)
        memory_total = round(mem.total / (1024 ** 3), 2)
        memory_percent = mem.percent

        net_io = psutil.net_io_counters()
        bytes_sent = net_io.bytes_sent
        bytes_recv = net_io.bytes_recv

        current_time = time.time()
        if current_time - last_network_sample_time >= NETWORK_SAMPLE_INTERVAL:
            if len(network_history) >= NETWORK_HISTORY_SIZE:
                network_history.pop(0)
            network_history.append({
                'timestamp': current_time,
                'bytes_sent': bytes_sent,
                'bytes_recv': bytes_recv
            })
            last_network_sample_time = current_time

        network_rates = []
        for i in range(1, len(network_history)):
            time_diff = network_history[i]['timestamp'] - network_history[i - 1]['timestamp']
            sent_diff = (network_history[i]['bytes_sent'] - network_history[i - 1]['bytes_sent']) / 1024 / time_diff
            recv_diff = (network_history[i]['bytes_recv'] - network_history[i - 1]['bytes_recv']) / 1024 / time_diff
            network_rates.append({
                'timestamp': network_history[i]['timestamp'],
                'upload_rate': round(sent_diff, 2),
                'download_rate': round(recv_diff, 2)
            })

        return jsonify({
            'cpu_percent': cpu_percent,
            'memory_used': memory_used,
            'memory_total': memory_total,
            'memory_percent': memory_percent,
            'network_sent': bytes_sent,
            'network_received': bytes_recv,
            'network_rates': network_rates
        })
    except Exception as e:
        flash(f"Error retrieving system stats: {str(e)}", "danger")
        logger.error(f"Error retrieving system stats: {str(e)}")
        return jsonify({
            'cpu_percent': 0,
            'memory_used': 0,
            'memory_total': 0,
            'memory_percent': 0,
            'network_sent': 0,
            'network_received': 0,
            'network_rates': []
        })