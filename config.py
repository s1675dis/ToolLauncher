"""
ToolLauncher 設定ファイル
MANIFEST_URL を実際の GitHub raw URL に変更してください。
"""
import os

# ============================================================
# マニフェスト JSON の URL
# GitHub の raw URL を指定してください
# 例: https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/manifest.json
# ============================================================
MANIFEST_URL = "https://raw.githubusercontent.com/moideco/ToolLauncher/main/manifest.json"

# ============================================================
# ランチャー自己更新
# ============================================================
LAUNCHER_REPO_RAW = "https://raw.githubusercontent.com/moideco/ToolLauncher/main"
LAUNCHER_FILES    = ["__init__.py", "config.py", "launcher.py", "tool_manager.py"]

# ============================================================
# ローカルキャッシュ
# ============================================================
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR      = os.path.join(_THIS_DIR, ".cache")
MANIFEST_CACHE      = os.path.join(CACHE_DIR, "manifest.json")
ICON_CACHE_DIR      = os.path.join(CACHE_DIR, "icons")
USER_MANIFESTS_FILE = os.path.join(CACHE_DIR, "user_manifests.json")

# ============================================================
# UI 設定
# ============================================================
ICON_SIZE        = 64    # ツールアイコンのサイズ (px)
GRID_COLUMNS     = 4     # アイコングリッドの列数
WINDOW_MIN_WIDTH = 340
