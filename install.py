"""
install.py - ToolLauncher インストーラー

Mayaのスクリプトエディター(Python)から実行することで
・sys.path への追加
・シェルフボタンの作成
を行います。

【使い方】
Maya Script Editor (Python) で以下を実行：

    import runpy
    runpy.run_path(r"D:/Dropbox/scripts/ToolLauncher/install.py")
"""
import os
import sys

# ToolLauncher の親ディレクトリ（scripts フォルダ）を sys.path に追加
_THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_THIS_DIR)

if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)
    print(f"[ToolLauncher] sys.path に追加: {_PARENT_DIR}")
else:
    print(f"[ToolLauncher] 既に sys.path に存在: {_PARENT_DIR}")

# シェルフボタン起動コマンド（パスをハードコード）
_SHELF_CMD = f"""\
import sys
_p = r"{_PARENT_DIR}"
if _p not in sys.path:
    sys.path.insert(0, _p)
import importlib
import ToolLauncher.launcher as _tl
importlib.reload(_tl)
_tl.show()
"""

# ------------------------------------------------------------------
# Mayaのシェルフに登録
# ------------------------------------------------------------------
try:
    import maya.cmds as cmds
    import maya.mel  as mel

    SHELF_NAME  = "ToolLauncher"
    BUTTON_LABEL = "Launcher"

    # シェルフがなければ作成
    if not cmds.shelfLayout(SHELF_NAME, exists=True):
        mel.eval(f'addNewShelfTab "{SHELF_NAME}"')
        print(f"[ToolLauncher] シェルフを作成: {SHELF_NAME}")

    # 重複チェック
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
    print("[ToolLauncher] Maya が見つかりません。シェルフ設定をスキップします。")

# ------------------------------------------------------------------
# userSetup.py 追記用スニペットを表示
# ------------------------------------------------------------------
snippet = f"""\
# ---- ToolLauncher: パス設定 ----
import sys
_tl = r"{_PARENT_DIR}"
if _tl not in sys.path:
    sys.path.insert(0, _tl)
# --------------------------------"""

print("\n" + "=" * 60)
print("Maya 起動時に自動読み込みするには userSetup.py に追記してください:")
print("=" * 60)
print(snippet)
