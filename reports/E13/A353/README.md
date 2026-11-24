# E13 A353：C1/C2/C7 交接（A 服务测 B 项目）

学号 241880353。个人分支 `student/241880353/e13-e14`。给 B2/B3 使用。完整 `work/` 目录不入库；C1 的 tar 在服务器 `/root/devops-submissions/241880353/e13-c1-b-project.tar.gz`。

B 项目仍是 E12 B1 交接包：base `0b62c79a6adb4cd913a814068074575afdbbd18b`，target `745ecf2621c8221b97bf0a5435ace50150ef57d4`。

## C1 正常链路（E11-A）

- 请求：`requests/c1-e11-a.json`
- 输出：`work/e13-c1-b-01`，`SUCCEEDED`
- job `job-33ddc3e1eaea4414ae93291a97cb4ac8` / trace `trace-919a053e37b64c5ba4ab378bd64a5123`
- 发现：仅 `MISSING helper.o → output_format.h`
- 本目录 `incremental-check.json`、`result.json` 与 `fixed-md-input.json`（由 `labs/e13e14/handoff_a_to_b.py` 生成）
- 增量产物也入库：`incremental-report.json`、`target-full/findings.json`（与 `incremental-check.json` 里登记的 sha256 一致）
- tar sha256：`23c527063448c0b96730569c5c2cc32ed2dbf1ec4cac4e85acbefd88c41331d0`

B 组消费时请核对本目录 `incremental-check.json` 的 sha256，并用 `fixed-md-input.json` 的 `source_report` 对照 job/trace。完整 `work/` 仍以 tar 为准；只复核交接器时不必解 tar，可用下面的命令。

## C2 错误 target 与旧报告

- 请求：`requests/c2-wrong-target.json`（target 换成 A05 的 `90646db8…`，该提交不在 B 项目里）
- 输出：`work/e13-c2-wrong-target-01`，外层 `FAILED`，`COMMAND_FAILED`，`target-project-resolve.log` 为 `fatal: Needed a single revision`
- 旧报告：`stale-incremental-check.json`，把 C1 增量报告的 envelope/data commit 改成 base `0b62c79a…`，供 B 侧拒绝（`STALE_REPORT` / 目标不符）
- 原报告与 SHA：`incremental-check.json`，供 C3 哈希核对

## C7 失败隔离

1. `requests/c7-bad-base.json`：base 为 40 个 0。`work/e13-c7-fail-01` `FAILED`，构建前 `COMMAND_FAILED`。
2. 再用 C1 同一请求跑 `work/e13-c7-ok-01`：`SUCCEEDED`，95 个产物，发现与 C1 相同。

两次 job/trace 不同，目录不复用。结束后 Docker 只剩 106 的 `mystifying_williams`。`data/real-project` 仍在 target，工作区干净。

## 校验

```bash
(cd reports/E13/A353 && sha256sum -c SHA256SUMS)
python3 labs/e13e14/handoff_a_to_b.py --a-result reports/E13/A353/result.json --target-sha 745ecf2621c8221b97bf0a5435ace50150ef57d4 --out /tmp/e13-a353-handoff-recheck.json
# 期望 HANDOFF_READY sha256=75a29263c245588c517073d0aa231bba51b5ed5287f1f1c9c5a8ee27e99c523d
```
