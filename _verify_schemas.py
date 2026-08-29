#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""已收编：本文件现为薄 shim，正式位置 tools/verify_schemas.py。

保留至下一个版本后移除；旧调用 `python _verify_schemas.py` 继续有效。
"""
import os
import runpy
import sys

_target = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools", "verify_schemas.py")
print("[deprecation] _verify_schemas.py 已收编为 tools/verify_schemas.py，请改用新路径", file=sys.stderr)
sys.exit(runpy.run_path(_target, run_name="__main__") or 0)
