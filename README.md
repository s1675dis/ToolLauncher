# ToolLauncher

Maya 用ツールランチャーです。  
GitHub 上で管理されているツールを一覧表示し、アイコンクリックで起動・アップデートボタンで最新版をダウンロードできます。

---

## 導入手順

### 1. ToolLauncher をダウンロード

任意のフォルダに `ToolLauncher` フォルダごと配置してください。

```
任意のフォルダ/
└── ToolLauncher/   ← このリポジトリをここに置く
```

**Git を使う場合**

```bash
cd 任意のフォルダ
git clone https://github.com/moideco/ToolLauncher.git
```

**ZIP でダウンロードする場合**

[Code → Download ZIP](https://github.com/moideco/ToolLauncher/archive/refs/heads/main.zip) からダウンロードして展開してください。  
フォルダ名が `ToolLauncher-main` になる場合は `ToolLauncher` にリネームしてください。

---

### 2. Maya にインストール

Maya を起動し、**Script Editor（スクリプトエディター）** を開きます。  
言語を **Python** に切り替えて、以下を実行してください。

```python
import runpy
runpy.run_path(r"C:/YOUR_PATH/ToolLauncher/install.py")
```

> `C:/YOUR_PATH/` の部分は実際の配置場所に合わせて変更してください。

実行すると **ToolLauncher シェルフ** が自動作成され、`Launcher` ボタンが追加されます。

---

### 3. Maya 起動時に自動で読み込む（推奨）

インストール実行後、Script Editor に以下のようなスニペットが表示されます。

```python
# ---- ToolLauncher: パス設定 ----
import sys
_tl = r"C:/YOUR_PATH"
if _tl not in sys.path:
    sys.path.insert(0, _tl)
# --------------------------------
```

これを Maya の `userSetup.py` に追記することで、Maya 起動時に自動でパスが設定されます。

`userSetup.py` の場所：

| OS | パス |
|---|---|
| Windows | `C:/Users/ユーザー名/Documents/maya/scripts/userSetup.py` |
| Mac | `/Users/ユーザー名/Library/Preferences/Autodesk/maya/scripts/userSetup.py` |

ファイルが存在しない場合は新規作成してください。

---

## 使い方

### ツールを起動する

シェルフの `Launcher` ボタンをクリックするとランチャーウィンドウが開きます。  
ツールのアイコンをクリックするとそのツールが起動します。

### ツールをアップデートする

ランチャーウィンドウの **「アップデート」** ボタンをクリックしてください。

- GitHub から最新のツール情報（`manifest.json`）を取得します
- 各ツールの最新スクリプトを Maya の scripts フォルダへダウンロードします
- 新たに追加されたツールも自動で表示されます

インターネット接続が必要です。オフライン時は前回のキャッシュから起動します。

---

## 対応環境

| 項目 | バージョン |
|---|---|
| Maya | 2018 以降 |
| Python | 3.x |

---

## 登録ツールを追加したい場合

`manifest.json` の `tools` 配列にエントリを追加してください。

```json
{
  "id": "your_tool_id",
  "name": "Your Tool",
  "description": "ツールの説明",
  "version": "1.0.0",
  "author": "author_name",
  "repository": "https://github.com/author/your_tool",
  "enabled": true,
  "icon_url": "アイコン画像のURL（省略可）",
  "maya_icon": "MayaアイコンのファイルP名（省略可）",
  "scripts": [
    {
      "url": "https://raw.githubusercontent.com/author/your_tool/main/your_tool.py",
      "filename": "your_tool.py"
    }
  ],
  "entry_module": "your_tool",
  "entry_function": "show"
}
```

追加後に `manifest.json` を push すれば、ユーザーはアップデートボタンを押すだけで新ツールが使えるようになります。
