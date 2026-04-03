"""
ToolLauncher - メインランチャーUI
・アイコングリッドで登録ツールを一覧表示
・アイコンクリックでツールを起動
・アップデートボタンでGitHubから最新スクリプト・マニフェストを取得
"""
import os
import sys

from PySide2 import QtCore, QtGui, QtWidgets

import ToolLauncher.config      as config
import ToolLauncher.tool_manager as tool_manager

try:
    import maya.OpenMayaUI as omui
    from shiboken2 import wrapInstance
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False


# ------------------------------------------------------------------
# ツールアイコンボタン
# ------------------------------------------------------------------

class ToolIconButton(QtWidgets.QToolButton):
    """アイコン + 名前ラベルを持つツールボタン。"""

    ICON_SIZE = config.ICON_SIZE

    def __init__(self, tool: dict, scripts_dir: str, parent=None):
        super().__init__(parent)
        self.tool        = tool
        self.scripts_dir = scripts_dir

        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.setIconSize(QtCore.QSize(self.ICON_SIZE, self.ICON_SIZE))
        self.setFixedSize(self.ICON_SIZE + 24, self.ICON_SIZE + 36)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setToolTip(tool.get("description", ""))

        self._refresh()
        self.clicked.connect(self._launch)

    # ---- 表示更新 ----
    def _refresh(self):
        name      = self.tool.get("name", self.tool.get("id", "Tool"))
        installed = tool_manager.is_tool_installed(self.tool, self.scripts_dir)

        # ラベル（未インストールは薄く表示）
        self.setText(name)
        self.setEnabled(installed)

        # アイコン設定
        icon_path = tool_manager.get_cached_icon_path(self.tool)
        if icon_path and os.path.exists(icon_path):
            self.setIcon(QtGui.QIcon(icon_path))
        else:
            self._set_fallback_icon(installed)

        # スタイル
        if installed:
            self.setStyleSheet("")
        else:
            self.setStyleSheet("color: gray;")

    def _set_fallback_icon(self, installed: bool):
        """Mayaアイコンまたはデフォルトアイコンを使う。"""
        if MAYA_AVAILABLE:
            maya_icon = self.tool.get("maya_icon", "commandButton.png")
            self.setIcon(QtGui.QIcon(f":{maya_icon}"))
        else:
            # Qtの標準アイコンをフォールバックに使う
            style = self.style()
            icon  = style.standardIcon(QtWidgets.QStyle.SP_FileIcon)
            self.setIcon(icon)

    def mark_updated(self):
        """アップデート完了後に呼び出して表示を更新する。"""
        self._refresh()

    # ---- ツール起動 ----
    def _launch(self):
        entry_module = self.tool.get("entry_module")
        entry_func   = self.tool.get("entry_function", "show")

        if not entry_module:
            QtWidgets.QMessageBox.warning(
                self, "設定エラー",
                f"'{self.tool.get('name')}' に entry_module が設定されていません。"
            )
            return

        # Maya scripts dir が sys.path に含まれているか確認
        if self.scripts_dir not in sys.path:
            sys.path.insert(0, self.scripts_dir)

        try:
            exec(f"import {entry_module}\n{entry_module}.{entry_func}()")
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "起動エラー",
                f"ツールの起動に失敗しました:\n{e}"
            )


# ------------------------------------------------------------------
# メインランチャーウィンドウ
# ------------------------------------------------------------------

class ToolLauncherUI(QtWidgets.QWidget):
    WINDOW_TITLE = "Tool Launcher"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumWidth(config.WINDOW_MIN_WIDTH)

        self._manifest    = tool_manager.load_manifest_cache()
        self._scripts_dir = tool_manager.get_maya_scripts_dir()
        self._worker      = None
        self._tool_buttons = {}  # type: dict

        self._build_ui()
        self._populate_grid()

    # ----------------------------------------------------------------
    # UI 構築
    # ----------------------------------------------------------------

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(4)
        root.setContentsMargins(8, 8, 8, 8)

        # ---- ヘッダー ----
        header = QtWidgets.QHBoxLayout()
        title  = QtWidgets.QLabel("Tool Launcher")
        f      = title.font()
        f.setBold(True)
        f.setPointSize(11)
        title.setFont(f)
        header.addWidget(title)
        header.addStretch()

        self.btn_update = QtWidgets.QPushButton("アップデート")
        self.btn_update.setFixedWidth(110)
        self.btn_update.setToolTip("GitHubから最新のツール情報とスクリプトを取得します")
        self.btn_update.clicked.connect(self._on_update)
        header.addWidget(self.btn_update)
        root.addLayout(header)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFrameShadow(QtWidgets.QFrame.Sunken)
        root.addWidget(sep)

        # ---- ツールグリッド（スクロール対応） ----
        self.scroll_area   = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.grid_container = QtWidgets.QWidget()
        self.grid_layout    = QtWidgets.QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(8)
        self.grid_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.scroll_area.setWidget(self.grid_container)
        root.addWidget(self.scroll_area)

        # ---- ステータスバー ----
        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet("color: gray; font-size: 9px;")
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)

        # ---- プログレスバー ----
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setRange(0, 0)   # indeterminate
        self.progress_bar.hide()
        root.addWidget(self.progress_bar)

    # ----------------------------------------------------------------
    # グリッド生成
    # ----------------------------------------------------------------

    def _populate_grid(self):
        # グリッドをクリア
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._tool_buttons.clear()

        tools   = self._manifest.get("tools", [])
        columns = config.GRID_COLUMNS

        if not tools:
            empty = QtWidgets.QLabel("ツールが登録されていません。\n「アップデート」ボタンを押してください。")
            empty.setAlignment(QtCore.Qt.AlignCenter)
            empty.setStyleSheet("color: gray;")
            self.grid_layout.addWidget(empty, 0, 0, 1, columns)
            return

        for idx, tool in enumerate(tools):
            if not tool.get("enabled", True):
                continue
            row = idx // columns
            col = idx % columns
            btn = ToolIconButton(tool, self._scripts_dir)
            self.grid_layout.addWidget(btn, row, col)
            self._tool_buttons[tool["id"]] = btn

    # ----------------------------------------------------------------
    # アップデート処理
    # ----------------------------------------------------------------

    def _on_update(self):
        if self._worker and self._worker.isRunning():
            return

        self.btn_update.setEnabled(False)
        self.progress_bar.show()
        self._set_status("アップデートを開始します...")

        self._worker = tool_manager.UpdateWorker(self)
        self._worker.progress.connect(self._set_status)
        self._worker.tool_done.connect(self._on_tool_done)
        self._worker.finished.connect(self._on_update_finished)
        self._worker.error.connect(self._on_update_error)
        self._worker.start()

    def _on_tool_done(self, tool_id: str):
        """1件のツールが更新されたらボタンを即時更新する。"""
        if tool_id in self._tool_buttons:
            self._tool_buttons[tool_id].mark_updated()

    def _on_update_finished(self, manifest: dict):
        self._manifest = manifest
        self._populate_grid()   # 新ツールが追加されていれば再描画
        self._set_status(f"アップデート完了 ({len(manifest.get('tools', []))} ツール)")
        self._finalize_update()

    def _on_update_error(self, message: str):
        self._set_status(f"エラー: {message}")
        QtWidgets.QMessageBox.warning(self, "アップデートエラー", message)
        self._finalize_update()

    def _finalize_update(self):
        self.btn_update.setEnabled(True)
        self.progress_bar.hide()

    def _set_status(self, msg: str):
        self.status_label.setText(msg)


# ------------------------------------------------------------------
# 表示エントリポイント
# ------------------------------------------------------------------

def show():
    """ランチャーウィンドウを表示する（シェルフボタンから呼び出す）。"""
    # 既存ウィンドウがあれば前面に出すだけ
    for widget in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(widget, ToolLauncherUI):
            widget.raise_()
            widget.activateWindow()
            return widget

    if MAYA_AVAILABLE:
        try:
            ptr = omui.MQtUtil.mainWindow()
            main_win = wrapInstance(int(ptr), QtWidgets.QWidget)
            win = ToolLauncherUI(parent=main_win)
        except Exception:
            win = ToolLauncherUI()
    else:
        win = ToolLauncherUI()

    win.setWindowFlags(win.windowFlags() | QtCore.Qt.Window)
    win.show()
    return win


if __name__ == "__main__":
    # Maya外でのデバッグ用
    import sys as _sys
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(_sys.argv)
    w = show()
    _sys.exit(app.exec_())
