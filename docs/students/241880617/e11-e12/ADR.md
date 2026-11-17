# ADR：集成接口决策

本文件记录 A05（A 轨）E11–E12 中两处影响跨阶段/跨组件接口的决策。编号规则 `ADR-e11e12-A05-<序号>`。

---

## ADR-e11e12-A05-01：阶段间报告以「封装 + 哈希引用」消费

| 项 | 内容 |
|---|---|
| 编号 | ADR-e11e12-A05-01 |
| 日期 | 2026-11-17 |
| 作者 | 241880617 饶嘉俊（A05，A 轨） |
| 状态 | 已采纳 |

**问题**

E12 的 `repair`（MDFixer）输入不再是固定文件 `fixed-md.json`，而是上游 `incremental-check`（EChecker）本轮真实产出的报告。多阶段串联后，报告可能来自别的 `job`、别的 `commit`、别的 `kind`，甚至内容被改过。如果下游只按路径 `json.load()` 直接吃，会出现三类事故：把上一次目标提交的报告用于这次、把 `full-check` 当 `incremental-check` 用、文件被截断/篡改后静默算出错误补丁。需要一个“消费前必校验”的约定。

**候选方案**

| 方案 | 做法 | 问题 |
|---|---|---|
| A. 裸文件传递 | 上游写路径，下游 `json.load` | 无任何校验，三种事故都会静默通过 |
| B. 只校验 `commit` | 比对报告 `commit` 与请求 `target` | 能挡“旧报告”，挡不住错阶段类型与被篡改内容 |
| C. 封装 + 三元校验 + 内容哈希 | 校验 `schema_version`/`kind`/`status`/`commit`，并按 `artifacts[].sha256` 复核文件字节 | 多一次读文件与哈希，成本可忽略 |
| D. 由 MDFixer 重新扫描项目 | 不消费上游报告 | 失去“报告驱动修复”的意义，等于绕过 EChecker |

**采用方案与原因**

采用 **C**。四类校验各自对应一类真实故障，且都能在“动手修”之前失败，避免产生错误补丁：

1. `schema_version` 必须是 `e11e12-1` → 挡版本漂移（`SCHEMA_MISMATCH`）。
2. `kind` 必须与下游期望的 `incremental-check` 一致 → 挡错阶段报告（`ARTIFACT_TYPE_MISMATCH`）。
3. `status` 必须是 `SUCCEEDED` → 挡拿失败报告继续修（`UPSTREAM_FAILED`）。
4. `commit` 必须等于本次修复目标 → 挡旧报告（`STALE_REPORT`）；再叠一层 `load_artifact` 按清单 `sha256` 复核字节 → 挡篡改或截断（`ARTIFACT_HASH_MISMATCH`）。

选择“封装 + 引用”而不是“把数据塞进同一个文件”的原因：阶段产物要能单独下载、单独归档、单独比对，`artifact://job/相对路径` 这个引用形式让 API 的 `/v1/jobs/{job_id}/files/{相对路径}` 与本地 `work/` 目录一一对应，出问题时能直接定位到是哪个产物。

**输入输出字段**

报告封装（所有阶段一致，消费者只依赖这些字段）：

| 字段 | 含义 | 消费者如何使用 |
|---|---|---|
| `schema_version` | `e11e12-1` | 严格相等，否则 `SCHEMA_MISMATCH` |
| `job_id` / `trace_id` | 全流程唯一标识，五阶段共用 | 日志关联、证据索引 |
| `kind` | `full-check` / `incremental-check` / `repair` / `recheck` … | 必须与期望类型一致 |
| `commit` | 本报告所描述的目标提交 | 必须等于本次修复目标 |
| `status` | `SUCCEEDED` / `FAILED` … | 非成功即 `UPSTREAM_FAILED` |
| `data` | 报告正文（`findings`、`actual`、`declared`、`key` 等） | 下游真正读取的部分 |
| `artifacts[]` | `{uri, sha256, bytes}` | `uri` 解析到文件，`sha256` 校验字节 |

正文（`incremental-report.json`，`schema_version=e8e10-1`）沿用 E8–E10 的图格式：`profile`、`commit`、`key{directives,recipes,flags,compiler}`、`actual`、`declared`、`findings`、`added`、`resolved`、`refreshed`、`reused`。下游只消费 `findings`（要修什么）与 `commit`（对谁修），`refreshed/reused` 用于解释增量边界，不参与修复决策。

**兼容性与测试**

- 向后兼容：E11 的固定输入 `fixed-md.json` 仍可被 MDFixer 消费，本决策只新增“消费前校验”，不改变正文字段；旧调用方（`e11-b.json`）无需修改。
- 真实项目适配：报告 `commit` 与 `target` 不同属正常（基线与目标本就不同提交），因此校验只针对**修复目标**那一段，基线报告另行记录其自身 commit。
- 测试：`labs/e11e12/test_student_241880617.py::Contract241880617::test_manifest_hash_guards_repair_consumption` 篡改产物字节后断言抛 `ARTIFACT_HASH_MISMATCH`；四个封装错误码另有实测（`改 commit → STALE_REPORT`、`改 schema → SCHEMA_MISMATCH`、`改 kind → ARTIFACT_TYPE_MISMATCH`、`改 status → UPSTREAM_FAILED`），并留有 `work/e11-stale-03`（`STALE_REPORT`）作为端到端反例。

---

## ADR-e11e12-A05-02：候选 Dockerfile 的 `FROM` 校验按「是否已 pin 摘要」分两种口径

| 项 | 内容 |
|---|---|
| 编号 | ADR-e11e12-A05-02 |
| 日期 | 2026-11-17 |
| 作者 | 241880617 饶嘉俊（A05，A 轨） |
| 状态 | 已采纳 |

**问题**

`prepare_candidate` 要在把候选 Dockerfile 交给 DRAFT 之前，保证候选**没有偷偷换基础镜像**。原始实现是先把候选的第一行 `FROM` 按 `@` 切开取 tag，再与原始行比较。这个比较只在原始行是 `FROM image:tag` 时成立；本组真实项目的 `Dockerfile.broken` 第一行是 `FROM python:3.13-slim@sha256:70729b…`，切完变成 `python:3.13-slim`，与原始整行必然不等，于是同一个 FROM 被判成“改了 tag”，真实项目接入直接硬阻塞。

**候选方案**

| 方案 | 做法 | 评价 |
|---|---|---|
| A. 放宽为只比较镜像名 | 忽略 tag 与摘要 | 太松，允许换任意版本 |
| B. 一律要求含摘要且摘要不变 | 缺摘要直接拒 | 会误伤未 pin 的官方样例与固定样例 |
| C. 按原始行是否含 `@` 分两种口径 | 含 `@` → 整行比较；不含 → 按 tag 比较 | 覆盖两类输入，且 pinned 时更严 |
| D. 允许候选从任意镜像构建 | 完全不校验 | 破坏“只追加构建步骤”的语义 |

**采用方案与原因**

采用 **C**。判定逻辑改为：

```python
expected_from = proposed[0] if "@" in original[0] else proposed[0].split("@", 1)[0]
if original[0] != expected_from:
    raise Failure("Candidate changed the original base image tag")
```

原因：原始行已 pin 摘要时，“不许换基础镜像”的精确含义就是**摘要逐字不变**，用整行比较恰好表达这一点，比旧逻辑更严格；原始行未 pin 时，tag 相等即视为同一镜像，保持原有宽松度，不破坏固定样例与官方 candidate 的既有行为。

**输入输出字段**

| 项 | 说明 |
|---|---|
| 输入 `original` | 项目自带 `Dockerfile.broken` 的指令行列表（`original[0]` 为 `FROM`） |
| 输入 `proposed` | 候选 Dockerfile 的指令行列表 |
| 校验 1 | 上述 `FROM` 口径（本 ADR 主题） |
| 校验 2 | 单阶段构建（不允许出现第二个 `FROM`） |
| 校验 3 | 原指令顺序不变，候选是原指令的**超集**且保持相对次序 |
| 校验 4 | 新增行必须以 `RUN ` 开头（只允许追加执行步骤） |
| 输出 | 通过则返回候选行列表；不通过抛 `Failure`，DRAFT 不启动 |

**兼容性与测试**

- 固定样例（`Dockerfile.broken` 未 pin）走 tag 比较分支，行为与修改前一致；真实项目（pinned）走整行比较分支，`CANDIDATE_PRECHECK=PASS`、`baseline_lines=5`。
- 三个新用例锁定边界：`Candidate241880617::test_pinned_accepts_new_run_line`（pinned + 追加 `RUN` → 通过）、`::test_pinned_rejects_digest_change`（pinned + 改摘要 → 拒绝）、`::test_unpinned_still_compares_tag`（未 pin + 改 tag → 拒绝）。
- 全量测试 `Ran 19 tests OK`；真实项目五阶段在此修改后跑通（`job-87743e5eb8134a23ba3f9f487b5814f3`）。
- 风险与边界：本决策不校验 `RUN` 行的内容（例如允许 `RUN rm -rf /`），因为候选来自学生的修复模型，安全边界由容器与只挂载工作副本保证；若后续要收紧，应在校验 4 上增加白名单而非回退到方案 A/B。
