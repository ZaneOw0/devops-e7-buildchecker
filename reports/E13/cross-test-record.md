# A05 E13 签收与 E14 交接

**最终门禁判定：通过（A05 组级 T5）。** 判定人：241880106。判定日期：2026-11-24。判定提交：`1f6ef6b5640f895bf1ff9524bdd9244d8db7fadd`（集成分支合并 #25 的提交）。

106 按现有证据签收 C1–C8。A 侧检测、交接、密钥扫描和幂等性已有独立复核，已知阻断缺陷 #15、#17、#19 均已关闭。第 2 项中的三个教师发放场景已有 A 组运行摘要。C1/C2/C3 的 B2 当次执行及 C5 在 A05 上的回滚继续登记为【无当次回执】，按既定签收口径列作证据缺项。B 仓证据取自 `cbfb160a2a40bb934bc0e8caf3b7367a6e961c5f`。

## 输入和独立复核

| 项目 | 提供方 | base → target | 来源及适用范围 |
| --- | --- | --- | --- |
| A05 quota-scale | A05 / 106 | `6b9deff53f8fcf6183204850ac6a9dddb22f1189` → `90646db8b8ad932da1a959d152942f987aaffff2` | [A05 交接包](A-project/)，双源文件、显式 Make 依赖，预期缺少 clamp.h。 |
| 配对 B 项目 | B 提供，353 执行 | `0b62c79a6adb4cd913a814068074575afdbbd18b` → `745ecf2621c8221b97bf0a5435ace50150ef57d4` | [A353 清单](A353/MANIFEST.json)，显式 Make 依赖，预期缺少 output_format.h。 |

353 记录的执行镜像为 `sha256:a933915e054124278b8d2dcebd6e29289bf5e64141592efa0fd7fc7e8cdeff47`。617 记录的镜像短 ID 为 `7ecd346355c6`。106 在自己的服务器目录复核两份个人交付和 A05 项目包，[校验输出](A106/verification.txt)记录全部 33 项哈希、12 项交接测试及 19 项契约测试。

PR #23 已将 C1 两个内层产物纳入 A353 目录。106 在 `3ce7943` 上核对 A353 清单 15 项，仅用仓库文件重建 `fixed-md-input.json`，SHA 为 `75a29263c245588c517073d0aa231bba51b5ed5287f1f1c9c5a8ee27e99c523d`，与入库文件逐字节相同。上段 33 项对应前一版清单。

## 用例签收

| 用例 | 签收的输入和结果 | 当次记录 |
| --- | --- | --- |
| C1 正常链路 | 353 的 `d543f4cc…` 报告和可复现交接件已验收。B1 归档的 `66e3bfb2…` 报告修复成功、复检缺失数为 0。两份报告及其内层产物 SHA 均不同。[B1 结果][c1] | A 侧通过。B2 消费 `d543f4cc…` 并修复、复检【无当次回执】。 |
| C2 拒旧与错误目标 | A 侧在实际交接副本上拒绝旧报告和错误目标。B1 使用 `84c2cd83…` 得到 `STALE_REPORT`，错误目标得到 `WRONG_TARGET`，均在修复前拒绝。[旧报告][c2s]、[错误目标][c2w] | A 侧通过。B2 消费 353 的旧报告 `f5bccbf6…`【无当次回执】。 |
| C3 哈希篡改 | 106 在 A 交接副本改动一字节后触发哈希校验失败。B2 归档原件 `66e3bfb2…` 与篡改件 `3bd0b8f8…` 的重算哈希与记录一致，返回 `ARTIFACT_HASH_MISMATCH`，未启动修复。[B2 判定][c3] | A 侧复验通过。B2 对本轮报告 `d543f4cc…` 的篡改检验【无当次回执】。 |
| C4 超时 | B3 在 A05 上以 0.25 秒超时取得外层 `FAILED`、内层 `TIMED_OUT`，检查时无残留构建客户端。B4 记录 A 组已签收。[B3 交接][b3]、[签收范围][b4] | 已签收。 |
| C5 错误补丁回滚 | B2 在 B 项目 `745ecf26…` 上拒绝补丁并回滚。HEAD、工作区状态和 11 个文件的哈希在回滚前后一致。[回滚原件][c5] | B 项目已签收。分工所列 A05 项目的回滚【无当次回执】。 |
| C6 假密钥 | 617 注入后扫描退出 1，清理后退出 0。工作区、历史、镜像、运行日志均有证据，353 已独立复核。[A617 清单](A617/SHA256SUMS)、[复核记录][pr20] | 已签收。 |
| C7 失败隔离 | A 侧坏 base 失败，后续正常任务成功，95 项产物，job/trace 独立。B3 也在 A05 上完成失败及恢复，B4 记录 A 已签收。[A353 清单](A353/MANIFEST.json)、[B3 交接][b3]、[签收范围][b4] | 两侧均已签收。 |
| C8 幂等 | 617 在 B 项目上得到 202/202/409/202，同键同输入复用 job，换键新建 job。353 已复核。[响应](A617/c8/c8-result.txt)、[复核记录][pr20] | 已签收。 |
| H1–H3 教师发放的未知场景 | 617 独立执行 jsmn、inih、tiny-AES-c，三项均五阶段成功，每项 177 个登记产物。617 报告 531 项 SHA 与大小复算全部匹配。H2 复检无 MISSING，保留一条 REDUNDANT。[A 组运行摘要](../../docs/students/241880617/e13-e14/三个未知项目运行结果.md) | 三项结果摘要已签收，执行提交 `2e4b9a5`，摘要提交 `9de1db6`。 |

## 交接给 E14

- 106 已验收 #15、#17、#19 的修复。`3ce7943` 上四个 push 工作流通过。#16、#20 缺少合并前独立审查。#20 有 353 的合并后独立复核。该组级签收记录待非作者审查。[集成提交](https://github.com/ZaneOw0/devops-e7-buildchecker/commit/3ce79430e07f3b462b7791c39f8c11dd3ae90659)
- 集成分支经非作者批准并合入 main 后，106 交付该 PR 的完整合并 SHA。617 按该 SHA 重建镜像并启动正式四服务验收，353 独立复核 job、trace 和产物哈希。合并前的运行仅作 `e14-pre-*` 前置记录。

[c1]: https://github.com/Rowan-hhh/devops-e4-draft/blob/cbfb160a2a40bb934bc0e8caf3b7367a6e961c5f/reports/E13/B1/server-run/C1-C2/C1-result.json
[c2s]: https://github.com/Rowan-hhh/devops-e4-draft/blob/cbfb160a2a40bb934bc0e8caf3b7367a6e961c5f/reports/E13/B1/server-run/C1-C2/C2-stale-result.json
[c2w]: https://github.com/Rowan-hhh/devops-e4-draft/blob/cbfb160a2a40bb934bc0e8caf3b7367a6e961c5f/reports/E13/B1/server-run/C1-C2/C2-wrong-target-result.json
[c3]: https://github.com/Rowan-hhh/devops-e4-draft/blob/cbfb160a2a40bb934bc0e8caf3b7367a6e961c5f/reports/E13/B2/C3-artifact-hash-tamper/decision/result.json
[c5]: https://github.com/Rowan-hhh/devops-e4-draft/blob/cbfb160a2a40bb934bc0e8caf3b7367a6e961c5f/reports/E13/B2/C5-invalid-patch/result.json
[b3]: https://github.com/Rowan-hhh/devops-e4-draft/blob/cbfb160a2a40bb934bc0e8caf3b7367a6e961c5f/reports/E13/B3/handoff.json
[b4]: https://github.com/Rowan-hhh/devops-e4-draft/blob/cbfb160a2a40bb934bc0e8caf3b7367a6e961c5f/reports/E13/B4/handoff.json
[pr20]: https://github.com/ZaneOw0/devops-e7-buildchecker/pull/20
