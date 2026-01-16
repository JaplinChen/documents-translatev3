#!/usr/bin/env python3
import re
import sys
import json
import subprocess
from pathlib import Path

def sh(cmd, check=True):
    p = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    stdout = p.stdout or ""
    stderr = p.stderr or ""
    out = (stdout + "\n" + stderr).strip()
    if check and p.returncode != 0:
        raise RuntimeError(out)
    return p.returncode, out

def load_yaml(path: str):
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def truncate(s: str, n: int) -> str:
    return s if len(s) <= n else s[-n:]

def detect_intent(task: str) -> str:
    t = task.lower()
    if any(k in t for k in ["migrate", "migration"]): return "migrate"
    if any(k in t for k in ["refactor", "restructure", "cleanup"]): return "refactor"
    if any(k in t for k in ["optimize", "performance", "deadlock", "race"]): return "optimize"
    if any(k in t for k in ["fix", "bug", "error", "exception"]): return "fix"
    return "implement"

def git_changed_files() -> list[str]:
    rc, out = sh(["git", "diff", "--name-only"], check=False)
    return [x.strip() for x in out.splitlines() if x.strip()]

def any_path_matches(prefixes: list[str], files: list[str]) -> bool:
    for f in files:
        for p in prefixes:
            if f.startswith(p):
                return True
    return False

def pick_zone(policy: dict, files: list[str]) -> dict:
    for z in policy["zones"]:
        if any_path_matches(z["match_paths"], files):
            return z
    # fallback heuristics
    if Path("pyproject.toml").exists() or Path("requirements.txt").exists():
        return next(z for z in policy["zones"] if z["name"] == "backend")
    if Path("package.json").exists() or Path("web/package.json").exists() or Path("frontend/package.json").exists():
        return next(z for z in policy["zones"] if z["name"] == "frontend")
    return policy["zones"][0]

def base_tier(policy: dict, zone: dict, intent: str, files: list[str]) -> int:
    d = policy["defaults"]
    if "force_tier" in zone:
        return int(zone["force_tier"])
    tier = int(zone.get("start_tier_by_intent", {}).get(intent, 1))
    if len(files) >= d.get("changed_files_escalate_to_tier3", 9999):
        return 3
    if len(files) >= d.get("changed_files_escalate_to_tier2", 9999):
        tier = max(tier, 2)
    return min(3, max(1, tier))

def compile_error_rules(error_map: dict):
    compiled = []
    for r in error_map["rules"]:
        pats = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in r.get("patterns", [])]
        compiled.append((r, pats))
    return compiled

def classify_failure(error_rules, logs: str):
    for rule, patterns in error_rules:
        for p in patterns:
            if p.search(logs):
                d = {"action": rule["action"], "matched_rule": rule["name"]}
                if rule["action"] == "escalate_to":
                    d["tier"] = int(rule["tier"])
                if rule["action"] == "escalate_by":
                    d["by"] = int(rule.get("by", 1))
                return d
    return {"action": "none", "matched_rule": None}

def is_windows() -> bool:
    return sys.platform.startswith("win")

def verify_command(zone: dict) -> list[str]:
    v = zone["verify"]
    cmd = v["windows"] if is_windows() else v["unix"]
    # Use shell-like splitting; safest is explicit list for pwsh/bash patterns we control
    return cmd.split()

def run_verify_zone(zone: dict):
    cmd = verify_command(zone)
    rc, out = sh(cmd, check=False)
    verify_str = " ".join(cmd)
    if "verify-frontend" in verify_str: stage = "frontend"
    elif "verify-backend" in verify_str: stage = "backend"
    else: stage = "all"
    return rc == 0, stage, out

def run_codex(model: str, effort: str, approval: str, task: str, context: str,
             zone_name: str, tier: int, attempt: int):
    import shutil

    prompt = task
    if context:
        prompt += "\n\n---\nVerification/Context:\n" + context

    if approval == "chat":
        ask = "on-request"
        sandbox = "read-only"
    else:
        ask = "on-failure"
        sandbox = "workspace-write"

    Path(".codex").mkdir(exist_ok=True)
    Path(".codex/last_prompt.txt").write_text(prompt, encoding="utf-8")

    codex_path = shutil.which("codex")
    npx_path = shutil.which("npx")

    if codex_path:
        cmd = [
            codex_path,
            "--model", model,
            "--ask-for-approval", ask,
            "--sandbox", sandbox,
            "-c", f"reasoning_effort={effort}",
            prompt
        ]
    elif npx_path:
        cmd = [
            npx_path, "-y", "@openai/codex",
            "--model", model,
            "--ask-for-approval", ask,
            "--sandbox", sandbox,
            "-c", f"reasoning_effort={effort}",
            prompt
        ]
    else:
        raise FileNotFoundError(
            "找不到 'codex' 或 'npx'。請先安裝 Node.js（含 npm/npx），或安裝 Codex CLI：\n"
            "  npm i -g @openai/codex\n"
            "安裝後請重開 VS Code 讓 PATH 生效。"
        )

    p = subprocess.run(cmd, text=True)
    return p.returncode == 0

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 codex_router.py '<task>'", file=sys.stderr)
        sys.exit(2)

    task = sys.argv[1]
    policy = load_yaml("ai-policy.yaml")
    error_map = load_yaml("error-map.yaml")
    rules = compile_error_rules(error_map)

    files = git_changed_files()
    intent = detect_intent(task)
    zone = pick_zone(policy, files)

    defaults = policy["defaults"]
    tier = base_tier(policy, zone, intent, files)

    def model_for(t): return defaults["models"][f"tier{t}"]
    def effort_for(t): return defaults["effort"][f"tier{t}"]
    def approval_for(t):
        if "approval_mode_override" in zone:
            return zone["approval_mode_override"]
        return defaults["approval_mode"][f"tier{t}"]

    max_attempts = int(defaults.get("max_attempts", 5))
    log_max = int(defaults.get("log_max_chars", 12000))

    context = ""
    last_logs = ""
    last_stage = "unknown"

    for attempt in range(1, max_attempts + 1):
        ok_codex = run_codex(
            model=model_for(tier),
            effort=effort_for(tier),
            approval=approval_for(tier),
            task=task,
            context=context,
            zone_name=zone["name"],
            tier=tier,
            attempt=attempt
        )
        # Even if Codex returns non-zero (e.g., user aborted approvals), treat as failure requiring human
        if not ok_codex:
            Path(".codex").mkdir(exist_ok=True)
            Path(".codex/failure_reason.txt").write_text("Codex CLI returned non-zero. Possibly approval aborted.", encoding="utf-8")
            print("NEEDS_HUMAN: Codex run did not complete. See .codex/failure_reason.txt")
            sys.exit(1)

        ok, stage, logs = run_verify_zone(zone)
        last_logs, last_stage = logs, stage

        if ok:
            print(f"OK zone={zone['name']} tier={tier} intent={intent}")
            return

        logs_trunc = truncate(logs, log_max)
        decision = classify_failure(rules, logs_trunc)

        context = (
            "Verification failed.\n"
            f"Zone: {zone['name']}\n"
            f"Stage: {stage}\n"
            f"Intent: {intent}\n"
            f"Tier: {tier}\n"
            f"MatchedRule: {decision.get('matched_rule')}\n"
            "Logs (truncated):\n"
            + logs_trunc
        )

        if decision["action"] == "retry_same_tier":
            continue
        elif decision["action"] == "escalate_to":
            tier = max(tier, int(decision["tier"]))
        elif decision["action"] == "escalate_by":
            tier = min(3, tier + int(decision.get("by", 1)))
        else:
            tier = min(3, tier + 1)

    Path(".codex").mkdir(exist_ok=True)
    Path(".codex/failure_stage.txt").write_text(last_stage, encoding="utf-8")
    Path(".codex/failure_logs.txt").write_text(truncate(last_logs, log_max), encoding="utf-8")
    print("NEEDS_HUMAN: verification still failing. See .codex/failure_stage.txt and .codex/failure_logs.txt")
    sys.exit(1)

if __name__ == "__main__":
    main()
