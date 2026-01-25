# Claude Code Development Guide - Hetzner AaaS Factory

Based on:
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- Factory SSOT (master__open_pr_contract_v1_3.md)

---

## ⚙️ Setup

### Global Settings
```bash
mkdir -p ~/.claude
cat > ~/.claude/settings.json << 'EOF'
{"cleanupPeriodDays": 99999}
EOF
```

---

## 🎯 Factory Development Principles

### 1. SSOT is Law
- Implementation MUST match SSOT
- Never weaken v1.2 safety guarantees
- Backward compatibility is mandatory

### 2. Human-in-the-Loop
- No autonomous apply
- No auto-merge
- All write operations require approval token

### 3. Fail-Safe First
- GitHub 401/403 → fallback URL (never abort)
- RepoLock/PRSchedule gates BEFORE write
- audit log failure → warn, don't block

### 4. Explicit Over Implicit
- All state transitions explicit
- All error codes defined
- All scope checks mandatory

---

## 📋 Development Workflow

### SSOT Changes (Highest Risk)
```
User: "Update actorId spec in SSOT"

Expected behavior:
1. Load skills: factory-ssot-knowledge, controlled-git-contract
2. Plan mode activated
3. Show diff of master__open_pr_contract_v1_3.md
4. Verify no weakening of v1.2 guarantees
5. Verify contractVersion handling
6. Request approval
```

### Implementation Changes
```
User: "Add actorId validation to cli.py"

Expected behavior:
1. Load skills: approval-token-spec
2. Check SSOT for validation rules
3. Plan implementation
4. Show test requirements
5. Request approval
```

---

## 🚨 Prohibited

- Breaking v1.2 compatibility
- Weakening actor binding (v1.3)
- Auto-apply without human approval
- Secrets in code/logs
- Files > 800 lines

---

## 📚 Reference

### SSOT Documents
- `master__open_pr_contract_v1_3.md`: PR creation contract
- `master__factory_master_v3.md`: Factory positioning

### Skills
- `factory-ssot-knowledge`: Factory overview
- `controlled-git-contract`: cli.py implementation
- `approval-token-spec`: Token structure/validation

---

## 🧪 Testing

### Unit Tests
- Mock GitHub API (requests)
- Test approval token signature
- Test canonical_proposal_hash

### Integration Tests
- Use test repos (not production)
- Test RepoLock acquire/release
- Test PRSchedule blocking

---

## 💡 Current Focus

- Phase: External repo safe PR creation
- Milestone: actorId spec clarification (COMPLETE)
- Next: delete DoD definition → test expansion
