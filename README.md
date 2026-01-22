# Text Sync Tools

用于从 GitHub 仓库下载文档并转换为静态网站的自动化工具。

## 功能特性

- 通过 GitHub API 下载指定仓库的文档
- 支持 TXT、Markdown、Word 文档格式
- 自动转换为静态 HTML 页面
- 部署到 GitHub Pages
- 支持手动触发工作流

## 配置说明

在 `reader/config.json` 中配置目标仓库：

```json
{
  "github_repo": "owner/repo",
  "source_dir": "txt",
  "site_title": "文档前端展示引擎",
  "sidebar_title": "文档目录"
}
```

## 使用方法

1. Fork 本仓库到你的账号
2. 修改 `reader/config.json` 配置目标仓库
3. 在 GitHub Actions 页面手动触发工作流
4. 等待部署完成，访问 GitHub Pages

## 目录结构

```
├── scripts/
│   ├── download-files.py    # 下载脚本
│   └── sync.py            # 同步脚本
├── reader/
│   ├── index.html          # 主页
│   ├── app.js              # 前端逻辑
│   ├── config.json          # 配置文件
│   ├── css/               # 样式文件
│   └── docs/              # 转换后的文档
└── .github/
    └── workflows/
        └── sync-api.yml      # 工作流配置
```

## 依赖项

- Python 3.11+
- python-docx

## 许可证

MIT
