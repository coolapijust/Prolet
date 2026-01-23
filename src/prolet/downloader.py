"""
GitHub API 下载器模块

使用 GitHub REST API 获取仓库文件树，筛选并下载 txt/md/docx 文件。
"""

import base64
import fnmatch
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import quote
import json

from .config_manager import Config


@dataclass
class FileItem:
    """文件条目"""
    path: str           # 相对于仓库根目录的完整路径
    name: str           # 文件名
    sha: str            # Git SHA
    download_url: str   # 下载地址
    size: int           # 文件大小 (bytes)


# 支持的文件扩展名
SUPPORTED_EXTENSIONS = {".txt", ".md", ".docx"}


def _make_request(url: str, token: Optional[str] = None) -> dict:
    """发送 GitHub API 请求"""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "prolet-tools/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        if e.code == 403:
            raise RuntimeError(f"GitHub API 限流或无权限: {e.reason}")
        elif e.code == 404:
            raise RuntimeError(f"仓库或路径不存在: {url}")
        raise


def _fetch_tree_recursive(
    owner: str,
    repo: str,
    branch: str,
    token: Optional[str],
    exclude_patterns: list[str],
    exclude_files: list[str],
) -> list[FileItem]:
    """
    使用 Git Database API 递归获取整个文件树

    返回筛选后的文件列表
    """
    # 获取 branch 最新 commit 的 tree SHA
    ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{branch}"
    ref_data = _make_request(ref_url, token)
    commit_sha = ref_data["object"]["sha"]

    # 获取 commit 对应的 tree
    commit_url = f"https://api.github.com/repos/{owner}/{repo}/git/commits/{commit_sha}"
    commit_data = _make_request(commit_url, token)
    tree_sha = commit_data["tree"]["sha"]

    # 递归获取整个 tree
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1"
    tree_data = _make_request(tree_url, token)

    files: list[FileItem] = []

    for item in tree_data.get("tree", []):
        if item["type"] != "blob":
            continue

        path = item["path"]
        name = Path(path).name
        ext = Path(path).suffix.lower()

        # 检查扩展名
        if ext not in SUPPORTED_EXTENSIONS:
            continue

        # 检查排除文件名
        if name in exclude_files:
            continue

        # 检查排除模式
        excluded = False
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(name, pattern):
                excluded = True
                break
        if excluded:
            continue

        # URL encode the path to handle special characters
        encoded_path = quote(path, safe='/')
        download_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{encoded_path}"
        files.append(FileItem(
            path=path,
            name=name,
            sha=item["sha"],
            download_url=download_url,
            size=item.get("size", 0),
        ))

    return files


def fetch_file_list(config: Config) -> list[FileItem]:
    """
    从 GitHub 获取文件列表

    Args:
        config: 配置对象

    Returns:
        符合条件的文件列表
    """
    parts = config.github_repo.split("/")
    if len(parts) != 2:
        raise ValueError(f"无效的仓库格式: {config.github_repo}，应为 owner/repo")

    owner, repo = parts
    return _fetch_tree_recursive(
        owner=owner,
        repo=repo,
        branch=config.target_branch,
        token=config.github_token,
        exclude_patterns=config.exclude_patterns,
        exclude_files=config.exclude_files,
    )


def download_file(file_item: FileItem, output_dir: Path, token: Optional[str] = None) -> Path:
    """
    下载单个文件

    Args:
        file_item: 文件条目
        output_dir: 输出目录
        token: GitHub token (可选)

    Returns:
        下载后的本地路径
    """
    # 创建目标目录
    target_path = output_dir / file_item.path
    target_path.parent.mkdir(parents=True, exist_ok=True)

    headers = {"User-Agent": "prolet-tools/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(file_item.download_url, headers=headers)

    with urlopen(req, timeout=60) as resp:
        content = resp.read()
        target_path.write_bytes(content)

    return target_path


from concurrent.futures import ThreadPoolExecutor, as_completed

def download_all(config: Config, file_list: list[FileItem], output_dir: Path) -> tuple[list[Path], list[str]]:
    """
    批量下载文件（带 SHA 缓存机制和多线程加速）

    Args:
        config: 配置对象
        file_list: 文件列表
        output_dir: 输出目录

    Returns:
        (下载成功的本地文件路径列表, 下载失败的文件路径列表)
    """
    downloaded_paths_map: dict[str, Path] = {}
    failed_files: list[str] = []
    total = len(file_list)
    cache_file = output_dir / "cache.json"
    cache = {}

    # 加载缓存
    if cache_file.exists():
        try:
            cache = json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ⚠ 缓存读取失败: {e}")

    to_download: list[FileItem] = []
    new_cache = {}
    skipped_count = 0

    # 预筛选：区分缓存文件和需要下载的文件
    for item in file_list:
        target_path = output_dir / item.path
        if target_path.exists() and cache.get(item.path) == item.sha:
            skipped_count += 1
            downloaded_paths_map[item.path] = target_path
            new_cache[item.path] = item.sha
        else:
            to_download.append(item)

    if skipped_count > 0:
        print(f"  ⚡ 跳过下载 (命中缓存): {skipped_count} 个文件")

    if not to_download:
        return [downloaded_paths_map[item.path] for item in file_list], []

    print(f"  🚀 开始并行下载 {len(to_download)} 个新文件 (线程数: 10)...")
    
    # 使用线程池并行下载
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_item = {
            executor.submit(download_file, item, output_dir, config.github_token): item 
            for item in to_download
        }
        
        completed = 0
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            completed += 1
            try:
                path = future.result()
                downloaded_paths_map[item.path] = path
                new_cache[item.path] = item.sha
                if completed % 100 == 0 or completed == len(to_download):
                    print(f"  [{completed}/{len(to_download)}] 下载完成: {item.path}")
            except Exception as e:
                failed_files.append(f"{item.path} ({e})")
                print(f"  ⚠ 下载失败 ({item.path}): {e}")

    # 保存新缓存
    try:
        cache_file.write_text(json.dumps(new_cache, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"  ⚠ 缓存保存失败: {e}")

    # 按照原始列表顺序返回路径
    successful = [downloaded_paths_map.get(item.path) for item in file_list if item.path in downloaded_paths_map]
    return successful, failed_files
