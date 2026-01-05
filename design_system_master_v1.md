# design_system_master_v1.md  
Design System – Master Specification (v1)  
最終更新: 2026-01-05

---

# 🎨 0. 概要（Purpose）

本ファイルは AaaS Factory 全プロジェクトにおける  
**UI/UX・デザイン・コンポーネントの唯一の真理（SSOT）**。

以下すべての基準を定義し、  
Next.js（Web）・SwiftUI（iOS）・テンプレート生成・エージェント開発  
すべてに一貫性を与える。

内容:

- Color / Typography / Spacing / Radius / Motion
- Light/Dark モード
- デザイントークン
- コンポーネント API（Button / Input / Modal 他）
- Next.js UI Kit ガイド
- SwiftUI UI Kit ガイド
- アクセシビリティ基準
- ファイル構成 / 命名規約

---

# 🎨 1. Naming Principles（命名思想）

## 1.1 Token Layering

デザイントークンは **3層で構造化** する。

1. **Core Token（生値）**  
   - 例: `--ds-color-blue-500: #3b82f6;`

2. **Semantic Token（意味）**  
   - 例: `--ds-color-primary: var(--ds-color-blue-600);`

3. **Component Token（用途）**  
   - 例: `--btn-bg-primary-default: var(--ds-color-primary);`

GPT / UI エージェントは **Semantic Token → Component Token** の順で参照する。

---

# 🎨 2. Color System（Light / Dark）

## 2.1 Core Palette

### Gray
`gray-0:#ffffff, 50:#f8fafc, 100:#f1f5f9, 200:#e2e8f0, 300:#cbd5e1, 400:#94a3b8, 500:#64748b, 600:#475569, 700:#334155, 800:#1f2937, 900:#0f172a, 950:#020617`

### Blue（Primary）
`#eff6ff, #dbeafe, #bfdbfe, #93c5fd, #60a5fa, #3b82f6, #2563eb, #1d4ed8, #1e40af, #1e3a8a`

### Green（Success）
`#ecfdf5 … #065f46`

### Yellow（Warning）
`#fefce8 … #854d0e`

### Red（Danger）
`#fef2f2 … #7f1d1d`

### Accent
Purple, Teal など拡張可能

---

## 2.2 Semantic Tokens（ライト/ダークで値が切り替わる）

### Light（抜粋）

–ds-surface-root: #ffffff;
–ds-surface-elev1: #ffffff;
–ds-surface-elev2: #f8fafc;

–ds-text-primary:#0f172a;
–ds-text-secondary:#334155;
–ds-text-muted:#64748b;

–ds-border:#e2e8f0;
–ds-border-strong:#cbd5e1;

–ds-color-primary:#2563eb;
–ds-color-secondary:#7c3aed;
–ds-color-accent:#0ea5a4;

–ds-color-success:#10b981;
–ds-color-warning:#f59e0b;
–ds-color-danger:#ef4444;

–ds-interactive-bg:#2563eb;
–ds-interactive-bg-hover:#1d4ed8;

–ds-focus-ring: 0 0 0 3px rgba(37,99,235,0.35);
–ds-scrim: rgba(0,0,0,0.45);

### Dark（抜粋）

–ds-surface-root:#0b1220;
–ds-surface-elev1:#0f1629;

–ds-text-primary:#e5e7eb;
–ds-text-secondary:#cbd5e1;

–ds-border:#1f2a44;

–ds-color-primary:#60a5fa;
–ds-color-secondary:#a78bfa;
–ds-color-accent:#5eead4;

–ds-interactive-bg:#60a5fa;
–ds-focus-ring: 0 0 0 3px rgba(96,165,250,0.45);
–ds-scrim: rgba(0,0,0,0.6);

---

# ✍️ 3. Typography

## 3.1 Font Families
- Sans: `Inter, SF Pro, Segoe UI, system-ui, sans-serif`
- Mono: `JetBrains Mono, SFMono, ui-monospace`

## 3.2 Scale（Major Third, 1.25）

| 名称 | px |
|------|------|
| Display-2 | 48.8px |
| Display-1 | 39.1px |
| H1 | 31.3px |
| H2 | 25px |
| H3 | 20px |
| Body | 16px |
| Subtext | 14px |
| Caption | 12px |

行間: 1.6（本文） / 1.25（見出し）

---

# 📐 4. Spacing / Radius / Elevation / Motion

## 4.1 Spacing（4px Grid）
`2, 4, 8, 12, 16, 24, 32, 48, 64`

## 4.2 Radius
`none:0, xs:2, sm:4, md:8, lg:12, xl:16, pill:9999`

## 4.3 Elevation（Shadow Tokens）

elev1: 0 1px 2px rgba(0,0,0,.06)
elev2: 0 2px 6px rgba(0,0,0,.08)
elev3: 0 8px 16px rgba(0,0,0,.10)
elev4: 0 16px 32px rgba(0,0,0,.12)
elev5: 0 24px 48px rgba(0,0,0,.14)

## 4.4 Motion

duration: fast:120ms, base:200ms, slow:320ms, modal:420ms
easing: standard:cubic-bezier(.2,0,.2,1)

# 🧩 4.5 Iconography（アイコン規約）

## 4.5.1 基本ルール
- 基準サイズ：**24px グリッド**（Web/SwiftUIともに同等の見え方になるよう正規化）
- 推奨サイズ：`12, 16, 20, 24, 32, 40`
- 線幅：1.5〜2px（同一プロダクト内で統一）
- 角：2px ラウンド（過度な装飾は避ける）

## 4.5.2 色と状態
- アイコン色は **Semantic Tokens** のみで表現する（直書き禁止）
  - 例：通常 `--ds-text-muted`、強調 `--ds-text-primary`、アクション `--ds-color-primary`
- 状態（hover/active/disabled/selected）は UI Kit の state に従い、Token で切替

## 4.5.3 デフォルトアイコンソース
- Primary / Default：**pqoqubbw/icons**
- 外部アイコンを追加する場合は、カテゴリ・線幅・角R・サイズ体系を本規約に揃えること

# 🧭 4.6 External References（非SSOT・参照のみ）
- **elevenlabs/ui**：AI SaaS の情報設計・密度・階層設計の参考（コンポーネント/色/値の流用は禁止）
- **react-grab**：Builder/Editor 系の実験的インタラクションの参考（共通UI Kitに含めない）
- **tigma**：設計支援ツール（ランタイムUIではないため SSOT 外）

---

# 🧬 5. デザイントークン（JSON Example）

```json
{
  "color": {
    "primary": { "light": "#2563eb", "dark": "#60a5fa" },
    "text": {
      "primary": { "light": "#0f172a", "dark": "#e5e7eb" }
    }
  },
  "radius": { "md": 8, "lg": 12 },
  "spacing": { "sm": 8, "md": 12, "lg": 16 },
  "motion": {
    "duration": { "base": 200 },
    "easing": { "standard": "cubic-bezier(.2,0,.2,1)" }
  }
}


⸻

🧱 6. コンポーネント API（全SaaSで共通）

6.1 Button
	•	Variants: solid | outline | ghost | soft | link
	•	Colors: primary | secondary | neutral | success | warning | danger
	•	Size: xs | sm | md | lg | xl
	•	Props:

type ButtonProps = {
  variant?: 'solid'|'outline'|'ghost'|'soft'|'link';
  color?: 'primary'|'secondary'|'neutral'|'success'|'warning'|'danger';
  size?: 'xs'|'sm'|'md'|'lg'|'xl';
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  loading?: boolean;
  fullWidth?: boolean;
}


⸻

6.2 Input

Slots:
	•	field
	•	label
	•	hint
	•	error
	•	leftIcon
	•	rightIcon

States:
default | focus | error | disabled

⸻

6.3 Select / Combobox
	•	keyboard navigation
	•	virtualization for large data sets

⸻

6.4 Checkbox / Radio / Switch

基本仕様：
	•	最小ヒット領域 40×40
	•	Tri-state 対応

⸻

6.5 Modal / Drawer
	•	focus trap 必須
	•	scrim は --ds-scrim
	•	Esc で閉じる

⸻

6.6 Table
	•	row-height: 48px
	•	hover: --ds-surface-elev2

⸻

6.7 その他の基本セット
	•	Tag / Chip
	•	Tooltip
	•	Popover
	•	Toast
	•	Tabs
	•	Breadcrumb
	•	Pagination
	•	Alert
	•	Skeleton
	•	Empty State

⸻

💻 7. Next.js（React）ガイドライン

7.1 CSS Variables（テーマ切替）

:root {
  --ds-surface-root:#fff;
  --ds-text-primary:#0f172a;
}
[data-theme="dark"] {
  --ds-surface-root:#0b1220;
  --ds-text-primary:#e5e7eb;
}

7.2 Tailwind連携

theme: {
  extend: {
    colors: {
      primary: "var(--ds-color-primary)"
    }
  }
}


⸻

📱 8. SwiftUI ガイドライン

8.1 Color Tokens

extension Color {
  static let primary = Color("primary")
  static let surfaceRoot = Color("surfaceRoot")
}

8.2 Font Tokens

extension Font {
  static let body = Font.system(size:16, weight:.regular)
  static let h1   = Font.system(size:31, weight:.semibold)
}

8.3 ButtonStyle（例）

struct DSButtonStyle: ButtonStyle {
  func makeBody(configuration: Configuration) -> some View {
    configuration.label
      .padding(12)
      .background(Color.primary)
      .cornerRadius(8)
      .opacity(configuration.isPressed ? 0.85 : 1.0)
  }
}


⸻

♿ 9. Accessibility（必須基準）
	•	コントラスト AA（4.5:1）
	•	ターゲットサイズ 44×44px
	•	フォーカスリング必須
	•	prefers-reduced-motion 準拠
	•	role="alert" / role="status" の使い分け

⸻

🗂 10. UI Kit 構造（推奨ディレクトリ）

ui/
 ├─ tokens/ (json, css-vars)
 ├─ react/
 │   ├─ primitives/
 │   ├─ composite/
 │   └─ hooks/
 └─ swiftui/
     ├─ Tokens/
     ├─ Components/
     └─ Utils/


⸻

🧭 11. GPT/エージェントが使用するルール
	1.	新しいSaaSのUIは必ず本 Design System に従うこと
	2.	デザイン変更はすべて v2, v3… として保存すること
	3.	UI設計チャットは常に本ファイルを参照すること
	4.	Next.js / SwiftUI のコード生成時は、このトークンとAPIを必ず使用する
	5.	テンプレ更新時は Self-Dev チャットに通知すること

⸻

END