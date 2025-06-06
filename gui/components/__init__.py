"""
GUI Components for C2C Botnet Management System
"""

from .sidebar import ModernSidebar
from .dashboard import DashboardWidget
from .bot_management import BotManagementWidget
from .monitoring import MonitoringWidget
from .payload_builder import PayloadBuilderWidget
from .network_scanner import NetworkScannerWidget
from .logs import LogsWidget
from .settings import SettingsWidget

__all__ = [
    "ModernSidebar",
    "DashboardWidget", 
    "BotManagementWidget",
    "MonitoringWidget",
    "PayloadBuilderWidget",
    "NetworkScannerWidget",
    "LogsWidget",
    "SettingsWidget"
]