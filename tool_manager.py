"""
tool_manager.py
GitHub上のマニフェストJSONを取得し、ツールスクリプト・アイコンを
Maya の scripts フォルダへダウンロード・管理するモジュール。
"""
import json
import os
import sys
import urllib.request
import urllib.error
from typing import Optional, List

from PySide2 import QtCore

import ToolLauncher.config as config


# ------------------------------------------------------------------
# ユーティリティ
# ------------------------------------------------------------------

def get_maya_scripts_dir():
    """C:/Users/<username>/Documents/maya/scripts を返す。"""
    path = os.path.join(os.path.expanduser("~"), "Documents", "maya", "scripts")
    os.makedirs(path, exist_ok=True)
    return os.path.normpath(path)


def _ensure_dirs():
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    os.makedirs(config.ICON_CACHE_DIR, exist_ok=True)


def _download(url, dest_path):
    """URL からファイルをダウンロードして dest_path に保存する。"""
    req = urllib.request.Request(url, headers={"User-Agent": "ToolLauncher/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read()
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb") as f:
        f.write(data)
    return dest_path


# ------------------------------------------------------------------
# マニフェスト操作
# ------------------------------------------------------------------

def load_manifest_cache():
    """ローカルキャッシュからマニフェストを読み込む。なければ空を返す。"""
    if os.path.exists(config.MANIFEST_CACHE):
        try:
            with open(config.MANIFEST_CACHE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"tools": []}


def fetch_manifest():
    """
    GitHub からマニフェストを取得してキャッシュに保存し、内容を返す。
    失敗した場合は例外をそのまま raise する。
    """
    _ensure_dirs()
    req = urllib.request.Request(
        config.MANIFEST_URL,
        headers={"User-Agent": "ToolLauncher/1.0"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    with open(config.MANIFEST_CACHE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


# ------------------------------------------------------------------
# スクリプト・アイコンのダウンロード
# ------------------------------------------------------------------

def download_tool_scripts(tool: dict, scripts_dir: str) -> List[str]:
    """
    tool の scripts リストを scripts_dir へダウンロードする。
    Returns: ダウンロードしたファイルパスのリスト
    """
    downloaded = []
    for script in tool.get("scripts", []):
        url      = script["url"]
        filename = script["filename"]
        dest     = os.path.join(scripts_dir, filename)
        _download(url, dest)
        downloaded.append(dest)
    return downloaded


def download_tool_icon(tool: dict) -> Optional[str]:
    """
    tool のアイコンをキャッシュフォルダへダウンロードする。
    Returns: ローカルキャッシュパス（失敗時は None）
    """
    icon_url = tool.get("icon_url", "")
    if not icon_url:
        return None
    _ensure_dirs()
    ext       = os.path.splitext(icon_url)[-1] or ".png"
    dest      = os.path.join(config.ICON_CACHE_DIR, f"{tool['id']}{ext}")
    try:
        _download(icon_url, dest)
        return dest
    except Exception:
        return None


def get_cached_icon_path(tool: dict) -> Optional[str]:
    """キャッシュ済みアイコンのパスを返す（存在しなければ None）。"""
    for ext in (".png", ".svg", ".jpg"):
        p = os.path.join(config.ICON_CACHE_DIR, f"{tool['id']}{ext}")
        if os.path.exists(p):
            return p
    return None


def is_tool_installed(tool: dict, scripts_dir: str) -> bool:
    """ツールのスクリプトが scripts_dir に存在するか確認する。"""
    for script in tool.get("scripts", []):
        if not os.path.exists(os.path.join(scripts_dir, script["filename"])):
            return False
    return bool(tool.get("scripts"))


# ------------------------------------------------------------------
# ランチャー自己更新
# ------------------------------------------------------------------

def update_launcher_files():
    """
    ランチャー本体のファイルを GitHub から更新する。
    Returns: 更新したファイル数
    """
    launcher_dir = os.path.dirname(os.path.abspath(__file__))
    count = 0
    for filename in config.LAUNCHER_FILES:
        url  = f"{config.LAUNCHER_REPO_RAW}/{filename}"
        dest = os.path.join(launcher_dir, filename)
        _download(url, dest)
        count += 1
    return count


# ------------------------------------------------------------------
# Qt Worker（バックグラウンドアップデート・3段階）
# ------------------------------------------------------------------

class UpdateWorker(QtCore.QThread):
    """
    3段階のアップデートをバックグラウンドで実行する。

    Stage 1: ランチャー自己更新
    Stage 2: Manifest 確認・取得
    Stage 3: 各ツールのスクリプト・アイコン取得

    シグナル:
        stage(int, str)         : ステージ番号(1-3)とラベル
        progress(str)           : 詳細メッセージ
        tool_done(str)          : ツールID（1件完了）
        launcher_updated()      : ランチャーファイルを更新した
        finished(dict)          : 完了時のマニフェストデータ
        error(str)              : エラーメッセージ
    """
    stage           = QtCore.Signal(int, str)
    progress        = QtCore.Signal(str)
    tool_done       = QtCore.Signal(str)
    launcher_updated = QtCore.Signal()
    finished        = QtCore.Signal(dict)
    error           = QtCore.Signal(str)

    def run(self):
        try:
            # ---- Stage 1: ランチャー自己更新 ----
            self.stage.emit(1, "ランチャーのアップデート")
            self.progress.emit("ランチャーのファイルを取得中...")
            count = update_launcher_files()
            self.progress.emit(f"ランチャーを更新しました ({count} ファイル)")
            self.launcher_updated.emit()

            # ---- Stage 2: Manifest 確認 ----
            self.stage.emit(2, "Manifest の確認")
            self.progress.emit("Manifest を取得中...")
            manifest = fetch_manifest()
            tools = [t for t in manifest.get("tools", []) if t.get("enabled", True)]
            self.progress.emit(f"Manifest を確認しました ({len(tools)} ツール登録)")

            # ---- Stage 3: 各ツールの取得 ----
            self.stage.emit(3, "ツールの取得・アップデート")
            scripts_dir = get_maya_scripts_dir()
            for i, tool in enumerate(tools):
                name = tool.get("name", tool.get("id", "unknown"))
                self.progress.emit(f"[{i + 1}/{len(tools)}] {name}...")
                download_tool_scripts(tool, scripts_dir)
                download_tool_icon(tool)
                self.tool_done.emit(tool["id"])

            self.finished.emit(manifest)

        except urllib.error.URLError as e:
            self.error.emit(f"ネットワークエラー: {e.reason}")
        except Exception as e:
            self.error.emit(str(e))
