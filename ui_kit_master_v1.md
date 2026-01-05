# ui_kit_master_v1.md
AaaS Factory – UI Kit Master Specification (v1)  
最終更新: 2026-01-05

---

# 🎯 Purpose（目的）

本ファイルは AaaS Factory における  
**React（Next.js）/ SwiftUI の共通 UI Component 仕様**  
を定義する “唯一の真理（SSOT）” である。

Design System（色・タイポ・間隔）は  
`design_system_master_v1.md` に定義されている。

本ファイルはその **コード実装バージョン** として：

- コンポーネント API（Props）
- 設計思想
- 構造（Primitives → Composite → Patterns）
- React / SwiftUI の具体的コードテンプレ
- 命名ルール
- UI Agent / Web Agent / Swift Agent の生成ルール

を統一的に管理する。

---

# 🧩 0. UI Kit Layer Model（3層構造）

Design System（色・タイポ・余白・バリアント）
↓
UI Kit（Primitives → Components → Patterns）
↓
SaaS UI（各 SaaS が利用）

UI Kit は 3層で構成：

1. **Primitive Components**  
   ボタン、入力、セレクト、トグルなど Design System 直結。

2. **Composite Components**  
   カード、フォーム、モーダル、テーブル、タブなど複合UI。

3. **Patterns（画面設計パターン）**  
   ダッシュボード、設定画面、空状態、ステップ UI など。

---

# 🎨 1. Base Design Tokens（React / SwiftUI 共通）

UI Kit では Design System Tokens を必ず参照する：

- `--ds-color-primary`  
- `--ds-text-primary`  
- `--ds-radius-md`  
- `--ds-spacing-lg`  
- `--ds-elevation-2`  
- `--ds-duration-base`

**React → CSS Variablesとして参照**  
**SwiftUI → Assets/ColorTokens.swift にマッピング**

---

# 🧱 2. React UI Kit（Next.js）仕様

## 2.1 ディレクトリ構造

ui/react/
├─ primitives/
│    ├─ Button.tsx
│    ├─ Input.tsx
│    ├─ Select.tsx
│    ├─ Checkbox.tsx
│    ├─ Switch.tsx
│    ├─ Badge.tsx
│    ├─ Tag.tsx
│    └─ TextArea.tsx
│
├─ composite/
│    ├─ Modal.tsx
│    ├─ Drawer.tsx
│    ├─ Table.tsx
│    ├─ Tabs.tsx
│    ├─ Card.tsx
│    └─ Pagination.tsx
│
└─ patterns/
├─ DashboardShell.tsx
├─ SettingsPage.tsx
└─ EmptyState.tsx

---

# 🎛️ 2.2 React: Base Button

## Props（すべてのSaaSで統一）

```ts
export type ButtonProps = {
  variant?: 'solid' | 'outline' | 'ghost' | 'soft' | 'link';
  color?: 'primary' | 'secondary' | 'neutral' | 'success' | 'warning' | 'danger';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  loading?: boolean;
  fullWidth?: boolean;
} & React.ButtonHTMLAttributes<HTMLButtonElement>;

実装テンプレ（抜粋）

export function Button({
  variant = 'solid',
  color = 'primary',
  size = 'md',
  loading = false,
  leftIcon,
  rightIcon,
  fullWidth,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center font-medium transition",
        `btn--${variant}`,
        `btn--${color}`,
        `btn--${size}`,
        fullWidth && "w-full"
      )}
      {...props}
    >
      {loading ? <Spinner /> : leftIcon}
      {children}
      {rightIcon}
    </button>
  );
}


⸻

✏️ 2.3 React: Input（TextField）

Props

type InputProps = {
  label?: string;
  error?: string;
  hint?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
} & InputHTMLAttributes<HTMLInputElement>;


⸻

🧩 2.4 Composite Components（例：Modal）

export function Modal({ open, onClose, title, children }) {
  if (!open) return null;

  return (
    <div className="ds-scrim">
      <div className="ds-modal">
        <div className="ds-modal-header">
          <h2>{title}</h2>
          <button onClick={onClose}>×</button>
        </div>
        <div>{children}</div>
      </div>
    </div>
  );
}


⸻

🗂 2.5 Patterns（React）

DashboardShell
	•	サイドバー + ヘッダー + content slot
	•	全 SaaS の共通レイアウト

SettingsPage
	•	タイトル + セクション + Form

EmptyState
	•	アイコン + タイトル + テキスト + CTAボタン

⸻

📱 3. SwiftUI UI Kit（iOS）仕様

3.1 ディレクトリ構造

ui/swiftui/
 ├─ Tokens/
 │    ├─ ColorTokens.swift
 │    ├─ FontTokens.swift
 │    └─ SpacingTokens.swift
 │
 ├─ Components/
 │    ├─ DSButton.swift
 │    ├─ DSTextField.swift
 │    ├─ DSSwitch.swift
 │    ├─ DSCard.swift
 │    ├─ DSTag.swift
 │    └─ DSModal.swift
 │
 └─ Patterns/
      ├─ DashboardView.swift
      ├─ SettingsView.swift
      └─ EmptyState.swift


⸻

📘 3.2 SwiftUI: DSButton（統一仕様）

struct DSButton: View {
    let title: String
    var variant: ButtonVariant = .solid
    var color: ButtonColor = .primary
    var size: ButtonSize = .md
    var loading: Bool = false
    var fullWidth: Bool = false
    var leftIcon: Image? = nil
    var rightIcon: Image? = nil
    var action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack {
                if loading { ProgressView() }
                else if let leftIcon = leftIcon { leftIcon }

                Text(title)
                    .font(FontTokens.button(size))

                if let rightIcon = rightIcon { rightIcon }
            }
            .frame(maxWidth: fullWidth ? .infinity : nil)
            .padding(SpacingTokens.padding(size))
            .background(ColorTokens.buttonBackground(color, variant))
            .foregroundColor(ColorTokens.buttonText(color, variant))
            .cornerRadius(8)
        }
    }
}


⸻

🔠 3.3 SwiftUI: DSTextField

struct DSTextField: View {
    var label: String?
    @Binding var text: String
    var hint: String?
    var error: String?
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            if let label = label {
                Text(label)
                    .font(.footnote)
            }
            TextField("", text: $text)
                .textFieldStyle(.roundedBorder)
            
            if let error = error {
                Text(error).foregroundColor(.red).font(.caption)
            } else if let hint = hint {
                Text(hint).foregroundColor(.gray).font(.caption)
            }
        }
    }
}


⸻

🗂 3.4 Patterns（SwiftUI）

DashboardView
	•	Sidebar + NavigationStack + Child content

SettingsView
	•	List + Section + Toggle/Button

EmptyState
	•	アセットアイコン + タイトル + 説明 + CTA

⸻

📏 4. 共通ルール（React / SwiftUI）
	1.	色/余白/タイポは Design System の Tokens を必ず参照
	2.	Variant / Size / State は必ず Props として提供
	3.	アクセシビリティ（A11y） は必須（focus ring, خوانみ上げ対応）
	4.	不要な style の直書きは禁止 → Token 経由
	5.	UI Kit の修正は TemplateAgent 経由で行う
	6.	SaaS固有UI は patterns フォルダに追加して良い
	•	ただし再利用できるUIはテンプレへ昇格

⸻

🧠 5. UIDesignAgent / WebDevAgent / SwiftDevAgent の使用ルール

UIDesignAgent
	•	UI Kit の primitives/composite/patterns を前提に画面設計
	•	Design System → UI Kit → Screen の順で参照

WebDevAgent
	•	UI Kit のReactコードテンプレを利用してコンポーネント生成
	•	不足があれば TemplateAgent へ昇格提案

SwiftDevAgent
	•	SwiftUI Kit を前提に View を実装
	•	Colors/Fonts は Token から読み込む

⸻

🔧 6. コンポーネント命名規則

React

Button
Input
Select
Card
DashboardShell
SettingsPage

SwiftUI

DSButton
DSTextField
DSCard
DashboardView
SettingsView


⸻

🔮 7. 将来拡張（v2以降）
	•	Chart Components
	•	Data Visualization Patterns
	•	Dark/Light 自動切替 Hook
	•	Mobile-first responsive Patterns
	•	Shadcn-like Generator
	•	SwiftUI + WidgetKit Kit
	•	React Native UI Kit（将来）

⸻

## 10. External Layout Template Packs

### 10.1 square-ui（Web専用 Layout Reference Pack）
square-ui は Next.js + shadcn/ui + Tailwind による OSS の UI レイアウトテンプレート集であり、  
本プロジェクトでは **「画面パターンの参照元（Webのみ）」として利用する**。

### 10.1.1 位置づけ
- コア UI Kit（Primitives / Composite / Patterns）とは分離  
- **Design System / UI Kit の SSOT ではない**  
- Dashboard / Email / Chat / Calendar / Tasks / Timeline 等、SaaSに頻出する画面構成の**参考パターン**として採用

### 10.1.2 利用ルール
1. **API・色名・Spacing・直接CSS値を流用しない**  
   - square-ui 内の class / カラー / 影 / 直接値は使用禁止  
   - 必ず Design System v1 の Semantic Tokens に置換すること

2. **コンポーネント構造だけを参照する**  
   - Card / Table / Sidebar / Email Viewer / Chat Window などの構造のみ採用  
   - 視覚デザイン（配色・半径・影）は DS に完全準拠させる

3. **UI Kit の Pattern と対応付けること**  
   - DashboardShell  
   - SettingsPage  
   - EmptyState  
   - Layout.Sidebar / Layout.Header  
   - Table / List / Menu など

4. **SwiftUI には直接転用しない**  
   - 情報構造（IA）とレイアウトのみ参考  
   - SwiftUI UI Kit で再構成する

### 10.1.3 A11y（アクセシビリティ）運用
square-ui 自体に A11y ガイドはなく、shadcn/ui に準拠しているため以下を必須とする：
- 全コンポーネントにフォーカスリング（`--ds-focus-ring`）を適用  
- コントラストは DS の基準（AA）に合わせて再調整  
- タッチ領域は最小 44×44px を保証  
- モバイルブレイク時の折りたたみ（Sidebar → Drawer）を UI Kit の Pattern として再定義

### 10.1.4 推奨使用例
- 新規SaaSの初期ワイヤーフレーム  
- Dashboard の KPI + Activity レイアウト  
- メール3ペイン構成（left nav / middle feed / right detail）  
- チャット（history + input box）  
- カレンダー（週間・月間）  
- Tasks / Kanban / Timeline（情報構造の参考）


### 10.2 Icon Sources（アイコンソース）
UI Kit のアイコンは Design System の Iconography ルールに従う。
本プロジェクトのデフォルトアイコンソースは以下とする：
- **pqoqubbw/icons**（Primary / Default）

#### 10.2.1 利用ルール
- SVG/ベクターは **24px グリッド**を基本とし、サイズは `12/16/20/24/32/40` のいずれかに正規化
- 色は **Semantic Tokens**（例: `--ds-text-muted`, `--ds-text-primary`, `--ds-color-primary`）のみで表現し、直接指定は禁止
- 状態（active/selected/disabled）は UI Kit 側の state に従い、色は Token で切替
- 装飾目的のアイコン乱用は禁止（情報階層のノイズを増やさない）

### 10.3 UX Reference Repos（UX参照用リポジトリ）
以下は SSOT ではなく、**情報設計・画面密度・階層設計**の参考としてのみ利用する。
- **elevenlabs/ui**（AI SaaS の入力→処理→出力の体験設計、密度/階層の参考）

#### 10.3.1 利用ルール
- コンポーネント API / class / 色 / spacing の直接流用は禁止
- 参照は **Pattern レベル（画面構造・導線）**に限定
- 反映する場合は、必ず UI Kit の Patterns にマッピングしてから採用

### 10.4 Interaction Utilities（実験的UX補助）
以下は共通 UI Kit には含めない（標準化すると一貫性を損なう可能性があるため）。
- **react-grab**（ドラッグ/掴み感のある操作の補助。Builder/Editor 系SaaSに限定）

#### 10.4.1 採用条件
- CRUD中心の一般SaaSでは原則不採用
- キーボード操作/フォーカス/タッチ操作を阻害しないこと（A11y優先）
- 採用する場合は SaaS 固有 UI として扱い、テンプレ昇格は原則禁止

### 10.5 Design Tooling（設計支援ツール）
以下は UI Kit/Design System の一部ではない（ランタイムUIではないため）。
- **tigma**（設計/抽出/検証の補助ツール群）

#### 10.5.1 利用ルール
- UI/UX成果物や UI Kit の SSOT を置き換えない
- 参照は設計プロセス上の補助に限定

⸻

END