#!/usr/bin/env python3
"""单变量故障/恢复对照的只读校验。

对照关系：
  fault-03   : data/e14-fault-tuna.json  (tuna candidate, build_timeout=0.01)
  sample-04  : data/e14-sample-tuna.json (tuna candidate, build_timeout=1800)
两份请求除 build_timeout 外逐字段相同，故构成 candidate 不变、仅 timeout 变化的单变量对照。
"""
import hashlib
import json
from pathlib import Path

STAGES = ["draft", "full-check", "incremental-check", "repair", "recheck"]
FAULT = Path("work/e14-compose-fault-03")
RECOVER = Path("work/e14-compose-sample-04")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


out = {}

# --- 1. 两份请求的字段差异 ---
fault_req = json.loads((FAULT / "request.json").read_text(encoding="utf-8"))
rec_req = json.loads((RECOVER / "request.json").read_text(encoding="utf-8"))
diff = {k: [fault_req.get(k), rec_req.get(k)] for k in set(fault_req) | set(rec_req)
        if fault_req.get(k) != rec_req.get(k)}
out["request_diff"] = diff
out["only_timeout_differs"] = list(diff.keys()) == ["build_timeout"]

# --- 2. 故障侧语义 ---
fr = json.loads((FAULT / "result.json").read_text(encoding="utf-8"))
out["fault"] = {
    "status": fr["status"],
    "job_id": fr["job_id"],
    "trace_id": fr["trace_id"],
    "artifact_count": len(fr.get("artifacts") or []),
    "stage_files_absent": [s for s in STAGES if not (FAULT / (s + ".json")).is_file()],
    "error": (fr.get("error") or "")[:160],
    "timed_out": "DRAFT_TIMED_OUT" in (fr.get("error") or ""),
}

# --- 3. 恢复侧五阶段 ---
rr = json.loads((RECOVER / "result.json").read_text(encoding="utf-8"))
stage_docs = {}
for s in STAGES:
    p = RECOVER / (s + ".json")
    stage_docs[s] = json.loads(p.read_text(encoding="utf-8"))
out["recover"] = {
    "status": rr["status"],
    "job_id": rr["job_id"],
    "trace_id": rr["trace_id"],
    "stage_status": {s: stage_docs[s]["status"] for s in STAGES},
    "all_stages_succeeded": all(stage_docs[s]["status"] == "SUCCEEDED" for s in STAGES),
    "stages_share_job": all(stage_docs[s]["job_id"] == rr["job_id"] for s in STAGES),
    "stages_share_trace": all(stage_docs[s]["trace_id"] == rr["trace_id"] for s in STAGES),
    "base_commit": rr["base_commit"],
    "target_commit": rr["target_commit"],
}

# --- 4. 哈希链 ---
inc = stage_docs["incremental-check"]["data"]
rep = stage_docs["repair"]["data"]
inc_report = RECOVER / "incremental" / "incremental-check.json"
patch = RECOVER / "repair-work" / "candidate.patch"
out["hash_chain"] = {
    "incremental_report_sha_matches": inc_report.is_file() and sha(inc_report) == inc["sha256"],
    "incremental_report_sha256": inc.get("sha256"),
    "patch_sha_matches": patch.is_file() and sha(patch) == rep.get("sha256"),
    "patch_sha256": rep.get("sha256"),
    "validation_accepted": rep.get("validation", {}).get("accepted"),
    "validation_checks": rep.get("validation", {}).get("checks"),
    "repair_has_input_report_field": "input_report" in rep,
}

# --- 5. 复检目标与剩余缺失 ---
rc = stage_docs["recheck"]
out["recheck"] = {
    "commit_is_target": rc.get("commit") == rr["target_commit"],
    "remaining_missing": rc.get("data", {}).get("remaining_missing"),
    "missing_count": len(rc.get("data", {}).get("remaining_missing") or []),
    "has_missing_finding": any(f.get("type") == "MISSING" for f in (rc.get("data", {}).get("findings") or [])),
}

# --- 6. 产物逐项复算 ---
arts = rr.get("artifacts") or []
bad = []
for a in arts:
    # compose 模式的 uri 是相对输出目录的路径；E12/E13 模式的 uri 带 artifact://job-*/ 前缀。
    rel = a["uri"]
    if rel.startswith("artifact://"):
        rel = rel.split("/", 3)[-1]
    p = RECOVER / rel
    if not p.is_file():
        bad.append({"uri": a["uri"], "reason": "missing file"})
        continue
    if sha(p) != a["sha256"] or p.stat().st_size != a["bytes"]:
        bad.append({"uri": a["uri"], "reason": "hash/size mismatch"})
out["artifacts"] = {"checked": len(arts), "mismatch": len(bad), "details": bad[:5]}

Path("work/e14-single-var-summary.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

print("== 请求差异 ==", out["request_diff"], "| 仅 timeout 不同:", out["only_timeout_differs"])
print("== 故障侧 ==", out["fault"]["status"], out["fault"]["job_id"], "timed_out:", out["fault"]["timed_out"],
      "缺阶段文件:", out["fault"]["stage_files_absent"])
print("== 恢复侧 ==", out["recover"]["status"], out["recover"]["job_id"],
      "| 全阶段成功:", out["recover"]["all_stages_succeeded"],
      "| 同 job:", out["recover"]["stages_share_job"], "| 同 trace:", out["recover"]["stages_share_trace"])
print("   阶段:", out["recover"]["stage_status"])
print("== 哈希链 ==", json.dumps(out["hash_chain"], ensure_ascii=False))
print("== 复检 ==", json.dumps(out["recheck"], ensure_ascii=False))
print("== 产物 ==", out["artifacts"]["checked"], "项, 不符", out["artifacts"]["mismatch"])
