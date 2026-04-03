# ToolLauncher

Maya 用ツールランチャーです。  
GitHub で管理されたツール一覧をボタン表示し、クリックで起動・Update ボタンで最新版を取得できます。

---

## 導入手順

### 1. ToolLauncher をダウンロード

[ToolLauncher.zip](https://github.com/moideco/ToolLauncher/releases/latest/download/ToolLauncher.zip) からダウンロードして展開してください。

### 2. 所定の場所に配置

以下のパスに `ToolLauncher` フォルダごと配置してください。

```
C:\Users\ユーザー名\Documents\maya\scripts\ToolLauncher\
```

### 3. Maya にインストール

Maya を起動し、**Script Editor（スクリプトエディター）** を開きます。  
言語を **Python** に切り替えて以下を実行してください。

```python
import ToolLauncher.install
ToolLauncher.install.run()
```

実行すると **ToolLauncher シェルフ** が自動作成され、`Launcher` ボタンが追加されます。


---

## 使い方

### ツールを起動する

シェルフの `Launcher` ボタンをクリックするとランチャーウィンドウが開きます。  
ツール名のボタンをクリックするとそのツールが起動します。

> まだツールがダウンロードされていない場合、ボタンはグレーアウトして表示されます。  
> **Update ボタン**を押してツールを取得してください。

### ツールをアップデートする

ランチャーウィンドウの **Update** ボタンをクリックしてください。  
以下の 3 段階が順に実行されます。

| Stage | 内容 |
|---|---|
| 1 / 3 | ランチャー本体の更新（差分がある場合のみ） |
| 2 / 3 | 共通ツールリスト（manifest.json）の取得 |
| 3 / 3 | 各ツールスクリプトの取得・更新 |

ランチャー本体に更新があった場合はウィンドウが閉じます。シェルフの `Launcher` ボタンを再クリックすると最新版で起動します。

インターネット接続が必要です。オフライン時は前回のキャッシュから起動します。

### 全体向けツールの追加申請

共通ランチャーへのツール追加は管理者が `manifest.json` を更新します。  
追加を希望する場合は管理者へ申請してください。

---

## 個人用ツールリスト（User Manifest）

プロジェクト固有のツールや個人で使用するツールは、**User Manifest** として追加できます。  
User Manifest はローカルに保存された JSON ファイルで、リポジトリには影響しません。

### 追加方法

1. ランチャー右上の **⚙ ボタン** をクリック
2. **Add File...** でJSON ファイルを選択
3. バリデーションが通れば登録完了
4. **Update** ボタンで内容を反映

---

### User Manifest の書き方

ファイル名は任意です（例: `ProjectA.json`、`testScript.json` など）。  
以下のフォーマットで記述してください。

#### LAN サーバー上のスクリプトを使う場合

```json
{
  "version": "1.0.0",
  "updated": "2026-04-03",
  "tools": [
    {
      "id": "任意のID",
      "name": "任意の名前",
      "description": "ツールの説明",
      "version": "1.0.0",
      "author": "必要場合は制作者名",
      "enabled": true,
      "scripts": [
        {
          "url": "\\\\192.168.255.255\\任意のディレクトリ\\任意のスクリプト名.py",
          "filename": "任意のスクリプト名.py"
        }
      ],
      "entry_module": "任意のスクリプト名",
      "entry_function": "show"
    }
  ]
}
```

#### GitHub リポジトリ上のスクリプトを使う場合

```json
{
  "version": "1.0.0",
  "updated": "2026-04-03",
  "tools": [
    {
      "id": "my_tool",
      "name": "My Tool",
      "description": "ツールの説明",
      "version": "1.0.0",
      "author": "author_name",
      "enabled": true,
      "scripts": [
        {
          "url": "https://raw.githubusercontent.com/author/repo/main/my_tool.py",
          "filename": "my_tool.py"
        }
      ],
      "entry_module": "my_tool",
      "entry_function": "show"
    }
  ]
}
```

### フィールド説明

| フィールド | 必須 | 説明 |
|---|---|---|
| `id` | ✓ | ツールの一意なID（英数字・アンダースコア） |
| `name` | ✓ | ランチャーに表示されるボタン名 |
| `description` | | ツールチップに表示される説明 |
| `enabled` | | `false` にするとランチャーに表示されない |
| `scripts[].url` | ✓ | スクリプトの取得元（HTTPS URL または UNC パス） |
| `scripts[].filename` | ✓ | Maya scripts フォルダに保存されるファイル名 |
| `entry_module` | ✓ | 起動時に import するモジュール名（`.py` 不要） |
| `entry_function` | ✓ | 起動時に呼び出す関数名 |

> **User Manifest は共通 manifest より優先されません。**  
> 共通 manifest に同じ `id` のツールが存在する場合、User Manifest 側は無視されます。

---

## 対応環境

| 項目 | バージョン |
|---|---|
| Maya | 2018 以降 |
| Python | 3.x |
