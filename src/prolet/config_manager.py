"""
配置管理模块

读取和解析 reader/config.json，对外提供统一配置接口。
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """项目配置数据类"""
    github_repo: str
    source_dir: str = ""
    target_branch: str = "master"
    site_title: str = "文档阅读器"
    sidebar_title: str = "目录"
    theme: str = "light"
    max_content_width: int = 900
    enable_search: bool = True
    enable_back_to_top: bool = True
    exclude_patterns: list[str] = field(default_factory=list)
    exclude_files: list[str] = field(default_factory=list)
    home_page: Optional[str] = None

    # 运行时配置（不从 JSON 读取）
    project_root: Path = field(default_factory=Path.cwd)
    front_text_path: Optional[Path] = None
    github_token: Optional[str] = None


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径，默认为 reader/config.json

    Returns:
        Config 对象
    """
    # 确定项目根目录
    project_root = Path(os.environ.get("PROLET_ROOT", Path.cwd()))

    if config_path is None:
        config_path = project_root / "reader" / "config.json"

    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 读取运行时环境变量
    github_token = os.environ.get("GITHUB_TOKEN")
    front_text_path_str = os.environ.get("FRONT_TEXT_PATH")
    front_text_path = Path(front_text_path_str) if front_text_path_str else None

    return Config(
        github_repo=data.get("github_repo", ""),
        source_dir=data.get("source_dir", ""),
        target_branch=data.get("target_branch", "master"),
        site_title=data.get("site_title", "文档阅读器"),
        sidebar_title=data.get("sidebar_title", "目录"),
        theme=data.get("theme", "light"),
        max_content_width=data.get("max_content_width", 900),
        enable_search=data.get("enable_search", True),
        enable_back_to_top=data.get("enable_back_to_top", True),
        exclude_patterns=data.get("exclude_patterns", []),
        exclude_files=data.get("exclude_files", []),
        home_page=data.get("home_page"),
        project_root=project_root,
        front_text_path=front_text_path,
        github_token=github_token,
    )
