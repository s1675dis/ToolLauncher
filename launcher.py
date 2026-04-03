"""
ToolLauncher - Main Launcher UI
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


class ToolIconButton(QtWidgets.QToolButton):

    ICON_SIZE = config.ICON_SIZE

    STYLE = """
        QToolButton {
            background-color: #5d5d5d;
            border: 1px solid #3a3a3a;
            border-radius: 4px;
            padding: 6px 10px;
            color: #dddddd;
        }
        QToolButton:hover {
            background-color: #6e6e6e;
            border-color: #999999;
        }
        QToolButton:pressed {
            background-color: #4a4a4a;
        }
        QToolButton:disabled {
            background-color: #3c3c3c;
            color: #666666;
            border-color: #2e2e2e;
        }
    """

    def __init__(self, tool: dict, scripts_dir: str, parent=None):
        super().__init__(parent)
        self.tool        = tool
        self.scripts_dir = scripts_dir

        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.setIconSize(QtCore.QSize(self.ICON_SIZE, self.ICON_SIZE))
        self.setMinimumHeight(self.ICON_SIZE + 40)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setToolTip(tool.get("description", ""))
        self.setStyleSheet(self.STYLE)

        self._refresh()
        self.clicked.connect(self._launch)

    def _refresh(self):
        name      = self.tool.get("name", self.tool.get("id", "Tool"))
        installed = tool_manager.is_tool_installed(self.tool, self.scripts_dir)

        self.setText(name)
        self.setEnabled(installed)

        icon_path = tool_manager.get_cached_icon_path(self.tool)
        if icon_path and os.path.exists(icon_path):
            self.setIcon(QtGui.QIcon(icon_path))
        else:
            self._set_fallback_icon()

    def _set_fallback_icon(self):
        if MAYA_AVAILABLE:
            maya_icon = self.tool.get("maya_icon", "commandButton.png")
            self.setIcon(QtGui.QIcon(f":{maya_icon}"))
        else:
            self.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon))

    def mark_updated(self):
        self._refresh()

    def _launch(self):
        entry_module = self.tool.get("entry_module")
        entry_func   = self.tool.get("entry_function", "show")

        if not entry_module:
            QtWidgets.QMessageBox.warning(
                self, "Config Error",
                f"'entry_module' is not set for '{self.tool.get('name')}'."
            )
            return

        if self.scripts_dir not in sys.path:
            sys.path.insert(0, self.scripts_dir)

        try:
            if entry_module in sys.modules:
                del sys.modules[entry_module]
            __import__(entry_module)
            mod  = sys.modules[entry_module]
            func = getattr(mod, entry_func, None)
            if func is None:
                raise AttributeError(
                    f"'{entry_module}' has no function '{entry_func}'.\n"
                    f"Available: {[x for x in dir(mod) if not x.startswith('_')]}"
                )
            func()
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Launch Error",
                f"Failed to launch tool:\n\n{e}"
            )


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

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(4)
        root.setContentsMargins(8, 8, 8, 8)

        header = QtWidgets.QHBoxLayout()
        title  = QtWidgets.QLabel("Tool Launcher")
        f      = title.font()
        f.setBold(True)
        f.setPointSize(11)
        title.setFont(f)
        header.addWidget(title)
        header.addStretch()

        self.btn_update = QtWidgets.QPushButton("Update")
        self.btn_update.setFixedWidth(80)
        self.btn_update.setToolTip("Fetch the latest tools and launcher files from GitHub")
        self.btn_update.clicked.connect(self._on_update)
        header.addWidget(self.btn_update)
        root.addLayout(header)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFrameShadow(QtWidgets.QFrame.Sunken)
        root.addWidget(sep)

        self.scroll_area    = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.grid_container = QtWidgets.QWidget()
        self.grid_layout    = QtWidgets.QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(8)
        self.grid_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.scroll_area.setWidget(self.grid_container)
        root.addWidget(self.scroll_area)

        self.stage_label = QtWidgets.QLabel("")
        self.stage_label.setStyleSheet("font-weight: bold; font-size: 10px;")
        self.stage_label.hide()
        root.addWidget(self.stage_label)

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet("color: gray; font-size: 9px;")
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        root.addWidget(self.progress_bar)

    def _populate_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._tool_buttons.clear()

        tools   = self._manifest.get("tools", [])
        columns = config.GRID_COLUMNS

        if not tools:
            empty = QtWidgets.QLabel("No tools registered.\nPress \"Update\" to fetch the tool list.")
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

    def _on_update(self):
        if self._worker and self._worker.isRunning():
            return

        self.btn_update.setEnabled(False)
        self.progress_bar.show()
        self._set_status("Starting update...")

        self._worker = tool_manager.UpdateWorker(self)
        self._worker.stage.connect(self._on_stage)
        self._worker.progress.connect(self._set_status)
        self._worker.tool_done.connect(self._on_tool_done)
        self._worker.launcher_updated.connect(self._on_launcher_updated)
        self._worker.finished.connect(self._on_update_finished)
        self._worker.error.connect(self._on_update_error)
        self._worker.start()

    def _on_stage(self, num, label):
        self.stage_label.setText(f"[{num}/3] {label}")
        self.stage_label.show()

    def _on_launcher_updated(self):
        self._launcher_was_updated = True

    def _on_tool_done(self, tool_id: str):
        if tool_id in self._tool_buttons:
            self._tool_buttons[tool_id].mark_updated()

    def _on_update_finished(self, manifest: dict):
        self._manifest = manifest
        self._populate_grid()
        self._set_status(f"Update complete ({len(manifest.get('tools', []))} tools)")
        self._finalize_update()
        if getattr(self, "_launcher_was_updated", False):
            QtWidgets.QMessageBox.information(
                self, "Launcher Updated",
                "The launcher has been updated.\nPlease click the shelf button again to reload."
            )
            self.close()

    def _on_update_error(self, message: str):
        self._set_status(f"Error: {message}")
        QtWidgets.QMessageBox.warning(self, "Update Error", message)
        self._finalize_update()

    def _finalize_update(self):
        self.btn_update.setEnabled(True)
        self.progress_bar.hide()
        self.stage_label.hide()

    def _set_status(self, msg: str):
        self.status_label.setText(msg)


def show():
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
    import sys as _sys
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(_sys.argv)
    w = show()
    _sys.exit(app.exec_())
