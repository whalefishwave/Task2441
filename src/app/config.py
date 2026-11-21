"""配置：仅从环境变量读取（统一技术约定）。

不提供硬编码密钥；本工单不依赖任何外部服务，所有配置项均有安全默认值。
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str) -> str:
    value = os.environ.get(name)
    return value if value not in (None, "") else default


def _env_int(name: str, default: int) -> int:
    raw = _env(name, str(default))
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_name: str = _env("APP_NAME", "member-questionnaire-s1-int-008")
    app_env: str = _env("APP_ENV", "local")
    log_level: str = _env("LOG_LEVEL", "INFO")
    host: str = _env("HOST", "127.0.0.1")
    port: int = _env_int("PORT", 8000)
    output_dir: str = _env("OUTPUT_DIR", "deliverables")
    # 试填模拟中每题停留时间（毫秒），用于模拟人类阅读速度；仅测试脚本使用。
    trial_dwell_ms: int = _env_int("TRIAL_DWELL_MS", 8000)


settings = Settings()
