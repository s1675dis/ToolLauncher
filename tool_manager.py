"""
tool_manager.py
GitHub上のマニフェストJSONを取得し、ツールスクリプト・アイコンを
Maya の scripts フォルダへダウンロード・管理するモジュール。
"""
import base64
import json
import os
import shutil
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


def _is_remote_url(source):
    """Return True if source is an HTTP/HTTPS/FTP URL."""
    return source.startswith(("http://", "https://", "ftp://"))


def _download(source, dest_path):
    """
    Copy source to dest_path.
    - HTTP/HTTPS/FTP : fetched via urllib
    - UNC path (\\server\share\...) or local path : copied via shutil
    """
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    if _is_remote_url(source):
        data = _fetch_remote(source)
        with open(dest_path, "wb") as f:
            f.write(data)
    else:
        shutil.copy2(source, dest_path)
    return dest_path


# ------------------------------------------------------------------
# マニフェスト操作
# ------------------------------------------------------------------

def load_manifest_cache():
    """Load merged manifest from local cache. Returns empty manifest if not found."""
    if os.path.exists(config.MANIFEST_CACHE):
        try:
            with open(config.MANIFEST_CACHE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"tools": []}


def _fetch_manifest_from_url(url):
    """Fetch a single manifest JSON from the given URL."""
    req = urllib.request.Request(url, headers={"User-Agent": "ToolLauncher/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_manifest():
    """
    Fetch the main manifest, then additionally fetch all user manifests.
    - Main manifest is always the base and takes priority.
    - User manifest tools are appended; they cannot override main manifest tools.
    - Unreachable user manifests are silently skipped.
    """
    _ensure_dirs()

    # 1. Main manifest (always required)
    main_tools = {
        tool["id"]: tool
        for tool in _fetch_manifest_from_url(config.MANIFEST_URL).get("tools", [])
    }

    # 2. User manifests (additive only - read from local files)
    user_tools = {}
    for path in load_user_manifest_paths():
        try:
            for tool in load_manifest_from_file(path).get("tools", []):
                if tool["id"] not in main_tools:  # never override main manifest
                    user_tools[tool["id"]] = tool
        except Exception:
            pass

    merged = {"tools": list(main_tools.values()) + list(user_tools.values())}

    with open(config.MANIFEST_CACHE, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    return merged


# ------------------------------------------------------------------
# User manifest URL management
# ------------------------------------------------------------------

def _user_manifests_file():
    """Return USER_MANIFESTS_FILE path, falling back if config is outdated."""
    return getattr(config, "USER_MANIFESTS_FILE",
                   os.path.join(config.CACHE_DIR, "user_manifests.json"))


# ------------------------------------------------------------------
# Manifest validation
# ------------------------------------------------------------------

def validate_manifest(data):
    """
    Validate that a parsed JSON object is a valid manifest.
    Raises ValueError with a descriptive message if invalid.
    """
    if not isinstance(data, dict):
        raise ValueError("Root element must be a JSON object.")
    if "tools" not in data:
        raise ValueError("Missing required key: 'tools'.")
    if not isinstance(data["tools"], list):
        raise ValueError("'tools' must be an array.")
    for i, tool in enumerate(data["tools"]):
        for key in ("id", "name"):
            if key not in tool:
                raise ValueError(f"Tool at index {i} is missing required key: '{key}'.")
    return True


def load_manifest_from_file(path):
    """
    Load and validate a manifest JSON from a local file path.
    Raises ValueError on JSON parse error or invalid structure.
    Returns the manifest dict on success.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parse error: {e}")
    validate_manifest(data)
    return data


# ------------------------------------------------------------------
# User manifest file path management
# ------------------------------------------------------------------

def load_user_manifest_paths():
    """Load the list of registered local manifest file paths."""
    path = _user_manifests_file()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_user_manifest_paths(paths):
    """Save the list of registered local manifest file paths."""
    _ensure_dirs()
    with open(_user_manifests_file(), "w", encoding="utf-8") as f:
        json.dump(paths, f, ensure_ascii=False, indent=2)


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

def _fetch_remote(url):
    """キャッシュを無効化したヘッダーでURLの内容を取得する。"""
    headers = {
        "User-Agent":     "ToolLauncher/1.0",
        "Cache-Control":  "no-cache, no-store",
        "Pragma":         "no-cache",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def _content_equal(local_path, remote_data):
    """ローカルファイルとリモートデータを改行コードを正規化して比較する。"""
    if not os.path.exists(local_path):
        return False
    with open(local_path, "rb") as f:
        local_data = f.read()
    return local_data.replace(b"\r\n", b"\n") == remote_data.replace(b"\r\n", b"\n")


def _fetch_via_contents_api(filename):
    """
    GitHub Contents API でファイル内容を取得する。
    raw.githubusercontent.com と異なりCDNキャッシュが効かないため
    常に最新コミットの内容を返す。
    """
    # LAUNCHER_REPO_RAW から owner/repo/ref を解析
    # 例: https://raw.githubusercontent.com/moideco/ToolLauncher/main
    path  = config.LAUNCHER_REPO_RAW.replace("https://raw.githubusercontent.com/", "")
    owner, repo, ref = path.split("/", 2)

    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}?ref={ref}"
    headers = {
        "User-Agent": "ToolLauncher/1.0",
        "Accept":     "application/vnd.github.v3+json",
    }
    req = urllib.request.Request(api_url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    return base64.b64decode(result["content"])


def update_launcher_files():
    """
    GitHub Contents API でランチャーファイルを取得し、
    差分があるファイルのみ上書きする。
    Returns: 実際に更新したファイル数（0なら全て最新）
    """
    launcher_dir = os.path.dirname(os.path.abspath(__file__))
    updated = 0
    for filename in config.LAUNCHER_FILES:
        dest        = os.path.join(launcher_dir, filename)
        remote_data = _fetch_via_contents_api(filename)

        if _content_equal(dest, remote_data):
            continue

        with open(dest, "wb") as f:
            f.write(remote_data)
        updated += 1

    return updated


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
            # ---- Stage 1: Launcher self-update ----
            self.stage.emit(1, "Launcher Update")
            self.progress.emit("Checking launcher files...")
            count = update_launcher_files()
            if count > 0:
                self.progress.emit(f"Launcher updated ({count} file(s))")
                self.launcher_updated.emit()
            else:
                self.progress.emit("Launcher is up to date")

            # ---- Stage 2: Manifest ----
            self.stage.emit(2, "Manifest Check")
            user_paths = load_user_manifest_paths()
            extra_msg = f" + {len(user_paths)} user manifest(s)" if user_paths else ""
            self.progress.emit(f"Fetching main manifest{extra_msg}...")
            manifest = fetch_manifest()
            tools = [t for t in manifest.get("tools", []) if t.get("enabled", True)]
            self.progress.emit(f"Manifest fetched ({len(tools)} tool(s) total)")

            # ---- Stage 3: Tools ----
            self.stage.emit(3, "Tool Update")
            scripts_dir = get_maya_scripts_dir()
            for i, tool in enumerate(tools):
                name = tool.get("name", tool.get("id", "unknown"))
                self.progress.emit(f"[{i + 1}/{len(tools)}] {name}...")
                download_tool_scripts(tool, scripts_dir)
                download_tool_icon(tool)
                self.tool_done.emit(tool["id"])

            self.finished.emit(manifest)

        except urllib.error.URLError as e:
            self.error.emit(f"Network error: {e.reason}")
        except Exception as e:
            self.error.emit(str(e))
