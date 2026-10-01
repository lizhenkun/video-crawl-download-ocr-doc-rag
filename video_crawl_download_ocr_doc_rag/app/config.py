#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
file: config.py
"""
import os
import json
import threading
import tomllib
from pathlib import Path
from typing import Any, Dict, List, Optional
from DrissionPage import ChromiumPage, ChromiumOptions

from pydantic import BaseModel, Field

def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = get_project_root()
OUTPUT_ROOT = PROJECT_ROOT.parent / "output"

if not os.path.exists(OUTPUT_ROOT):
    os.makedirs(OUTPUT_ROOT)
# WORKSPACE_ROOT = PROJECT_ROOT / "workspace"
# CLAUDE_CWD = PROJECT_ROOT / "app" / ".claude"
# SKILL_ROOT = CLAUDE_CWD / "skills"


class LLMSettings(BaseModel):
    """LLMSettings"""
    model: str = Field(..., description="Model name")
    base_url: str = Field(..., description="API base URL")
    api_key: str = Field(..., description="API key")
    max_tokens: int = Field(4096, description="Maximum number of tokens per request")
    max_input_tokens: Optional[int] = Field(
        None,
        description="Maximum input tokens to use across all requests (None for unlimited)",
    )
    temperature: float = Field(1.0, description="Sampling temperature")
    api_type: str = Field(..., description="Azure, Openai, or Ollama")
    api_version: str = Field(..., description="Azure Openai version if AzureOpenai")


class ProxySettings(BaseModel):
    """ProxySettings"""
    server: str = Field(None, description="Proxy server address")
    username: Optional[str] = Field(None, description="Proxy username")
    password: Optional[str] = Field(None, description="Proxy password")


class SearchSettings(BaseModel):
    """SearchSettings"""
    engine: str = Field(default="Google", description="Search engine the llm to use")
    fallback_engines: List[str] = Field(
        default_factory=lambda: ["DuckDuckGo", "Baidu", "Bing"],
        description="Fallback search engines to try if the primary engine fails",
    )
    retry_delay: int = Field(
        default=60,
        description="Seconds to wait before retrying all engines again after they all fail",
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of times to retry all engines when all fail",
    )
    lang: str = Field(
        default="en",
        description="Language code for search results (e.g., en, zh, fr)",
    )
    country: str = Field(
        default="us",
        description="Country code for search results (e.g., us, cn, uk)",
    )


class BrowserSettings(BaseModel):
    """BrowserSettings"""
    headless: bool = Field(False, description="Whether to run browser in headless mode")
    disable_security: bool = Field(
        True, description="Disable browser security features"
    )
    extra_chromium_args: List[str] = Field(
        default_factory=list, description="Extra arguments to pass to the browser"
    )
    chrome_instance_path: Optional[str] = Field(
        None, description="Path to a Chrome instance to use"
    )
    wss_url: Optional[str] = Field(
        None, description="Connect to a browser instance via WebSocket"
    )
    cdp_url: Optional[str] = Field(
        None, description="Connect to a browser instance via CDP"
    )
    proxy: Optional[ProxySettings] = Field(
        None, description="Proxy settings for the browser"
    )
    max_content_length: int = Field(
        2000, description="Maximum length for content retrieval operations"
    )


class SandboxSettings(BaseModel):
    """Configuration for the execution sandbox"""

    use_sandbox: bool = Field(False, description="Whether to use the sandbox")
    image: str = Field("python:3.12-slim", description="Base image")
    work_dir: str = Field("/workspace", description="Container working directory")
    memory_limit: str = Field("512m", description="Memory limit")
    cpu_limit: float = Field(1.0, description="CPU limit")
    timeout: int = Field(300, description="Default command timeout (seconds)")
    network_enabled: bool = Field(
        False, description="Whether network access is allowed"
    )


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server"""
    orginal_config: Dict[Any, Any] = Field(
        default_factory=dict, description="original configure of the mcp server")
    transport_type: str = Field(..., description="Server connection type (sse, streamableHttp, stdio)")
    url: Optional[str] = Field(None, description="Server URL for SSE connections")
    command: Optional[str] = Field(None, description="Command for stdio connections")
    args: List[str] = Field(
        default_factory=list, description="Arguments for stdio command"
    )


class MCPSettings(BaseModel):
    """Configuration for MCP (Model Context Protocol)"""

    server_reference: str = Field(
        "app.mcp.server", description="Module reference for the MCP server"
    )
    servers: Dict[str, MCPServerConfig] = Field(
        default_factory=dict, description="MCP server configurations"
    )

    @classmethod
    def load_server_config(cls) -> Dict[str, MCPServerConfig]:
        """Load MCP server configuration from JSON file"""
        config_path = PROJECT_ROOT / "config" / "mcp.json"

        try:
            config_file = config_path if config_path.exists() else None
            if not config_file:
                return {}

            with config_file.open() as f:
                data = json.load(f)
                servers = {}

                for server_id, server_config in data.get("mcpServers", {}).items():
                    servers[server_id] = MCPServerConfig(
                        orginal_config=server_config,
                        transport_type=server_config["transportType"],
                        url=server_config.get("url"),
                        command=server_config.get("command"),
                        args=server_config.get("args", []),
                    )
                return servers
        except Exception as e:
            raise ValueError(f"Failed to load MCP server config: {e}")


class AppConfig(BaseModel):
    """
    App config
    """
    llm: Dict[str, LLMSettings]
    sandbox: Optional[SandboxSettings] = Field(
        None, description="Sandbox configuration"
    )
    browser_config: Optional[BrowserSettings] = Field(
        None, description="Browser configuration"
    )
    search_config: Optional[SearchSettings] = Field(
        None, description="Search configuration"
    )
    mcp_config: Optional[MCPSettings] = Field(None, description="MCP configuration")

    bilibili_up_info: Dict[int, Any] = Field(None, description="Bilibili up info")

    class Config:
        """sub config class"""
        arbitrary_types_allowed = True


class Config:
    """config class"""
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    print_level = "INFO"
    log_level = "DEBUG"

    # WEB_BROWER_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    WEB_BROWER_PATH = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
    # WEB_BROWER_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

    CHROMIUM_OPTIONS = ChromiumOptions().auto_port()
    # CHROMIUM_OPTIONS.set_paths(browser_path=DRIVER_PATH)
    # 设置无痕模式
    # CHROMIUM_OPTIONS.incognito(True)

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        import sys
        print(f'{"-" * 60}\n system.args: {sys.argv}\n{"-" * 60}')

        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._config = None
                    self._load_initial_config()
                    self._initialized = True

    @staticmethod
    def _get_config_path() -> Path:
        root = PROJECT_ROOT
        config_path = root / "config" / "config.toml"
        if config_path.exists():
            return config_path
        example_path = root / "config" / "config.example.toml"
        if example_path.exists():
            return example_path
        raise FileNotFoundError("No configuration file found in config directory")

    def _load_config(self) -> dict:
        config_path = self._get_config_path()
        with config_path.open("rb") as f:
            return tomllib.load(f)

    def _load_initial_config(self):
        raw_config = self._load_config()
        print(f'raw_config: {json.dumps(raw_config)}')

        base_llm = raw_config.get("llm", {})
        llm_overrides = {
            k: v for k, v in raw_config.get("llm", {}).items() if isinstance(v, dict)
        }

        default_settings = {
            "model": base_llm.get("model"),
            "base_url": base_llm.get("base_url"),
            "api_key": base_llm.get("api_key"),
            "max_tokens": base_llm.get("max_tokens", 4096),
            "max_input_tokens": base_llm.get("max_input_tokens"),
            "temperature": base_llm.get("temperature", 1.0),
            "api_type": base_llm.get("api_type", ""),
            "api_version": base_llm.get("api_version", ""),
        }

        # handle browser config.
        browser_config = raw_config.get("browser", {})
        browser_settings = None

        if browser_config:
            # handle proxy settings.
            proxy_config = browser_config.get("proxy", {})
            proxy_settings = None

            if proxy_config and proxy_config.get("server"):
                proxy_settings = ProxySettings(
                    **{
                        k: v
                        for k, v in proxy_config.items()
                        if k in ["server", "username", "password"] and v
                    }
                )

            # filter valid browser config parameters.
            valid_browser_params = {
                k: v
                for k, v in browser_config.items()
                if k in BrowserSettings.__annotations__ and v is not None
            }

            # if there is proxy settings, add it to the parameters.
            if proxy_settings:
                valid_browser_params["proxy"] = proxy_settings

            # only create BrowserSettings when there are valid parameters.
            if valid_browser_params:
                browser_settings = BrowserSettings(**valid_browser_params)

        search_config = raw_config.get("search", {})
        search_settings = None
        if search_config:
            search_settings = SearchSettings(**search_config)
        sandbox_config = raw_config.get("sandbox", {})
        if sandbox_config:
            sandbox_settings = SandboxSettings(**sandbox_config)
        else:
            sandbox_settings = SandboxSettings()

        mcp_config = raw_config.get("mcp", {})
        mcp_settings = None
        if mcp_config:
            # Load server configurations from JSON
            mcp_config["servers"] = MCPSettings.load_server_config()
            mcp_settings = MCPSettings(**mcp_config)
        else:
            mcp_settings = MCPSettings(servers=MCPSettings.load_server_config())

        config_dict = {
            "llm": {
                "default": default_settings,
                **{
                    name: {**default_settings, **override_config}
                    for name, override_config in llm_overrides.items()
                },
            },
            "sandbox": sandbox_settings,
            "browser_config": browser_settings,
            "search_config": search_settings,
            "mcp_config": mcp_settings,
            
            "bilibili_up_info": raw_config.get("BILIBILI_UP_INFO", {}),
            "kwargs": raw_config.get("kwargs", {})
        }

        self._config = AppConfig(**config_dict)

    @property
    def llm(self) -> Dict[str, LLMSettings]:
        """property"""
        return self._config.llm

    @property
    def sandbox(self) -> SandboxSettings:
        """property"""
        return self._config.sandbox

    @property
    def browser_config(self) -> Optional[BrowserSettings]:
        """property"""
        return self._config.browser_config

    @property
    def search_config(self) -> Optional[SearchSettings]:
        """property"""
        return self._config.search_config

    @property
    def mcp_config(self) -> MCPSettings:
        """Get the MCP configuration"""
        return self._config.mcp_config

    @property
    def output_root(self) -> Path:
        """Get the output root directory"""
        return OUTPUT_ROOT

    @property
    def root_path(self) -> Path:
        """Get the root path of the application"""
        return PROJECT_ROOT
    
    @property
    def bilibili_up_info(self) -> Dict[str, Any]:
        """property"""
        return self._config.bilibili_up_info

config = Config()
print(config.bilibili_up_info)
print(config.output_root)

# # 创建数据库对应的异步数据连接池
# class DBSettings(BaseModel):
#     """
#     db 配置
#     """
#     dbs: Dict[str, dict] = Field(
#         default_factory=dict, description="Database configurations"
#     )

#     async_database_map: Dict[str, object] = Field(
#         default_factory=dict, description="Async Database name mapping"
#     )

#     sync_database_map: Dict[str, object] = Field(
#         default_factory=dict, description="Sync Database name mapping"
#     )

#     @classmethod
#     def load_db_config(cls) -> Dict[str, dict]:
#         """Load db configuration from JSON file"""
#         config_path = PROJECT_ROOT / "config" / "database.json"
#         if not config_path.exists():
#             return None

#         with config_path.open() as f:
#             data = json.load(f)
#             dbs = {}

#             for name, db_config in data.items():
#                 dbs[name] = db_config

#             return dbs

#     def get_or_create_async_database(self, db_name):
#         """
#         get_or_create_async_database
#         """
#         if db_name in self.async_database_map:
#             return self.async_database_map[db_name]

#         database = PooledMySQLDatabase(**self.dbs[db_name])
#         self.async_database_map[db_name] = database
#         return database
    
#     def get_or_create_sync_database(self, db_name):
#         """
#         get_or_create_sync_database
#         """
#         if db_name in self.sync_database_map:
#             return self.sync_database_map[db_name]

#         db_config = self.dbs[db_name].copy()
#         db_config.pop("pool_params")

#         database = MySQLDatabase(**db_config)
#         self.sync_database_map[db_name] = database
#         return database

# db_names = ["SMART_PIPE", "EOS_READ"]
# # db_names = ["SMART_PIPE_TEST"]
# for db_name in db_names:
#     print(f"get_or_create_async_database : {db_name}")
#     config.db_config.get_or_create_async_database(db_name)

# print(f"CLAUDE_CWD: {CLAUDE_CWD}")
# print(f'tornado_port: {config.tornado_port}')
# print(f'nginx_url: {config.nginx_url}')
