"""E14 正式四容器运行只读校验（compose 链路字段版）。

判据：
1. 三次正向运行 result.json 为 SUCCEEDED，五阶段齐全且共享同一 job_id/trace_id；
2. draft/full-check/incremental-check/repair/recheck 各自 status 均 SUCCEEDED；
3. incremental-check.data.sha256 == 该阶段 report 文件的实算 sha256（报告来源可追溯）；
4. repair.data.sha256 == 补丁文件实算 sha256，validation.accepted 且 checks 全 true；
5. recheck.commit == result 的 target_commit，remaining_missing 为空；
6. result.json 中每个登记产物逐项复算 sha256 与 bytes。
"""
import hashlib
import json
from pathlib import Path

STAGES = ("draft", "full-check", "incremental-check", "repair", "recheck")
SUCCESS_DIRS = {
    "sample-tuna": "work/e14-compose-sample-02",
    "real-a05": "work/e14-compose-real-a05-01",
    "real-pair": "work/e14-compose-real-pair-01",
    "sample-recover": "work/e14-compose-sample-03",
}
FAULT_DIR = "work/e14-compose-fault-02"


def local(path_text: str) -> Path:
    """把容器内 /course/... 路径映射回宿主仓库相对路径。"""
    p = Path(path_text)
    parts = p.parts
    return Path(*parts[2:]) if len(parts) > 2 and parts[1] == "course" else p


def check_success(name: str, d: Path) -> dict:
    r = json.loads((d / "result.json").read_text(encoding="utf-8"))
    row = {
        "case": name,
        "dir": d.as_posix(),
        "status": r["status"],
        "job": r["job_id"],
        "trace": r["trace_id"],
        "base": r["base_commit"],
        "target": r["target_commit"],
    }
    assert r["status"] == "SUCCEEDED", (name, r["status"])
    assert [s["name"] for s in r["stages"]] == list(STAGES), (name, r["stages"])
    stage_status = {}
    for stage in STAGES:
        e = json.loads((d / (stage + ".json")).read_text(encoding="utf-8"))
        assert e["status"] == "SUCCEEDED", (name, stage, e["status"])
        assert (e["job_id"], e["trace_id"]) == (r["job_id"], r["trace_id"]), (name, stage)
        stage_status[stage] = e["status"]
    row["stages"] = stage_status

    inc = json.loads((d / "incremental-check.json").read_text(encoding="utf-8"))
    report = local(inc["data"]["report"])
    row["report_sha_matches"] = hashlib.sha256(report.read_bytes()).hexdigest() == inc["data"]["sha256"]
    row["report"] = report.as_posix()

    rep = json.loads((d / "repair.json").read_text(encoding="utf-8"))
    patch = local(rep["data"]["patch"])
    row["patch_sha_matches"] = hashlib.sha256(patch.read_bytes()).hexdigest() == rep["data"]["sha256"]
    row["patch"] = patch.as_posix()
    row["patch_checks"] = rep["data"]["validation"]["checks"]
    row["patch_accepted"] = rep["data"]["validation"]["accepted"]

    rc = json.loads((d / "recheck.json").read_text(encoding="utf-8"))
    row["recheck_commit_is_target"] = rc["commit"] == r["target_commit"]
    row["recheck_remaining_missing"] = rc["data"]["remaining_missing"]
    row["recheck_no_missing"] = not any(
        f["type"] == "MISSING" for f in rc["data"]["result"]["result"]["findings"]
    )

    arts, bad = r["artifacts"], 0
    for a in arts:
        p = d / a["uri"]
        if not p.is_file():
            bad += 1
            continue
        if hashlib.sha256(p.read_bytes()).hexdigest() != a["sha256"] or p.stat().st_size != a["bytes"]:
            bad += 1
    row["artifacts"] = len(arts)
    row["artifact_mismatch"] = bad
    return row


def check_fault(d: Path) -> dict:
    r = json.loads((d / "result.json").read_text(encoding="utf-8"))
    return {
        "dir": d.as_posix(),
        "status": r["status"],
        "job": r["job_id"],
        "trace": r["trace_id"],
        "stages": [s["name"] for s in r.get("stages", [])],
        "error": r.get("error"),
    }


def main() -> None:
    out = {"success": [], "fault": check_fault(Path(FAULT_DIR))}
    for name, path in SUCCESS_DIRS.items():
        out["success"].append(check_success(name, Path(path)))

    log = Path("work/e14-compose-services.log").read_text(errors="replace")
    entries = []
    for line in log.splitlines():
        if "| {" not in line:
            continue
        try:
            rec = json.loads(line.split("| ", 1)[1])
        except json.JSONDecodeError:
            continue
        if isinstance(rec, dict) and "job_id" in rec:
            entries.append(rec)
    per_job = {}
    for row in out["success"] + [out["fault"]]:
        bucket = {}
        for rec in entries:
            if rec["job_id"] == row["job"]:
                key = "%s/%s" % (rec.get("role"), rec.get("status"))
                bucket[key] = bucket.get(key, 0) + 1
        per_job[row["job"]] = bucket
    out["roles_per_job"] = per_job
    out["services_log_lines"] = len(log.splitlines())
    out["services_log_json_entries"] = len(entries)
    Path("work/e14-formal-summary.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
