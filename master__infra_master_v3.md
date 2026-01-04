```markdown
# Factory Infrastructure Master — v3  
Hetzner × AaaS 自動開発ファクトリー  
最終更新: 2025-11-19

---

# 0. 目的

本ドキュメントは AaaS Factory のインフラに関する  
**完全な Single Source of Truth（SSOT）** であり、以下を定義する：

- Hetzner サーバ設計（CPU/メモリ/ネットワーク）
- ネットワーク構成（Linux Networking / Docker Networking）
- セキュリティ構成（Firewall / SSH / Zero Trust）
- デプロイ方式（Docker / Coolify）
- Backup / PITR（Postgres）
- Factory ランナー（GitHub Runner / Mac Runner）
- Observability / Metrics

本 v3 では新たに **Linux Networking セクション** を統合し、  
infra_master_v2 を完全上位互換で再構築する。

---

# 1. サーバ設計（Hetzner Cloud）

## 1.1 最適構成（Factory 本体）

- CX32（8 vCPU / 32GB RAM）  
  → 24/365 稼働の Factory ノード  
- Dedicated vCPU 化（CCX21+ 以上）も推奨  
- ストレージ：  
  - NVMe SSD  
  - 必要に応じて Volume をアタッチ  
- ネットワーク：  
  - IPv4（必須）  
  - IPv6（推奨）  

**理由**  
SelfDevAgent / RAG / docker compose / Coolify の稼働に必要。

---

# 2. Linux Networking（v3 新規セクション）

このセクションは、Factory の安定運用に不可欠な  
**Linux のネットワーク基礎構造**を正しく理解するための基礎を提供する。

Factory の特徴：

- self-host（Hetzner）  
- Docker ベース  
- ランナー / SaaS / DB / Coolify がすべて同一ネット上で連携  
- Zero Trust / Overlay Network（v4）を計画

そのため、Linux networking の理解は SSOT として必須。

---

## 2.1 ip コマンドの基本

Linux では、ネットワーク情報・操作は  
すべて **netlink（カーネルのネットワークサブシステム）** により一元管理される。

ip コマンドはこれへのフロントエンド。

### よく使う構文：

```

ip addr            # NICのIPアドレス一覧
ip link            # NIC一覧 (UP/DOWN, MTU)
ip route           # ルーティングテーブル
ip neigh           # ARP/NDP

```

### 重要ポイント

- `lo` はローカルループバック  
- `eth0`（Hetznerでは `ens10` など）は物理NIC  
- Docker が作成する仮想NICは **veth** として現れる

---

## 2.2 veth ペア（Docker の中核）

Docker コンテナはホストと **veth ペア** を使って通信する。

```

vethXXXX <--> vethYYYY

```

- 一方がコンテナ側  
- もう一方がホスト側（bridge へ接続）

特徴：

- パイプのように 1対1  
- 片方が消えるともう片方も消える  
- Docker が自動生成/削除

---

## 2.3 bridge（docker0）

Docker が自動作成する仮想スイッチ。

```

[ container veth ]──┐
[ container veth ]──┼── docker0 ── eth0 ── Internet
[ container veth ]──┘

```

- L2 スイッチのように振る舞う  
- 172.17.0.0/16 がデフォルト  
- NAT（SNAT）で外部に出る

Factory において：

- Coolify が使う network  
- SaaS が使う backend network  
- DB（Postgres）も同ネットワーク上で通信

---

## 2.4 ルーティング（ip route）

例：

```

default via 172.31.1.1 dev eth0
172.17.0.0/16 dev docker0  proto kernel

```

Factory の重要点：

- SaaS → DB は docker0 の内部通信  
- ホスト → インターネットは eth0 の default route  
- Runner → SaaS の境界がルーティング上で明瞭

---

## 2.5 NAT（iptables/nftables）

Docker はホスト側で自動的に以下を設定：

- MASQUERADE（SNAT）  
- DNAT（ポートフォワード）

Factory では：

- Coolify が自動で pf を構成  
- Caddy / Traefik が 80/443 を管理  
- firewall は ufw / nftables で最小構成に絞る

---

## 2.6 Docker Network の種類と Factory での使い分け

### bridge（デフォルト）

Factory の基本ネットワーク。

### host

パフォーマンス重視時に使うが、Factory では原則非推奨。

### overlay（将来）

Factory v4 で multi-host runner の際に利用予定。

### macvlan（将来）

DB とバックエンドを分離させる場合に採用検討。

---

## 2.7 SaaS のネットワーク設計（Factory 標準）

SaaS（Next.js / Backend / DB）は以下構成：

```

[ Next.js ]──┐
[ Backend ]──┼── factory_app_net (bridge)
[ Postgres ]─┘

```

- 外部公開は Caddy / Coolify  
- 内部通信は factory_app_net で限定  
- DBは外部公開しない

---

## 2.8 Zero Trust（v4 予定）

Factory v4 では次を検討：

- Tailscale / WireGuard  
- Multi-host runner 連結  
- Service Mesh（軽量版）

---

# 3. セキュリティ構成

## 3.1 SSH

- root login 禁止  
- 秘密鍵のみ許可  
- Fail2ban（任意）  
- TOTP (v4 で検討)

## 3.2 Firewall（ufw/nftables）

- 22 (SSH)  
- 80,443 (Caddy / Coolify)  
- 5432 (Postgres → internal network 限定)  
- 3000, 8000, 9000 など（internal limited）

---

# 4. Docker / Coolify

- Docker Engine を標準化  
- Coolify はサービスオーケストレーションに使用  
- SaaS は Coolify の GitHub Deploy で自動化  
- Factory 自体も Coolify で管理可能

---

# 5. Database（Postgres / PITR）

## 5.1 Postgres

- バージョン：15 or 16  
- StorageBox or Volume を推奨  
- Point-in-Time Recovery（PITR）対応

## 5.2 PITR（master__infra_runbook_postgres_pitr_v1）

- WAL-G or wal-g-rs  
- S3互換オブジェクトストレージ  
- cron + basebackup  
- recovery.conf による時点復旧

---

# 6. Backup & Storage

- StorageBox（rsync / borg）  
- Object Storage（WAL-G）  
- snapshots（Hetzner Cloud）

---

# 7. Observability（Monitoring/Logging）

- Uptime Kuma（Status/Health Check）  
- Grafana（v4）  
- Prometheus（v4）  
- container logs（Coolify）  
- agent success ratio（SelfDevAgent management）

---

# 8. runner（self-hosted runner）

## 8.1 Hetzner runner

- Docker runner（Linux x86）  
- concurrency=2〜4  
- ephemeral runner推奨（v4）  

## 8.2 Mac runner（iOSビルド用）

- Mac mini  
- Fastlane  
- app signing  
- 拡張 runner（複数iPhone）も検討可

---

# 9. infra_master 更新ポリシー

- バージョンは v3, v4 ... と単調増加  
- SelfDevAgent は人間に  
  「関連するマスターを更新しますか？」  
  と確認してから次版を生成  
- 過去バージョンは archive ディレクトリへ保存

---

# END
```

---