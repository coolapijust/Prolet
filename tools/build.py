#!/usr/bin/env python3
"""
构建入口脚本

用于在未安装包的情况下直接运行构建流程。
"""

import sys
from pathlib import Path

# 将 src 目录加入 Python 路径
project_root = Path(__file__).resolve().parent.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

# 设置项目根目录环境变量
import os
os.environ.setdefault("PROLET_ROOT", str(project_root))

# 运行主程序
from prolet.main import main

if __name__ == "__main__":
    sys.exit(main())
