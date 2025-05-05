from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from kirara_ai.config.global_config import GlobalConfig, WebConfig
from kirara_ai.im.manager import IMManager
from kirara_ai.ioc.container import DependencyContainer
from kirara_ai.llm.llm_manager import LLMManager
from kirara_ai.plugin_manager.plugin_loader import PluginLoader
from kirara_ai.web.app import WebServer
from kirara_ai.workflow.core.workflow import WorkflowRegistry
from tests.utils.auth_test_utils import auth_headers, setup_auth_service  # noqa

# ==================== 常量区 ====================
TEST_PASSWORD = "test-password"
TEST_SECRET_KEY = "test-secret-key"


# ==================== Fixtures ====================
@pytest.fixture
def app():
    """创建测试应用实例"""
    container = DependencyContainer()

    # 配置mock
    config = GlobalConfig()
    config.web = WebConfig(
        secret_key=TEST_SECRET_KEY, password_file="test_password.hash"
    )
    container.register(GlobalConfig, config)

    # 设置认证服务
    setup_auth_service(container)

    # Mock其他依赖
    im_manager = MagicMock(spec=IMManager)
    im_manager.adapters = {
        "adapter1": MagicMock(is_running=True),
        "adapter2": MagicMock(is_running=False),
    }
    container.register(IMManager, im_manager)

    llm_manager = MagicMock(spec=LLMManager)
    llm_manager.active_backends = {"backend1": [], "backend2": []}
    container.register(LLMManager, llm_manager)

    plugin_loader = MagicMock(spec=PluginLoader)
    plugin_loader.plugins = [MagicMock(), MagicMock(), MagicMock()]
    container.register(PluginLoader, plugin_loader)

    workflow_registry = MagicMock(spec=WorkflowRegistry)
    workflow_registry._workflows = {"workflow1": MagicMock(), "workflow2": MagicMock()}
    container.register(WorkflowRegistry, workflow_registry)

    web_server = WebServer(container)
    container.register(WebServer, web_server)
    return web_server.app


@pytest.fixture
def test_client(app):
    """创建测试客户端"""
    return TestClient(app)


# ==================== 测试用例 ====================
class TestSystemStatus:
    @pytest.mark.asyncio
    async def test_get_system_status(self, test_client, auth_headers):
        """测试获取系统状态"""
        # Mock psutil.Process
        mock_process = MagicMock()
        mock_process.memory_full_info.return_value = MagicMock(
            uss=1024 * 1024 * 100  # 100MB
        )
        mock_process.cpu_percent.return_value = 1.2
        
        # Mock psutil.virtual_memory
        mock_virtual_memory = MagicMock()
        mock_virtual_memory.total = 1024 * 1024 * 8192  # 8GB
        mock_virtual_memory.available = 1024 * 1024 * 4096  # 4GB
        mock_virtual_memory.used = 1024 * 1024 * 4096  # 4GB

        with patch(
            "kirara_ai.web.api.system.utils.psutil.Process", return_value=mock_process
        ), patch(
            "kirara_ai.web.api.system.utils.psutil.virtual_memory", return_value=mock_virtual_memory
        ), patch(
            "kirara_ai.web.api.system.utils.psutil.cpu_percent", return_value=1.2
        ):
            response = test_client.get(
                "/backend-api/api/system/status", headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert "status" in data
            status = data["status"]

            # 验证基本字段
            assert "version" in status
            assert "uptime" in status
            assert status["active_adapters"] == 1  # 只有一个运行中的适配器
            assert status["active_backends"] == 2  # 两个后端
            assert status["loaded_plugins"] == 3  # 三个插件
            assert status["workflow_count"] == 2  # 两个工作流

            # 验证资源使用情况
            assert "memory_usage" in status
            assert "cpu_usage" in status
            assert status["memory_usage"]["percent"] == 0.5  # used/total
            assert status["memory_usage"]["total"] == 8192  # 8GB
            assert status["memory_usage"]["free"] == 4096  # 4GB
            assert status["memory_usage"]["used"] == 100  # 100MB (process.memory_full_info().uss)
            assert status["cpu_usage"] == 1.2

    @pytest.mark.asyncio
    async def test_get_system_status_unauthorized(self, test_client):
        """测试未认证时获取系统状态"""
        response = test_client.get("/backend-api/api/system/status")

        assert response.status_code == 401
        data = response.json()
        assert "error" in data


    @pytest.mark.asyncio
    async def test_check_update(self, test_client, auth_headers):
        """测试检查更新"""
        response = test_client.get("/backend-api/api/system/check-update", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["current_backend_version"] != "0.0.0"
        assert data["latest_backend_version"] != "0.0.0"
        assert data["backend_update_available"] == False
        assert data["latest_webui_version"] != "0.0.0"
        assert data["webui_download_url"] != ""