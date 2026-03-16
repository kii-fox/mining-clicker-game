# Mining Clicker (Beta)

ブラウザで遊べるシンプルなクリック型採掘ゲームです。  
プレイヤーは採掘を行い素材を集め、ツールを製作・研究してより効率的に採掘を進めていきます。

現在は **ベータ版**として基本的なゲームループが実装されています。

---

# ゲーム概要

Mining Clicker は以下の流れで進行します。

1. 採掘ボタンをクリックして素材を入手
2. 素材を使ってツールを製作
3. 研究を行い新しいツールを解放
4. より強力なツールで採掘効率を上げる

---

# 実装済み機能（Beta）

## 採掘システム
- クリックによる採掘
- ツール耐久値システム
- ツール未装備時は採掘不可

## 素材
現在実装されている素材

- stone
- coal
- iron

## ツール
ツールには耐久値があり、採掘すると消耗します。

例

- wood_pickaxe
- stone_pickaxe
- iron_pickaxe

## 装備システム
所持ツールの中から装備を切り替え可能。

## クラフト
素材を消費してツールを作成できます。

## 研究システム
研究を完了すると新しいツールがクラフト可能になります。

例


鉄ピッケル研究
必要素材:
stone 100
iron 10


---

# 技術構成

## Backend
- Python
- Flask

## Frontend
- HTML
- CSS
- JavaScript

## Database
- Google Firestore

---

# データ構造（Firestore）


users
└ UID
├ materials
│ └ data
│ ├ stone
│ ├ coal
│ └ iron
│
├ tools
│ └ tool documents
│
└ research
└ research documents


マスターデータ


tool_master
research_master
material_master


---

# API

主なエンドポイント


POST /mine
採掘を実行

GET /materials
素材取得

GET /tools
ツール一覧取得

POST /tools/craft
ツール製作

POST /tools/equip
ツール装備

POST /research
研究実行


---

# 今後の予定

ベータ版以降では以下の機能追加を予定しています。

- 採掘ログ表示
- レアドロップ
- 新素材
- 新ツール
- 自動採掘
- バランス調整
- UI改善

---

# 開発状況

現在のバージョン


Beta


実装済みの基本ゲームループ


採掘 → 素材収集 → 製作 → 研究 → 強化


---

# ライセンス

個人開発プロジェクト

# Setup

pip install -r requirements.txt
python app.py