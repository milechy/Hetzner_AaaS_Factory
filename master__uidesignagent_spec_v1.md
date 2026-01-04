# UIDesignAgent Specification v1  
Intent Engine Integration  
最終更新: 2025-11-19

---

# 0. 目的

UIDesignAgent は自然言語要件から  
**UI構成（ワイヤーフレーム → ページ構成 → コンポーネント構造）**  
を生成する。

本仕様では “Intent Engine” を使った  
UI Intent Normalizer を定義する。

---

# 1. Intent → UI Flow 変換

UIDesignAgent は自然言語から以下を抽出する：

- pages  
- components  
- states  
- flows  
- auth patterns  
- data-bound elements  
- CRUD operations  
- layout patterns  

---

# 2. UI Intent Normalizer（新規）

UIDesignAgent は以下の多段階意図理解を行う：

1. **Rewrite**  
   - UIに不要なノイズを除去  
   - 曖昧な要求を定義化  

2. **Group**  
   - sub-intents を page 単位へグループ化  
   - entity × action × user-flow の mapping

3. **Map**  
   - UIパターン（UI Kit Master）へマッピング  
   - 画面ごとの CRUD フローを構造化

4. **Validate**  
   - design_system_master と比較  
   - style/spacing/typography/components の整合確認

---

# 3. Output（UI構造）

UIDesignAgent は以下を JSON として生成：

```json
{
  "pages": [],
  "components": [],
  "flows": [],
  "layouts": [],
  "patterns": [],
  "data_bindings": []
}
````

これをもとに WebDevAgent / SwiftDevAgent が実装する。

---

# END

```

---