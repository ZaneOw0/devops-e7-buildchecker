# E14 四容器正式验收证据（241880617 / A05）

## 修订记录（按 PR #27 审核意见）

241880106 于 2026-11-24T11:25:20Z 给出 `CHANGES_REQUESTED`，三条意见与处理如下：

| 审核意见 | 本次处理 |
| --- | --- |
| `fault/` 与 `recover/` 两份请求**同时改变** `candidate` 与 `build_timeout`，不能登记为单变量恢复 | 第五节拆为组 1 / 组 2。组 1 改登记为「超时后切换到已验收候选，新任务恢复成功」，并在 2.2 表标注「两处变化」；新增组 2（`fault-single/`、`recover-single/`）补出**仅 timeout 变化**的单变量证据 |
| README 末段的 `SHA256SUMS` 范围应写为**选摘归档** | 第八节改写：明确未收录的原始文件不在覆盖范围，`SHA256SUMS` 只能证明「归档内文件未被改动」 |
| `repair.json` 没有 `input_report.sha256` 字段 | 第三节新增「哈希链的可核对范围」，列出归档内可独立核对的四项，删除原先的超范围表述 |

另：第一节「M 与判定提交的差异」原为无凭证断言，现补实测 `git diff --stat 1f6ef6b 68c5454`（仅 `cross-test-record.md`，+7 −3）。

## 一、验收对象

| 项 | 值 |
| --- | --- |
| 候选提交 | **`68c5454914b48ee2482fb17cd101ff8b8ee854ce`**（PR #26 合并提交 M，2026-11-24T10:56:49Z，`main` 当前指向） |
| 判定提交 | `1f6ef6b`（集成分支上的 T5 门禁判定）。实测 `git diff --stat 1f6ef6b 68c5454` 只输出 `reports/E13/cross-test-record.md`（+7 −3），即 M 与判定提交的树差异仅该文件自身 |
| 镜像 | `course-e11e12:241880617`，ID **`sha256:9b19710406eb6e2d35454fb36889e3da8fd163ac82a9f035418bcd605c4cd134`** |
| 镜像构建 | 在 M 上执行 `docker build`（BASE_IMAGE / DOCKER_CLI_IMAGE 均按 digest 固定），全层命中缓存，`Created` 仍为 2026-11-10T18:54:41+08:00 —— 说明 M 的教学镜像定义与原构建逐字节一致 |
| 编排入口 | `labs/e13e14/orchestrate.py`（四角色经 HTTP 传递阶段数据） |
| Compose 项目 | `e14-241880617`，端口仅 `127.0.0.1:18081–18084` |
| 四角色健康 | `buildchecker` / `echecker` / `draft` / `mdfixer` 启动后均为 `healthy`（`docker compose ps`） |

## 二、运行清单

### 2.1 正向运行（五次）

| 目录 | 类型 | base → target | job_id | 五阶段 | 产物 | 补丁 sha256 |
| --- | --- | --- | --- | --- | --- | --- |
| `sample/` | 固定样例（镜像源适配候选） | `d77b4d86` → `03195569` | `job-3f0c37ff14874dd78d775ffd2f5a41a9` | 5/5 SUCCEEDED | 162 | `88074f66…bd0e5a` |
| `real-a05/` | 真实项目：A05 本组 | `6b9deff5` → `90646db8` | `job-59c9c4af21d0499ba9aaead8e41fcc20` | 5/5 SUCCEEDED | 181 | `0030f288…bef9db` |
| `real-pair/` | 真实项目：配对侧 | `0b62c79a` → `745ecf26` | `job-b281badaae9542ce94f76dbd6e72d57a` | 5/5 SUCCEEDED | 180 | `a7a3be54…b5142a` |
| `recover/` | 固定样例重试（`fault/` 之后） | `d77b4d86` → `03195569` | `job-25293e0821aa42b796222fd82c751161` | 5/5 SUCCEEDED | 162 | `88074f66…bd0e5a` |
| `recover-single/` | 固定样例重试（`fault-single/` 之后，原请求原样） | `d77b4d86` → `03195569` | `job-72190418df5c47b6a67eba846f79764e` | 5/5 SUCCEEDED | 162 | `88074f66…bd0e5a` |

### 2.2 故障注入与恢复：两组对照

| 目录 | 所属组 | candidate | build_timeout | job_id | 结果 |
| --- | --- | --- | --- | --- | --- |
| `fault/` | 组 1（**两处变化**） | `integration-sample/candidate.Dockerfile`（教师原候选） | 0.01 | `job-d223d409fae0451ab327ea7ebc758a5c` | FAILED，exit 1 |
| `recover/` | 组 1（**两处变化**） | `candidate-tuna.Dockerfile` | 1800 | `job-25293e0821aa42b796222fd82c751161` | SUCCEEDED |
| `fault-single/` | 组 2（**仅 timeout 变化**） | `candidate-tuna.Dockerfile` | 0.01 | `job-10410e9704674cb4b81f83325564147d` | FAILED，exit 1 |
| `recover-single/` | 组 2（**仅 timeout 变化**） | `candidate-tuna.Dockerfile` | 1800 | `job-72190418df5c47b6a67eba846f79764e` | SUCCEEDED |
| `baseline-failure/` | 网络失败留证 | `integration-sample/candidate.Dockerfile` | 600（默认） | `job-2e02e91c2bec4a569c70a2e7f4f8cfcb` | FAILED（draft 600 s 超时） |

两组对照的差别必须说清，详见第五节：**组 1 同时改变了 candidate 与 build_timeout 两个变量**，只能登记为「超时后切换到已验收候选，新任务恢复成功」；**组 2 只改变 build_timeout 一个变量**，才是手册要求的单变量故障恢复。

固定样例与真实项目分别记录，**未把样例结果写成真实项目结果**。

## 三、判据核对（`checks/e14-formal-summary.json` + `checks/e14-single-var-summary.json`）

四次正向运行（`sample`、`real-a05`、`real-pair`、`recover`）由 `checks/e14_verify.py` 核对，`recover-single` 由 `checks/e14_verify_single.py` 单独核对，两脚本判据一致，逐项满足：

1. `result.json` 为 `SUCCEEDED`，阶段顺序严格为 `draft → full-check → incremental-check → repair → recheck`；
2. 五个阶段文件各自 `status=SUCCEEDED`，且 `job_id`/`trace_id` 与 `result.json` 完全一致（同一任务贯穿四角色）；
3. `incremental-check.data.sha256` 与该阶段 report 文件（`incremental/incremental-check.json`）实算 sha256 一致 —— A→B 报告来源可追溯；
4. `repair.data.sha256` 与补丁文件实算一致，`validation.accepted=true`，`checks={patch_applies,build,test,header_change,no_missing}` 全为 `true`；
5. `recheck.commit` 等于目标提交，`remaining_missing=0`，`findings` 中无 `MISSING`；
6. `result.json` 登记的全部产物逐项复算 sha256 与字节数：**847 个产物，0 处不符**（162+181+180+162+162）。

**哈希链的可核对范围**（按 241880106 审核意见修订）：compose 模式的 `repair.json` 其 `data` 段**不含 `input_report` 字段**（实测该键不存在），因此「补丁的输入报告哈希」不能从归档内独立核对。归档内可独立核对的是以下四项：

| 核对项 | 字段/文件 | 结果 |
| --- | --- | --- |
| 增量报告哈希 | `incremental-check.data.sha256` vs `incremental/incremental-check.json` 实算 | 一致 |
| 同轮任务关联 | 五阶段 `job_id` / `trace_id` vs `result.json` | 全部一致 |
| 补丁哈希 | `repair.data.sha256` vs `repair-work/candidate.patch` 实算 | 一致 |
| 补丁验收结论 | `repair.data.validation.accepted` + `checks` 五项 | `true` / 五项全 `true` |

第 3 项与第 4 项合起来说明「该补丁就是被验收的那份补丁」；报告→补丁的输入关系由同轮 job/trace 保证，而非由 `repair.json` 内的显式哈希字段保证，此处不作超范围声明。

## 四、四角色确实处理了本轮任务（不只是 healthy）

两批容器生命周期各留一份完整日志：

- `services/e14-compose-services.log`：784 行，26 条结构化记录（第一次 `up`→`down`，含 `baseline-failure` 与组 1 故障）
- `services/e14-compose-services-02.log`：68 行，7 条结构化记录（第二次 `up`→`down`，含组 2 单变量故障与恢复）

按 job 统计（两批合并）：

| job | 日志 | buildchecker | echecker | draft | mdfixer | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| `job-3f0c37ff…` | services | 3 | 1 | 1 | 1 | SUCCEEDED |
| `job-59c9c4af…` | services | 3 | 1 | 1 | 1 | SUCCEEDED |
| `job-b281bada…` | services | 3 | 1 | 1 | 1 | SUCCEEDED |
| `job-25293e08…` | services | 3 | 1 | 1 | 1 | SUCCEEDED |
| `job-2e02e91c…`（网络失败） | services | — | — | 1（FAILED） | — | FAILED |
| `job-d223d409…`（组 1 故障） | services | — | — | 1（FAILED） | — | FAILED |
| `job-72190418…`（组 2 恢复） | services-02 | 3 | 1 | 1 | 1 | SUCCEEDED |
| `job-10410e97…`（组 2 故障） | services-02 | — | — | 1（FAILED） | — | FAILED |

每条记录含 `role`、`job_id`、`trace_id`、`status`、`elapsed_ms`。规律清晰：**成功任务四角色各留下记录，失败任务只有 draft 的 `FAILED` 记录、下游角色不产生记录**，与「失败不显示成功」一致。

日志扫描：`scan_runtime_logs.py` 对 **2 份服务日志 + 7 个运行目录**共 9 次分别执行，累计 **868 个文本文件，`hits=0 errors=0`**（9 份结果均在 `checks/*scan.log`）。第二批明细：`sample-04` 151 个、`fault-03` 37 个、`services-02.log` 1 个。

## 五、受控故障与恢复（两组对照）

故障注入分两组，**变量数量不同，结论强度也不同**，下面分开登记，不混用。

### 5.1 组 1：`fault/` → `recover/`（同时改变 candidate 与 build_timeout）

| 项 | `fault/` | `recover/` | 是否变化 |
| --- | --- | --- | --- |
| `candidate` | `/course/data/integration-sample/candidate.Dockerfile`（教师原候选） | `/course/data/candidate-tuna.Dockerfile` | **变化** |
| `build_timeout` | 0.01 | 1800 | **变化** |
| `repo` / `base` / `target` / `fixed_report` / `expected_output` | 同 | 同 | 不变 |

**因此本组不是单变量恢复**，只能登记为：**「超时后切换到已验收候选，新任务恢复成功」**。

事实部分仍然成立：`fault/` 得到 `DRAFT_TIMED_OUT: Docker client command exceeded 0.01s`，外层 `result.json` 为 `FAILED`、`stages=[]`、编排退出码 **1**；`recover/` 在新目录得到 `SUCCEEDED`，job/trace 与故障那次不同（`job-25293e08…` / `trace-c81aef73…`），是干净的新任务。该组证明的是「换用已验收候选后可以跑通」，**不能用于论证仅恢复时限即可恢复**。

### 5.2 组 2：`fault-single/` → `recover-single/`（仅改变 build_timeout，手册要求的单变量恢复）

请求构造：以 `data/e14-sample-tuna.json`（`sample/` 实际所用请求）为基准，只把 `build_timeout` 由 1800 改为 0.01，生成 `data/e14-fault-tuna.json`。校验脚本断言两份请求**逐字段相同，差异键集合恰为 `{build_timeout}`**（`checks/e14-single-var-summary.json` 的 `request_diff` 与 `only_timeout_differs=true`）。

| 项 | `sample/`（基准） | `fault-single/`（注入） | `recover-single/`（恢复） |
| --- | --- | --- | --- |
| `candidate` | `candidate-tuna.Dockerfile` | 同 | 同 |
| `build_timeout` | 1800 | **0.01** | **1800（原值）** |
| 请求文件 | `data/e14-sample-tuna.json` | `data/e14-fault-tuna.json` | `data/e14-sample-tuna.json`（**原文件、未修改**） |
| 结果 | SUCCEEDED | **FAILED**，exit 1 | SUCCEEDED |
| job_id | `job-3f0c37ff…` | `job-10410e9704674cb4b81f83325564147d` | `job-72190418df5c47b6a67eba846f79764e` |
| trace_id | `trace-2ca3ddc7…` | `trace-e91ac9dede26487987d3e76d03d475a0` | `trace-8a9a8d9e1818435fb2ed696b6aa1b79e` |

时序与结论：

1. **注入**：`fault-single` 运行后 `status=FAILED`、`stages=[]`、退出码 **1**，错误为 `DRAFT_TIMED_OUT: Docker client command exceeded 0.01s`；五个阶段文件均未生成（`stage_files_absent` 列出全部五项），确认失败任务不产生下游产物。
2. **恢复**：用**同一个请求文件原样**（未改任何字段）在全新目录 `recover-single` 重试 → `SUCCEEDED`，五阶段 `draft/full-check/incremental-check/repair/recheck` 全部 `SUCCEEDED`，五阶段共享同一 job/trace。
3. **干净性**：故障与恢复的 job_id、trace_id 各不相同，说明恢复是全新任务，不是复用故障现场。
4. **判据核对**（`checks/e14_verify_single.py`）：报告哈希一致、补丁哈希一致、`validation` 五项全 `true`、`recheck.commit` 等于 target、`remaining_missing=0`、**162 个产物逐个复算 sha256+bytes 0 处不符**。
5. **确定性旁证**：`recover-single` 的补丁 sha256 与 `sample/`、`recover/` 相同（`88074f66…bd0e5a`），同一 fixture 的修复逻辑稳定复现。三份 `report_sha256` 不同属正常：报告内容含 job_id、trace_id 等任务元数据。

### 5.3 收尾与残留

- 残留检查：无 `e6-draft-replay` 容器残留；第一次运行后仅两个 `[docker-buildx] <defunct>` 僵尸条目（进程已退出，父进程 dockerd 会回收）。
- 收尾：第二次补齐对照后执行 `docker compose -f labs/e13e14/compose.yaml -p e14-241880617 down`，只移除本项目容器与网络；同机其他组容器（如 241880106 的 `mystifying_williams`）未受影响。

## 六、`baseline-failure/` 为什么存在

固定样例首跑用的是教师样例原候选（`apt-get` 走 `deb.debian.org`），draft 在 600 s 内未能完成 `apt-get update`，被判 `DRAFT_TIMED_OUT`。现场实测：

- `deb.debian.org`：60 s 无响应（curl 被 timeout 终止）；
- `mirrors.tuna.tsinghua.edu.cn`：9.2 MB/s，1.4 s 取完 13 MB。

因此固定样例改用仓库内已有的 `data/candidate-tuna.Dockerfile`：**同一 fixture、同一 `FROM` digest、同一修复逻辑（`apt-get install build-essential`）**，仅把 apt 源替换为清华镜像并加 `Acquire::ForceIPv4`。该候选在本仓库已是既有做法（`work/e12-02`、`work/e13-baseline-241880617-01` 均用它跑通）。

结论：固定样例以 `sample/` 为准；`baseline-failure/` 原样保留，作为"网络不可达导致超时、非代码缺陷"的证据，不做删改。

## 七、复现命令

```bash
cd /绝对路径/个人仓库
git checkout 68c5454914b48ee2482fb17cd101ff8b8ee854ce   # 复现须在该候选提交上执行（证据包本身的提交在其之后）
docker build --progress=plain \
  --build-arg BASE_IMAGE=python:3.13-slim@sha256:f82c96458eedc847b233e582eb31336f4954b39cae020b6dcf5b3ed0e5cbcd74 \
  --build-arg DOCKER_CLI_IMAGE=docker:28.5.1-cli@sha256:9190b0613792e658a7783cf14b2d5ace5941bb68ede7276922ea36ee457d76ad \
  -f labs/e11e12/environment/services/buildchecker/Dockerfile -t course-e11e12:241880617 labs/e11e12/environment
python3 run_e11e12.py prepare
export E14_ROOT=$PWD E14_IMAGE=course-e11e12:241880617
docker compose -f labs/e13e14/compose.yaml -p e14-241880617 config --quiet
docker compose -f labs/e13e14/compose.yaml -p e14-241880617 up -d
python3 labs/e13e14/orchestrate.py --request data/e14-sample-tuna.json --out work/e14-compose-sample-02
python3 labs/e13e14/orchestrate.py --request data/e14-real-a05.json  --out work/e14-compose-real-a05-01
python3 labs/e13e14/orchestrate.py --request data/real-request.json   --out work/e14-compose-real-pair-01
# —— 组 1（两处变化）——
python3 labs/e13e14/orchestrate.py --request data/e14-fault-request.json --out work/e14-compose-fault-02   # 期望 exit 1
python3 labs/e13e14/orchestrate.py --request data/e14-sample-tuna.json --out work/e14-compose-sample-03
docker compose -f labs/e13e14/compose.yaml -p e14-241880617 logs --no-color > work/e14-compose-services.log
# —— 组 2（仅 timeout 变化）：先由基准请求派生注入请求 ——
python3 -c "import json,pathlib as p; s=json.loads(p.Path('data/e14-sample-tuna.json').read_text()); s['build_timeout']=0.01; p.Path('data/e14-fault-tuna.json').write_text(json.dumps(s,indent=2)+chr(10))"
python3 labs/e13e14/orchestrate.py --request data/e14-fault-tuna.json  --out work/e14-compose-fault-03   # 期望 exit 1
python3 labs/e13e14/orchestrate.py --request data/e14-sample-tuna.json --out work/e14-compose-sample-04
docker compose -f labs/e13e14/compose.yaml -p e14-241880617 logs --no-color > work/e14-compose-services-02.log
python3 reports/E14/A617/checks/e14_verify.py          # 四次正向 + 组 1
python3 reports/E14/A617/checks/e14_verify_single.py   # 组 2 单变量对照
docker compose -f labs/e13e14/compose.yaml -p e14-241880617 down
```

注：`data/` 与 `work/` 均被 `.gitignore` 忽略，上面的 `data/e14-*.json` 请求文件不在仓库内，需按本节命令现场生成或在执行机保留；归档只收结果侧产物。

## 八、边界声明

- 本轮四容器在本人服务器（阿里云 ECS，Ubuntu 22.04）完成，属于"学生实际项目四容器运行"，不是教师固定样例彩排，也不是 CI 运行；CI 侧另有 `.github/workflows/e13e14.yml` 的 `four-services` 作业。
- **本目录为选摘归档（摘录，非全量）**：`data/`、`work/` 均被 `.gitignore` 忽略，这里只收录判定所需的选摘产物——请求、五阶段 JSON、候选补丁、增量报告、console 日志、服务日志、校验脚本与汇总。未收录的原始文件（镜像构建中间层、`repo/` 检出、各阶段临时目录等）**不在 `SHA256SUMS` 覆盖范围内**。
- `SHA256SUMS` 覆盖本目录内除自身以外的全部文件，`sha256sum -c SHA256SUMS` 全部通过。它能证明的是「**归档内文件自归档之日起未被改动**」，不能据此推断「归档等于全部原始产物」。
- 复现前提：`sha256sum -c` 任何机器可独立执行；`checks/e14_verify*.py` 需要执行机上的 `work/e14-compose-*` 目录（不入库），不具备条件时以 `checks/e14-formal-summary.json`、`checks/e14-single-var-summary.json` 的既有结果为准。
