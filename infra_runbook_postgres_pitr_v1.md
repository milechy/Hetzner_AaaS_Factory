# Postgres PITR Runbook v1
最終更新: 2025-11-18

## 0. 目的

この Runbook は、AaaS Factory の本番系 Postgres に対して

- 日次フルバックアップ
- WAL アーカイブ
- Point-In-Time Recovery（PITR）
- DR リハーサル

を実施・運用するための **標準手順テンプレート** である。

対象:

- `factory-meta-db`（必須）
- 各 SaaS 本番 DB（推奨）

対象外:

- dev / preview / CI 用 DB（壊れたら再作成）

---

## 1. 用語

- **Main Postgres Server**: 本番 DB が動作しているサーバ
- **WAL Archive**: WAL ファイルを保存するストレージ（StorageBox / Object Storage / 別ボリューム）
- **Full Backup**: `pg_basebackup` 等で取得するベースバックアップ
- **PITR Server**: 復旧時に起動する新しい Postgres サーバ（または新コンテナ）

---

## 2. 前提構成（Factory 標準）

- OS: Ubuntu 22.04（例）
- Postgres: 15.x
- デプロイ: Docker または bare metal（どちらでもよいが、データディレクトリは専用ボリューム）
- ストレージ:
  - `/var/lib/postgresql/data`（データディレクトリ）
  - `/var/backups/postgres/{{DB_NAME}}`（フルバックアップ）
  - `/var/wal-archive/{{DB_NAME}}`（WALアーカイブ）
  - これらを定期的に Hetzner StorageBox / Object Storage に rsync or rclone

---

## 3. 初期セットアップ

### 3.1 Postgres 設定（`postgresql.conf`）

```conf
# PITR 有効化に必要
archive_mode = on
archive_command = 'test ! -f /var/wal-archive/{{DB_NAME}}/%f && cp %p /var/wal-archive/{{DB_NAME}}/%f'
wal_level = replica
max_wal_senders = 5
````

* `{{DB_NAME}}` は論理名（例: `factory-meta`）。
* `archive_command` は StorageBox / S3 を使う場合は `rclone copy` 等に置き換える。

設定変更後:

```bash
sudo systemctl restart postgresql
# or docker restart {{postgres_container_name}}
```

### 3.2 ディレクトリ作成

```bash
sudo mkdir -p /var/backups/postgres/{{DB_NAME}}
sudo mkdir -p /var/wal-archive/{{DB_NAME}}
sudo chown -R postgres:postgres /var/backups/postgres /var/wal-archive
```

---

## 4. 日次フルバックアップ

### 4.1 バックアップ取得コマンド（基本形）

```bash
sudo -u postgres pg_basebackup \
  -D /var/backups/postgres/{{DB_NAME}}/base_$(date +%Y%m%d_%H%M%S) \
  -F tar \
  -X none \
  -z \
  -P
```

* `-X none`：WAL は別途 archive_command に任せる
* `-F tar -z`：tar + gzip 形式

### 4.2 cron 例（毎日 01:00 実行）

`/etc/cron.d/pg_basebackup_{{DB_NAME}}`:

```cron
0 1 * * * postgres /usr/local/bin/factory_pg_basebackup_{{DB_NAME}}.sh >> /var/log/pg_basebackup_{{DB_NAME}}.log 2>&1
```

`/usr/local/bin/factory_pg_basebackup_{{DB_NAME}}.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

DB_NAME="{{DB_NAME}}"
BACKUP_DIR="/var/backups/postgres/${DB_NAME}/base_$(date +%Y%m%d_%H%M%S)"

pg_basebackup \
  -D "${BACKUP_DIR}" \
  -F tar \
  -X none \
  -z \
  -P

# 古いバックアップ削除（例: 14日より古いものを削除）
find /var/backups/postgres/${DB_NAME} -maxdepth 1 -type d -mtime +14 -print -exec rm -rf {} \;
```

---

## 5. WAL アーカイブ運用

### 5.1 保存期間ポリシー（例）

* 最低: **7日**
* 推奨: **14〜30日**
* 運用:

  * `find` で古い WAL を削除
  * StorageBox / S3 のライフサイクルルールで自動削除

### 5.2 古い WAL の削除例

```bash
find /var/wal-archive/{{DB_NAME}} -type f -mtime +14 -print -delete
```

---

## 6. PITR 復旧手順（本番インシデント）

### 6.1 事前に決めること

* **ロールバックしたい時刻**: 例) `2025-11-18 15:37:00+00`
* 対象 DB: `factory-meta-db` など
* 既存アプリの停止方法（Coolify / docker-compose）

### 6.2 新しい PITR Server の用意

1. 新しい VM or コンテナを起動（本番と同じ Postgres バージョン）
2. データディレクトリ（`/var/lib/postgresql/data_pitr`) を空の状態で作成
3. バックアップと WAL を復元用サーバにコピー

```bash
# フルバックアップ & WAL を復旧サーバへコピー（例: rsync）
rsync -avz backup-host:/var/backups/postgres/{{DB_NAME}}/base_YYYYMMDD_HHMMSS /var/tmp/base_backup
rsync -avz backup-host:/var/wal-archive/{{DB_NAME}} /var/wal-archive/{{DB_NAME}}
```

### 6.3 ベースバックアップ展開

```bash
mkdir -p /var/lib/postgresql/data_pitr
tar -xzf /var/tmp/base_backup/base.tar.gz -C /var/lib/postgresql/data_pitr
# 必要に応じて他の tar を展開
chown -R postgres:postgres /var/lib/postgresql/data_pitr
```

### 6.4 `postgresql.conf` / `postgresql.auto.conf` 調整

* `archive_mode` や `archive_command` は OFF または適宜調整
* `data_directory` が `data_pitr` を指すように確認

### 6.5 `recovery.conf` または `standby.signal` 等の設定

Postgres 15では `postgresql.conf` 内の `recovery_target_time` などで指定する。

`/var/lib/postgresql/data_pitr/postgresql.conf` に追記:

```conf
restore_command = 'cp /var/wal-archive/{{DB_NAME}}/%f %p'
recovery_target_time = '2025-11-18 15:37:00+00'
recovery_target_action = promote
```

### 6.6 PITR 実行

```bash
sudo -u postgres pg_ctl -D /var/lib/postgresql/data_pitr start
# ログを確認し、指定の時刻まで WAL がリプレイされることを確認
```

リプレイが完了すると、自動的に promote され、通常の Postgres として稼働する。

### 6.7 アプリ側の切り替え

* Coolify / docker-compose の DB 接続先を `PITR Server` に切り替える
* Readiness を確認した上でアプリを再起動
* 既存の DB サーバは停止 or 別名に変更（誤接続防止）

---

## 7. PITR リハーサル（DR Drill）

### 7.1 目的

* **いざという時に本当に復旧できるか**を定期的に検証する。
* BackupAgent のレポート内容と実際の手順の乖離をなくす。

### 7.2 実施頻度（推奨）

* 四半期ごと（3ヶ月に1回）
* Factory の大きな変更（DB schema 大改修）の前後

### 7.3 手順サマリ

1. 本番と同じバックアップ + WAL セットを用いて、別サーバで PITR 実行
2. 復元した DB に対して:

   * `SELECT count(*)` など基本チェック
   * 主要テーブルの件数比較
3. 問題なければ、PITR 手順を `reports/backup/pg_pitr_drill_YYYYMMDD.md` に記録
4. SelfDevAgent / BackupAgent にレポートを渡し、自動チェック用メトリクスに反映

---

## 8. モニタリング & アラート

（ここは MonitoringAgent / HealthDashboardAgent と連携する想定でテンプレだけ定義）

監視すべき項目:

* フルバックアップの成功 / 失敗（直近 N 日）
* WAL Archive のサイズ / 保存期間
* `archive_command` のエラー有無
* ディスク使用率（データ / WAL / バックアップ）

アラート例:

* 直近 24 時間でバックアップ失敗あり
* WAL Archive がポリシーより短い日数しか残っていない
* バックアップディスクが 80%以上使用中

---

## 9. 新しい DB を PITR 対象にするチェックリスト

1. `infra_master` に DB 名と PITR 対象フラグを追加したか
2. `postgresql.conf` に `archive_mode` / `archive_command` を設定したか
3. WAL / Backup のディレクトリを作成し、権限を付与したか
4. 日次バックアップ cron（または systemd timer）を設定したか
5. 一度テストバックアップを取得し、Restore 手順を試したか
6. Monitoring / Alert に対象 DB を追加したか

---

# END

```

---