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
# Qt Worker（バックグラウンドアップデート）
# ------------------------------------------------------------------

class UpdateWorker(QtCore.QThread):
    """
    バックグラウンドでマニフェスト取得 + 全ツールのダウンロードを行う。
    シグナル:
        progress(str)    : 進捗メッセージ
        tool_done(str)   : ツールID（1件完了）
        finished(dict)   : 完了時のマニフェストデータ
        error(str)       : エラーメッセージ
    """
    progress  = QtCore.Signal(str)
    tool_done = QtCore.Signal(str)
    finished  = QtCore.Signal(dict)
    error     = QtCore.Signal(str)

    def run(self):
        try:
            # 1. マニフェストを取得
            self.progress.emit("マニフェストを取得中...")
            manifest = fetch_manifest()

            scripts_dir = get_maya_scripts_dir()
            self.progress.emit(f"ダウンロード先: {scripts_dir}")

            tools = manifest.get("tools", [])
            for i, tool in enumerate(tools):
                if not tool.get("enabled", True):
                    continue
                name = tool.get("name", tool.get("id", "unknown"))
                self.progress.emit(f"[{i + 1}/{len(tools)}] {name} を更新中...")

                # スクリプトダウンロード
                download_tool_scripts(tool, scripts_dir)

                # アイコンダウンロード
                download_tool_icon(tool)

                self.tool_done.emit(tool["id"])

            self.finished.emit(manifest)

        except urllib.error.URLError as e:
            self.error.emit(f"ネットワークエラー: {e.reason}")
        except Exception as e:
            self.error.emit(str(e))
