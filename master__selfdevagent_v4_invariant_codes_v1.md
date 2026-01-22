# SelfDevAgent v4 Invariant Codes v1

| code | severity | condition | human_action |
| --- | --- | --- | --- |
| INV_ROUTER_PROOFS_MISSING | fix_required | router_proofs missing or fewer than 2 entries | Add writer and reviewer router proofs. |
| INV_ROUTER_PROOF_WRITER_MISSING | fix_required | no writer proof present in router_proofs | Add at least one writer proof. |
| INV_ROUTER_PROOF_REVIEWER_MISSING | fix_required | no reviewer proof present in router_proofs | Add at least one reviewer proof. |
| INV_ROUTER_PROOF_FIELDS_INVALID | fix_required | router proof has empty selected_model/rationale or empty fallback_chain | Populate required fields with valid values. |
| INV_ROUTER_PROOF_REVIEW_TASK_KIND_INVALID | fix_required | reviewer proof task_kind is not review | Set reviewer proof task_kind to review. |
| INV_PLAN_MISSING | fix_required | plan is absent | Provide a plan with steps. |
| INV_PLAN_STEPS_EMPTY | fix_required | plan.steps is empty | Add at least one plan step. |
| INV_PLAN_STEP_EMPTY | fix_required | plan.steps entry has empty step | Fill in the step text. |
| INV_CONTEXT_SCAN_MISSING | fix_required | context_scan is absent | Provide context_scan from the brief. |
| INV_CONTEXT_TASK_ID_MISMATCH | fix_required | context_scan.task_id differs from brief.task_id | Align task_id with the brief. |
| INV_CONTEXT_GOAL_EMPTY | fix_required | context_scan.goal is empty | Populate the goal from the brief. |
| INV_RISK_LEVEL_MISMATCH | warn | proposal risk_level differs from a router proof risk_level | Reconcile risk levels or document the mismatch. |
