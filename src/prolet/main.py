"""
命令行入口模块

提供 CLI 接口运行构建流程
"""

import argparse
import sys
from pathlib import Path

from .config_manager import load_config
from .builder import run_build


def main() -> int:
    """CLI 入口函数"""
    parser = argparse.ArgumentParser(
        prog="prolet",
        description="Prolet Tools - 文档管理与静态站点生成工具",
    )
    parser.add_argument(
        "-c", "--config",
        type=Path,
        help="配置文件路径 (默认: reader/config.json)",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="输出目录 (默认: reader/)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        help="项目根目录 (默认: 当前目录)",
    )

    args = parser.parse_args()

    try:
        # 加载配置
        if args.root:
            import os
            os.environ["PROLET_ROOT"] = str(args.root.resolve())

        config = load_config(args.config)

        # 运行构建
        run_build(config, args.output)

        return 0

    except FileNotFoundError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"构建失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
