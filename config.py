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
MANIFEST_URL = "https://raw.githubusercontent.com/moideco/ToolLauncher-manifest/main/manifest.json"

# ============================================================
# ローカルキャッシュ
# ============================================================
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR      = os.path.join(_THIS_DIR, ".cache")
MANIFEST_CACHE = os.path.join(CACHE_DIR, "manifest.json")
ICON_CACHE_DIR = os.path.join(CACHE_DIR, "icons")

# ============================================================
# Maya scripts ディレクトリ
# None の場合は cmds.internalVar(userScriptDir=True) で自動取得
# 固定したい場合はフルパスで指定:
#   MAYA_SCRIPTS_DIR = r"C:/Users/YOUR_USER/Documents/maya/scripts"
# ============================================================
MAYA_SCRIPTS_DIR = None

# ============================================================
# UI 設定
# ============================================================
ICON_SIZE        = 64    # ツールアイコンのサイズ (px)
GRID_COLUMNS     = 4     # アイコングリッドの列数
WINDOW_MIN_WIDTH = 340
