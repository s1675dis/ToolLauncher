# ToolLauncher

Maya 用ツールランチャーです。  
GitHub 上で管理されているツールを一覧表示し、アイコンクリックで起動・アップデートボタンで最新版をダウンロードできます。

---

## 導入手順

### 1. ToolLauncher をダウンロード

[ToolLauncher.zip](https://github.com/moideco/ToolLauncher/releases/latest/download/ToolLauncher.zip) からダウンロードして展開してください。

### 2. 所定の場所に配置

以下のパスに `ToolLauncher` フォルダごと配置してください。

```
C:\Users\ユーザー名\Documents\maya\scripts\ToolLauncher\
```

配置後の構成：

```
C:\Users\ユーザー名\Documents\maya\scripts\
└── ToolLauncher\
    ├── __init__.py
    ├── config.py
    ├── install.py
    ├── launcher.py
    ├── manifest.json
    └── tool_manager.py
```

### 3. Maya にインストール

Maya を起動し、**Script Editor（スクリプトエディター）** を開きます。  
言語を **Python** に切り替えて、以下を実行してください。

```python
import ToolLauncher.install
```

実行すると **ToolLauncher シェルフ** が自動作成され、`Launcher` ボタンが追加されます。

> Maya は起動時に `Documents/maya/scripts/` を自動でパスに追加するため、追加設定は不要です。

---

## 使い方

### ツールを起動する

シェルフの `Launcher` ボタンをクリックするとランチャーウィンドウが開きます。  
ツールのアイコンをクリックするとそのツールが起動します。

### ツールをアップデートする

ランチャーウィンドウの **「アップデート」** ボタンをクリックしてください。

- GitHub から最新のツール情報を取得します
- 各ツールの最新スクリプトを `Documents/maya/scripts/` へダウンロードします
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
  "maya_icon": "Mayaアイコンのファイル名（省略可）",
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
