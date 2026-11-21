# E13 A617：C6 密钥扫描与 C8 API 幂等（A05）

学号 241880617，A 轨 A05。个人分支 `student/241880617/e13-e14`，集成基线 `cc1e1548`。

`work/` 被 `.gitignore` 忽略，本目录收录 C6/C8 判定所需的原始输出，供 T5 门禁汇总与他组复核。完整过程见 `docs/students/241880617/e13-e14/个人报告.md`。

镜像 `course-e11e12:241880617`（`7ecd346355c6`）。执行时段 2026-11-19 22:46 – 2026-11-20 00:05。

## C6 假密钥阻断与恢复

隔离目录 `c6/`，不触碰仓库工作区。

| 步骤 | 退出码 | 输出 |
|---|---|---|
| 植入假 Key（`api_key` 赋 `sk-demo` 前缀假串，完整值仅存于 `work/` 未入库）后扫描 | **1** | `FOUND probe.log:1 LLM/API Key sk-d***`<br>`FOUND probe.log:1 secret assignment sk-d***`<br>`text_files=1 hits=2 errors=0` |
| 覆写为 `probe completed; clean content` 后复扫 | **0** | `text_files=1 hits=0 errors=0` |

内容指纹（证明文件真的被替换，而非缓存命中）：

```
eaa23e89f5ce97902e127ab7e3131d08c5752d43b0c760a178a7dbfb83a445a0  probe.log   植入后
4149894cbf0da8022229bcd4b0587b0d3038606cecf175387568722155e778e7  probe.log   清理后
```

`hits=2` 是两条独立规则各命中一次（`LLM/API Key` 与 `secret assignment`），不是同一条报了两遍。`text_files=1` 说明扫描器确实读到了文本，排除「路径不存在直接返回 0」的假阴性。

## C6 四范围扫描

门禁 §4 要求覆盖工作区、历史、镜像、运行日志。两个扫描器互补，缺一不可：

| 范围 | 证据文件 | 退出码 | 输出 |
|---|---|---|---|
| 工作区 + Git 历史 | `c6/scan-workspace-history.txt` | **0** | `未发现问题（文件 181 个，含 Git 历史）` |
| 镜像层 | `c6/scan-image.txt` | **0** | `未发现问题（文件 181 个，含镜像）` |
| 运行日志（基线证据） | `c6/scan-runtime-baseline.txt` | **0** | `text_files=145 hits=0 errors=0` |
| 运行日志（C8 作业） | `c6/scan-runtime-c8.txt` | **0** | `text_files=367 hits=0 errors=0` |

互补性：`scripts/secret_scan.py` 的 `SKIP_DIRS` 含 `work`，扫不到 `work/` 下的运行日志；`labs/e13e14/scan_runtime_logs.py` 只扫传入路径，不处理 Git 历史与镜像层。四个退出码无一为 `2`（2 = 扫描不完整，等同未执行）。

运行日志范围未取整个 `work/`：该目录混有 E10–E12 历史证据与他人日志，命中无法归属本轮。故限定为「本轮基线证据目录」与「本轮 C8 作业目录 + `work/api-jobs`」。

## C6 发现：旧版扫描器误报

执行 C6 时对比发现，仓库原有 `scan_runtime_logs.py`（2851 字节）只过滤占位符，把解析器里取 `token` 指针的赋值（函数调用、取数组元素地址两种形态）判为密钥。对三个教师项目（jsmn / inih / tiny-AES-c，128 个文本文件）实测 **`hits=10`，全部来自 `H1-jsmn/*/jsmn.h`**，无一是密钥。

已建 Issue **#19**，修复为本分支第二个提交。本目录的扫描证据均产生于升级后的 3177 字节版本（教师包同款）。

## C8 API 幂等

| 情形 | 输入 | 期望 | 实测 |
|---|---|---|---|
| 1 | 同键 + 同输入，第 1 次 | 202 新建 | **202**，`job-c7dba69cc8ed4fbaac285432745ea28a`，`QUEUED` |
| 2 | 同键 + 同输入，第 2 次 | 202 同一 job_id | **202**，`job-c7dba6…a28a`，`RUNNING` |
| 3 | 同键 + 不同输入 | 409 冲突 | **409**，`{"error": "IDEMPOTENCY_CONFLICT"}` |
| 4 | 换键 + 同输入 | 202 不同 job_id | **202**，`job-8b364b7e8e6543f4890f7a76ffadf139`，`QUEUED` |

`C8_IDEMPOTENCY=PASS`。作业目录从 2 个增至 4 个（`c8/jobs-before.txt` / `c8/jobs-after.txt`），同键两次提交只产生 **1** 个新作业目录。

请求指向 B 组实际项目 `data/real-project`（base `0b62c79a` → target `745ecf26`），不是固定样例——手册 §2 规定契约测试里的同类用例只能作回归基线，不得填入对方项目结果栏。

判定成立的依据：

- 情形 2 返回 `RUNNING` 而非 `QUEUED`，说明取到的是内存中同一 `state` 对象的实时快照，而非新建的等价作业。
- 情形 3 与 4 的 `request_hash` 前缀相同，因为 `Store.submit()` 的 `digest = sha256(json.dumps(request, sort_keys=True))` **只覆盖输入不覆盖 key**：同键异输入 → digest 变、key 不变 → 409；换键同输入 → digest 相同、key 不同 → 新建。
- 两个作业终态均 `SUCCEEDED`，`trace_id` 互异（`trace-5e1f6f3f…` / `trace-e328b576…`），说明幂等复用的是 job 对象，不是同一次执行。
- 各 95 个产物的 `artifact://<job_id>/` 前缀与字节 SHA 逐一匹配，证明 API 路径未绕过 `pipeline.py`。

本次请求 `mode=e11-a`，只走 `full-check` / `incremental-check` 两阶段，不产生 `recheck.json`，不构成五阶段路径验证——C8 的判定对象是幂等语义，与阶段数无关。

## 校验

```bash
(cd reports/E13/A617 && sha256sum -c SHA256SUMS)
```

## 说明

`c8/key.txt`（幂等键原文）**未入库**，仅在个人报告记录键名格式。其余文件均为纯文本输出，可逐行复核。
