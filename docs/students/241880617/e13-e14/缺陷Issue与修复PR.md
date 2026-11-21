# 缺陷 Issue 与修复 PR（241880617，E13）

> 对应 E13 出口门禁第 3 条「每个阻断缺陷有 Issue、修复 PR、回归结果」。
> 缺陷对象：`labs/e13e14/scan_runtime_logs.py` 旧版（2851 字节）。
> 本文所有密钥形态均已脱敏；完整假值只在 `work/` 下运行期生成，未入库。

## Issue

- **用例编号与发现方**：E13 / C6（密钥扫描四范围）。A 侧 241880617 在执行 C6 时发现，分拣记录为 Issue **#19**。
- **输入仓库及完整 SHA**：教师发放包 `e13-upstream-student.zip`，SHA-256 `d9818c5f34d6ff5b6016222dabd7f56daca09ceaa5f525be214e146e3d485435`。解压后为 `e13-upstream-student/{H1-jsmn,H2-inih,H3-tiny-AES-c}`，各含 `repo/`（课程适配副本）与 `upstream-original/`。本缺陷不依赖被测项目提交，复现输入是解压后的 128 个文本文件。
- **预期 / 实际**：
  - 预期：扫描运行日志与证据目录时只报真实密钥，`hits` 可直接用于判定。
  - 实际：对 128 个文本文件报 `hits=10`、退出码 1，10 条全部来自 `H1-jsmn/*/jsmn.h` 第 177、211、287、318、334 行（`repo/` 与 `upstream-original/` 各 5 条）。这些行是从函数调用或数组元素给 token 指针赋值，不是密钥。
- **失败阶段、错误码和原始日志路径**：`labs/e13e14/scan_runtime_logs.py`（2851 字节）的 `secret assignment` 规则；退出码 1。工作副本 `~/devops-students/241880617/buildchecker`，原始输出：
  - `work/e13-t4-repro/old-upstream.txt`（旧版，`hits=10` / exit 1）
  - `work/e13-t4-repro/new-upstream.txt`（新版，`hits=0` / exit 0）
  - `work/e13-t4-repro/old-probe.txt`、`new-probe.txt`、`clean-scan.txt`（探针三态）
  - `work/e13-t4-repro/probe/dirty.sha256`、`clean.sha256`（探针清理前后内容哈希）
- **严重度（阻断 / 非阻断）与理由**：**阻断**。E13 门禁第 4 条要求密钥扫描覆盖运行日志并给出可解释结论；证据目录只要含源码副本、编译日志或 strace 输出，旧版就产生成片误报，命中数失去判别力，「未发现问题」的结论不可信，门禁无法据以签字。
- **最小复现步骤**：
  1. `git show 95c3a6d:labs/e13e14/scan_runtime_logs.py > /tmp/scan_old.py`（2851 字节）
  2. `python3 -m zipfile -e e13-upstream-student.zip work/e13-t4-repro/upstream`
  3. `python3 /tmp/scan_old.py work/e13-t4-repro/upstream; echo $?` → `hits=10`，退出 1
  4. 换教师包 3177 字节版本重复第 3 步 → `hits=0`，退出 0
  5. 单文件探针（一行真实假 Key + 一行解析器赋值）旧版 `hits=3`、新版 `hits=2`
- **是否影响其他任务或原仓库**：不影响 `pipeline.py`、`service.py`、`compose.yaml`、`orchestrate.py`、`handoff_a_to_b.py`；不修改任何被测仓库；退出码语义不变（0 无命中 / 1 有命中 / 2 未扫到文本或扫描不全）。

## PR

- **关联 Issue**：`#19` — https://github.com/ZaneOw0/devops-e7-buildchecker/issues/19
- **修改文件与原因**：
  1. `labs/e13e14/scan_runtime_logs.py`，`+6 −2`：`secret assignment` 的排除条件从「仅占位符」扩为「占位符 或 `&` 前缀 或 含 `(` 或 含 `[`」，与教师包 3177 字节版本一致。C 赋值语句不再被判为硬编码密钥。
  2. `labs/e13e14/tests/test_student_241880617.py`（新增，4 项）：把该行为固化为回归，防止以后被改回去。
- **失败前证据 / 修复后同一测试证据**：

| 同一输入 | 旧版 2851B | 新版 3177B |
|---|---|---|
| 教师包 `e13-upstream-student/`（128 个文本文件） | `hits=10`，退出 1，10 条全是 `jsmn.h` 的 C 赋值 | `hits=0`，退出 0 |
| 探针：1 行真实假 Key + 1 行解析器赋值 | `hits=3`，退出 1 | `hits=2`，退出 1（仅假 Key 命中两条规则） |
| 探针清理为普通文本后（sha256 `4149894c…`） | `hits=0`，退出 0 | `hits=0`，退出 0 |

- **新增或修改的回归测试**：`labs/e13e14/tests/test_student_241880617.py`
  1. `test_parser_assignments_are_not_reported`：函数调用、`&` 取址、数组下标三种赋值 → 退出 0、`hits=0`
  2. `test_real_key_is_still_reported`：运行期拼出的假 Key → 退出 1、至少 1 条命中，且输出已脱敏（断言原文不出现在 stdout）
  3. `test_clean_copy_passes`：占位符写法 + 普通文本 → 退出 0
  4. `test_placeholder_assignment_is_still_excluded`：环境变量引用形态 → 退出 0

  测试夹具用模板拼接生成，源文件本身不含可被仓库密钥扫描命中的完整赋值，避免「用测试触发自己的门禁」。
  E13 交接测试由 6 项增至 **10 项全 ok**；E11–E12 契约测试 19 项不受影响。
- **原始仓库修复前后 SHA 核对**：修复只改扫描脚本与测试文件，被测项目（A05 `6b9deff`→`90646db8`、B 项目 `0b62c79a`→`745ecf26`、固定样例 `d77b4d86`→`03195569`）的 base/target 提交与工作区内容不变；E13 基线证据 `work/e13-baseline-241880617-01` 的 156 个产物哈希在修复前后一致。
- **CI 门禁链接与审查人**：PR 建立后由 241880106 按分工审查并合并。目标提交上 `E13-E14 integration gate`、`E11-E12 integration`、`E7 A quality gate`、`E8-E10 teaching validation` 五项必需检查须全绿；合并前链接填入本节。
- **剩余风险**：
  1. 排除规则按「值里出现 `(`、`[` 或以 `&` 开头」判断，理论上会漏掉形如 `key = abc(def)` 的真密钥；现实中密钥是定长随机串，不含括号，且 `LLM/API Key`、GitHub Token、私钥三条规则不受影响，故判为可接受。
  2. 该规则与教师包版本逐字节一致，若教师后续更新扫描器，需重新对齐并跑一遍本文的对照表。
  3. `--history` 走 `git log --all`，本地多分支残留会误报；判定须用 `git clone --single-branch --branch <分支>` 复验，CI 不受影响。
