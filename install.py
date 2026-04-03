"""
install.py - ToolLauncher インストーラー

Mayaのスクリプトエディター(Python)から実行することで
シェルフボタンを自動作成します。

【使い方】
Maya Script Editor (Python) で以下を実行：

    import runpy
    runpy.run_path(r"C:/Users/ユーザー名/Documents/maya/scripts/ToolLauncher/install.py")
"""
import os
import sys

# 配置パスは固定
_SCRIPTS_DIR = os.path.join(os.path.expanduser("~"), "Documents", "maya", "scripts")
_THIS_DIR    = os.path.join(_SCRIPTS_DIR, "ToolLauncher")

# Maya は起動時に ~/Documents/maya/scripts を自動で sys.path に追加するため
# userSetup.py への追記は不要です

_SHELF_CMD = """\
import ToolLauncher.launcher
ToolLauncher.launcher.show()
"""

# ------------------------------------------------------------------
# Mayaのシェルフに登録
# ------------------------------------------------------------------
try:
    import maya.cmds as cmds
    import maya.mel  as mel

    SHELF_NAME   = "ToolLauncher"
    BUTTON_LABEL = "Launcher"

    if not cmds.shelfLayout(SHELF_NAME, exists=True):
        mel.eval(f'addNewShelfTab "{SHELF_NAME}"')
        print(f"[ToolLauncher] シェルフを作成: {SHELF_NAME}")

    existing = cmds.shelfLayout(SHELF_NAME, query=True, childArray=True) or []
    already  = any(
        cmds.shelfButton(b, query=True, label=True) == BUTTON_LABEL
        for b in existing
        if cmds.objectType(b) == "shelfButton"
    )

    if not already:
        cmds.shelfButton(
            parent=SHELF_NAME,
            label=BUTTON_LABEL,
            command=_SHELF_CMD,
            annotation="Tool Launcher を開く",
            image="menuIconDisplay.png",
            sourceType="python",
        )
        print(f"[ToolLauncher] シェルフボタンを作成: '{BUTTON_LABEL}' on '{SHELF_NAME}'")
    else:
        print(f"[ToolLauncher] シェルフボタン '{BUTTON_LABEL}' は既に存在します")

    print("[ToolLauncher] インストール完了!")

except ImportError:
    print("[ToolLauncher] Maya が見つかりません。Mayaのスクリプトエディターから実行してください。")
