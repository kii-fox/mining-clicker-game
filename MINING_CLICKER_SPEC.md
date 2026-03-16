# MINING_CLICKER_SPEC.md
# マイニングクリッカー 設計書（MVP版）

---

# 1. 概要

クリック操作によって素材を収集し、収集素材を用いてツールを作成・強化し、より効率的に採掘を行うWebゲーム。

本ゲームに明確なクリア条件は存在しない。
継続的な収集・強化・効率化を目的とするインクリメンタル型ゲームである。

---

# 2. ゲームルール

- クリックごとに素材を獲得する
- 一定確率で鉱石がドロップする
- 素材を消費してツールを作成できる
- ツールには耐久値が存在する
- 採掘ごとに耐久値が減少する
- 耐久値が0になると使用不可
- 修理により耐久値を回復可能
- 同一ツールは最大10個まで所持可能
- 同時に1種類のみ装備可能
- 未装備時はツール効果を発揮しない

---

# 3. ユーザー機能

- UID（自動生成）+ パスワードによる認証
- 複数端末からアクセス可能
- 同時ログイン不可（サーバー側制御）
- 非同期通信（AJAX）による状態更新
- 採掘ロジックは完全サーバー管理（不正対策）

---

# 4. 画面設計（MVP）

## 4.1 ゲーム画面

- 採掘ボタン（中央配置）
- 素材一覧表示（インベントリ）
- 装備中ツール表示
  - 耐久値（数値またはゲージ）
- バッグメニュー
  - 所持ツール一覧
  - 作成ボタン
  - 修理ボタン

---

# 5. データベース設計

## 5.1 設計方針

- ユーザーデータとマスターデータを分離
- 正規化を意識した構造
- 将来的な拡張を考慮
- バランス調整をDB側で可能にする

---

# 5.2 ユーザーテーブル

## users

| カラム名 | 型 | 制約 | 説明 |
|----------|------|------|------|
| id | INT | PK | ユーザーID |
| username | VARCHAR(50) | UNIQUE, NOT NULL | UID |
| password_hash | VARCHAR(255) | NOT NULL | ハッシュ化パスワード |
| created_at | DATETIME | NOT NULL | 作成日時 |
| is_logged_in | BOOLEAN | DEFAULT FALSE | ログイン状態 |

---

## save_data

| カラム名 | 型 | 制約 | 説明 |
|----------|------|------|------|
| id | INT | PK | セーブデータID |
| user_id | INT | FK(users.id) | ユーザーID |
| device_name | VARCHAR(100) | | 端末識別名 |
| last_login_at | DATETIME | | 最終ログイン |
| created_at | DATETIME | NOT NULL | 作成日時 |

users 1 : N save_data

---

# 5.3 マスターテーブル

## material_master

| カラム名 | 型 | 制約 | 説明 |
|----------|------|------|------|
| id | INT | PK | 主キー |
| material_type | VARCHAR(50) | UNIQUE, NOT NULL | 素材識別子 |
| display_name | VARCHAR(100) | NOT NULL | 表示名 |
| base_drop_rate | FLOAT | NOT NULL | 基本ドロップ率 |
| is_rare | BOOLEAN | DEFAULT FALSE | レア判定 |
| description | TEXT | | 説明 |
| created_at | DATETIME | NOT NULL | 作成日時 |

---

## tool_master

| カラム名 | 型 | 制約 | 説明 |
|----------|------|------|------|
| id | INT | PK | 主キー |
| tool_type | VARCHAR(50) | UNIQUE, NOT NULL | ツール識別子 |
| display_name | VARCHAR(100) | NOT NULL | 表示名 |
| base_durability | INT | NOT NULL | 最大耐久値 |
| durability_cost_per_mine | INT | NOT NULL | 採掘時消費耐久 |
| mining_power | FLOAT | DEFAULT 1.0 | 採掘倍率 |
| required_materials | JSON | NOT NULL | 作成必要素材 |
| repair_materials | JSON | NOT NULL | 修理必要素材 |
| created_at | DATETIME | NOT NULL | 作成日時 |

---

# 5.4 ユーザーデータ（トランザクション）

## materials

| カラム名 | 型 | 制約 | 説明 |
|----------|------|------|------|
| id | INT | PK | 主キー |
| save_data_id | INT | FK(save_data.id) | セーブID |
| material_master_id | INT | FK(material_master.id) | 素材ID |
| amount | INT | NOT NULL | 所持数 |

UNIQUE(save_data_id, material_master_id)

---

## tools

| カラム名 | 型 | 制約 | 説明 |
|----------|------|------|------|
| id | INT | PK | 主キー |
| save_data_id | INT | FK(save_data.id) | セーブID |
| tool_master_id | INT | FK(tool_master.id) | ツールID |
| durability | INT | NOT NULL | 現在耐久 |
| is_equipped | BOOLEAN | DEFAULT FALSE | 装備中 |

save_data 1 : N materials  
save_data 1 : N tools  

---

# 6. API設計（MVP）

## 認証系

POST /register  
POST /login  
POST /logout  

## ゲーム系

POST /mine  
GET /materials  
GET /tools  
POST /tools/craft  
POST /tools/repair  
POST /tools/equip  

※ 採掘処理・耐久減少・素材付与はすべてサーバー側で実行する

---

# 7. 拡張予定（MVP対象外）

- 研究システム（スキルツリー）
- 電力システム
- 自動採掘
- 素材取引
- レア素材追加
- 転生機能

---

# 8. 設計思想まとめ

- マスターデータとユーザーデータの分離
- 正規化されたDB設計
- サーバー主導ロジックによる不正対策
- 将来拡張を前提とした構造
- バランス調整をDBで管理可能
- MVPを小さく構築し段階的に拡張