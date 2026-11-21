"""单独重取问卷预览截图（不重复试填计时）。

运行：python -m scripts.take_screenshots
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from playwright.sync_api import sync_playwright  # noqa: E402

BASE = "http://127.0.0.1:8000"
SHOT_DIR = ROOT / "交付物" / "预览截图"


def main() -> None:
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=edge, headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page.goto(f"{BASE}/preview", wait_until="networkidle")
        page.click("#meta-btn")
        page.screenshot(path=str(SHOT_DIR / "01_问卷整体预览_含元数据.png"), full_page=True)
        page.locator('[data-section="B"]').screenshot(path=str(SHOT_DIR / "02_B部分满意度与NPS.png"))
        page.locator('[data-section="C"]').screenshot(path=str(SHOT_DIR / "03_C部分资源对接与跳转.png"))
        browser.close()
    for path in sorted(SHOT_DIR.glob("0[123]_*.png")):
        print(f"screenshot: {path.name} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
