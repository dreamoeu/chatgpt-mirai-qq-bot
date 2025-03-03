import os

from im_http_legacy_adapter.adapter import HttpLegacyAdapter, HttpLegacyConfig

from kirara_ai.logger import get_logger
from kirara_ai.plugin_manager.plugin import Plugin
from kirara_ai.web.app import WebServer

logger = get_logger("HTTP-Legacy-Adapter")


class HttpLegacyAdapterPlugin(Plugin):
    """HTTP API 消息适配器插件"""
    web_server: WebServer
    
    def __init__(self):
        pass

    def on_load(self):
        self.im_registry.register("http_legacy", HttpLegacyAdapter, HttpLegacyConfig, "HTTP API", "HTTP 消息 API，可用于接入第三方程序。")
        self.web_server.add_static_assets("/assets/icons/im/http_legacy.svg", os.path.join(os.path.dirname(__file__), "assets", "http_legacy.svg"))

    def on_start(self):
        pass

    def on_stop(self):
        pass
