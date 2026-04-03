"""
install.py - ToolLauncher インストーラー

Mayaのスクリプトエディター(Python)から以下を実行してください：

    import ToolLauncher.install
    ToolLauncher.install.run()
"""

_SHELF_CMD = """\
import sys
for _k in list(sys.modules.keys()):
    if _k.startswith('ToolLauncher'):
        del sys.modules[_k]
import ToolLauncher.launcher
ToolLauncher.launcher.show()
"""


def run():
    """シェルフボタンを作成する。何度でも実行可能。"""
    try:
        import maya.cmds as cmds
        import maya.mel  as mel

        SHELF_NAME   = "ToolLauncher"
        BUTTON_LABEL = "Launcher"

        if not cmds.shelfLayout(SHELF_NAME, exists=True):
            mel.eval(f'addNewShelfTab "{SHELF_NAME}"')
            print(f"[ToolLauncher] シェルフを作成: {SHELF_NAME}")

        # 既存ボタンを削除して再作成（常に最新のコマンドで上書き）
        existing = cmds.shelfLayout(SHELF_NAME, query=True, childArray=True) or []
        for b in existing:
            try:
                if cmds.shelfButton(b, query=True, label=True) == BUTTON_LABEL:
                    cmds.deleteUI(b)
                    break
            except Exception:
                pass

        cmds.shelfButton(
            parent=SHELF_NAME,
            label=BUTTON_LABEL,
            command=_SHELF_CMD,
            annotation="Tool Launcher を開く",
            image="menuIconDisplay.png",
            sourceType="python",
        )
        print("[ToolLauncher] インストール完了!")

    except ImportError:
        print("[ToolLauncher] Maya が見つかりません。Mayaのスクリプトエディターから実行してください。")
