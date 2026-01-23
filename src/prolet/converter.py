"""
内容转换器模块

将 txt/md/docx 文件转换为 HTML 片段。
本模块的逻辑参考 front-text 的转换实现，确保生成的 HTML 结构与前端兼容。
"""

from pathlib import Path
from typing import Optional
import html


def convert_txt(content: str) -> str:
    """
    将纯文本转换为 HTML

    保留换行和空格，使用 <pre> 包装
    """
    escaped = html.escape(content)
    return f'<pre class="txt-content">{escaped}</pre>'


def convert_markdown(content: str) -> str:
    """
    将 Markdown 转换为 HTML

    使用 markdown-it-py 渲染，确保与前端 markdown-it 一致。
    """
    try:
        from markdown_it import MarkdownIt
    except ImportError:
        # 回退到简单预格式化
        print("⚠ markdown-it-py 未安装，使用简单 HTML 转换")
        escaped = html.escape(content)
        return f'<pre class="md-fallback">{escaped}</pre>'

    # 配置与前端 markdown-it 尽量一致
    md = MarkdownIt("commonmark", {"html": True, "linkify": True, "typographer": True})

    # 启用常用插件功能
    md.enable(["table", "strikethrough"])

    return md.render(content)


def convert_docx(file_path: Path) -> str:
    """
    将 DOCX 文件转换为 HTML

    使用 mammoth 库进行转换
    """
    try:
        import mammoth
    except ImportError:
        return '<p class="error">无法转换 DOCX 文件：mammoth 库未安装</p>'

    try:
        with open(file_path, "rb") as f:
            result = mammoth.convert_to_html(f)
            if result.messages:
                for msg in result.messages:
                    print(f"  mammoth: {msg}")
            return result.value
    except Exception as e:
        escaped = html.escape(str(e))
        return f'<p class="error">DOCX 转换失败: {escaped}</p>'


def convert_file(file_path: Path) -> str:
    """
    根据文件类型自动选择转换器

    Args:
        file_path: 源文件路径

    Returns:
        HTML 字符串
    """
    ext = file_path.suffix.lower()

    if ext == ".docx":
        return convert_docx(file_path)

    # 对于文本文件，先读取内容
    try:
        # 尝试常见编码
        for encoding in ["utf-8", "gbk", "gb2312", "utf-16"]:
            try:
                content = file_path.read_text(encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            # 所有编码都失败，使用二进制读取并强制解码
            content = file_path.read_bytes().decode("utf-8", errors="replace")
    except Exception as e:
        return f'<p class="error">文件读取失败: {html.escape(str(e))}</p>'

    if ext == ".md":
        return convert_markdown(content)
    elif ext == ".txt":
        return convert_txt(content)
    else:
        # 未知类型，作为纯文本处理
        return convert_txt(content)


def generate_html_page(title: str, content_html: str, config: Optional[dict] = None) -> str:
    """
    生成完整的 HTML 页面（独立阅读用）

    注意：通常只需要 HTML 片段供前端 app.js 动态加载，本函数可选使用。

    Args:
        title: 页面标题
        content_html: 内容 HTML
        config: 可选配置

    Returns:
        完整 HTML 页面字符串
    """
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>
        body {{ font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        pre {{ background: #f5f5f5; padding: 1em; overflow-x: auto; }}
        code {{ background: #f5f5f5; padding: 0.2em 0.4em; border-radius: 3px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    </style>
</head>
<body>
    <article class="document-content">
        {content_html}
    </article>
</body>
</html>'''
