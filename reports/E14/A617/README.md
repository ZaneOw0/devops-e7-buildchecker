# E14 四容器正式验收证据（241880617 / A05）

## 一、验收对象

| 项 | 值 |
| --- | --- |
| 候选提交 | **`68c5454914b48ee2482fb17cd101ff8b8ee854ce`**（PR #26 合并提交 M，2026-11-24T10:56:49Z，`main` 当前指向） |
| 判定提交 | `1f6ef6b`（集成分支上的 T5 门禁判定）；M 与它的差异仅 `reports/E13/cross-test-record.md` 自身 |
| 镜像 | `course-e11e12:241880617`，ID **`sha256:9b19710406eb6e2d35454fb36889e3da8fd163ac82a9f035418bcd605c4cd134`** |
| 镜像构建 | 在 M 上执行 `docker build`（BASE_IMAGE / DOCKER_CLI_IMAGE 均按 digest 固定），全层命中缓存，`Created` 仍为 2026-11-10T18:54:41+08:00 —— 说明 M 的教学镜像定义与原构建逐字节一致 |
| 编排入口 | `labs/e13e14/orchestrate.py`（四角色经 HTTP 传递阶段数据） |
| Compose 项目 | `e14-241880617`，端口仅 `127.0.0.1:18081–18084` |
| 四角色健康 | `buildchecker` / `echecker` / `draft` / `mdfixer` 启动后均为 `healthy`（`docker compose ps`） |

## 二、运行清单

| 目录 | 类型 | base → target | job_id | 五阶段 | 产物 | 补丁 sha256 |
| --- | --- | --- | --- | --- | --- | --- |
| `sample/` | 固定样例（镜像源适配候选） | `d77b4d86` → `03195569` | `job-3f0c37ff14874dd78d775ffd2f5a41a9` | 5/5 SUCCEEDED | 162 | `88074f66…bd0e5a` |
| `real-a05/` | 真实项目：A05 本组 | `6b9deff5` → `90646db8` | `job-59c9c4af21d0499ba9aaead8e41fcc20` | 5/5 SUCCEEDED | 181 | `0030f288…bef9db` |
| `real-pair/` | 真实项目：配对侧 | `0b62c79a` → `745ecf26` | `job-b281badaae9542ce94f76dbd6e72d57a` | 5/5 SUCCEEDED | 180 | `a7a3be54…b5142a` |
| `recover/` | 故障恢复后重试 | `d77b4d86` → `03195569` | `job-25293e0821aa42b796222fd82c751161` | 5/5 SUCCEEDED | 162 | `88074f66…bd0e5a` |
| `fault/` | 受控故障（`build_timeout=0.01`） | `d77b4d86` → `03195569` | `job-d223d409fae0451ab327ea7ebc758a5c` | 0（外层 exit 1） | — | — |
| `baseline-failure/` | 固定样例首跑（官方 apt 源不可达） | `d77b4d86` → `03195569` | `job-2e02e91c2bec4a569c70a2e7f4f8cfcb` | 0（draft 600s 超时） | — | — |

固定样例与真实项目分别记录，**未把样例结果写成真实项目结果**。

## 三、判据核对（`checks/e14-formal-summary.json`，由 `checks/e14_verify.py` 生成）

三次正向运行 + 一次恢复运行，逐项满足：

1. `result.json` 为 `SUCCEEDED`，阶段顺序严格为 `draft → full-check → incremental-check → repair → recheck`；
2. 五个阶段文件各自 `status=SUCCEEDED`，且 `job_id`/`trace_id` 与 `result.json` 完全一致（同一任务贯穿四角色）；
3. `incremental-check.data.sha256` 与该阶段 report 文件（`incremental/incremental-check.json`）实算 sha256 一致 —— A→B 报告来源可追溯；
4. `repair.data.sha256` 与补丁文件实算一致，`validation.accepted=true`，`checks={patch_applies,build,test,header_change,no_missing}` 全为 `true`；
5. `recheck.commit` 等于目标提交，`remaining_missing=0`，`findings` 中无 `MISSING`；
6. `result.json` 登记的全部产物逐项复算 sha256 与字节数：**685 个产物，0 处不符**（162+181+180+162）。

## 四、四角色确实处理了本轮任务（不只是 healthy）

`services/e14-compose-services.log`（784 行，26 条结构化记录）按 job 统计：

| job | buildchecker | echecker | draft | mdfixer |
| --- | --- | --- | --- | --- |
| `job-3f0c37ff…` | 3 | 1 | 1 | 1 |
| `job-59c9c4af…` | 3 | 1 | 1 | 1 |
| `job-b281bada…` | 3 | 1 | 1 | 1 |
| `job-25293e08…` | 3 | 1 | 1 | 1 |
| `job-d223d409…`（故障） | — | — | 1（FAILED） | — |

每条记录含 `role`、`job_id`、`trace_id`、`status`、`elapsed_ms`；全部为 `SUCCEEDED`，故障 job 的 draft 记录为 `FAILED`。

日志扫描：`scan_runtime_logs.py` 对服务日志与四个证据目录分别执行，均 `hits=0 errors=0`（见 `checks/*.scan.log`）。

## 五、受控故障与恢复

- 注入方式：复制固定样例请求，`build_timeout` 由 600 改为 **0.01**，全新目录 `work/e14-compose-fault-02` 运行。
- 预期与实际一致：DRAFT 返回 `DRAFT_TIMED_OUT: Docker client command exceeded 0.01s`，外层 `result.json` 为 `FAILED`、`stages=[]`、编排退出码 **1**；失败任务不显示成功。
- 恢复：用原时限在全新目录 `work/e14-compose-sample-03` 重试，`SUCCEEDED`，job/trace 与故障那次不同（`job-25293e08…` / `trace-c81aef73…`），证明恢复后是干净的新任务。
- 残留检查：无 `e6-draft-replay` 容器残留；仅两个 `[docker-buildx] <defunct>` 僵尸条目（进程已退出，父进程 dockerd 会回收）。
- 收尾：`docker compose -f labs/e13e14/compose.yaml -p e14-241880617 down`，只移除本项目容器与网络，未触碰同机其他组容器。

## 六、`baseline-failure/` 为什么存在

固定样例首跑用的是教师样例原候选（`apt-get` 走 `deb.debian.org`），draft 在 600 s 内未能完成 `apt-get update`，被判 `DRAFT_TIMED_OUT`。现场实测：

- `deb.debian.org`：60 s 无响应（curl 被 timeout 终止）；
- `mirrors.tuna.tsinghua.edu.cn`：9.2 MB/s，1.4 s 取完 13 MB。

因此固定样例改用仓库内已有的 `data/candidate-tuna.Dockerfile`：**同一 fixture、同一 `FROM` digest、同一修复逻辑（`apt-get install build-essential`）**，仅把 apt 源替换为清华镜像并加 `Acquire::ForceIPv4`。该候选在本仓库已是既有做法（`work/e12-02`、`work/e13-baseline-241880617-01` 均用它跑通）。

结论：固定样例以 `sample/` 为准；`baseline-failure/` 原样保留，作为"网络不可达导致超时、非代码缺陷"的证据，不做删改。

## 七、复现命令

```bash
cd /绝对路径/个人仓库
git rev-parse HEAD                      # 应等于 68c5454914b48ee2482fb17cd101ff8b8ee854ce
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
python3 labs/e13e14/orchestrate.py --request data/e14-fault-request.json --out work/e14-compose-fault-02   # 期望 exit 1
python3 labs/e13e14/orchestrate.py --request data/e14-sample-tuna.json --out work/e14-compose-sample-03
docker compose -f labs/e13e14/compose.yaml -p e14-241880617 logs --no-color > work/e14-compose-services.log
python3 /tmp/e14_verify.py     # 见 checks/e14_verify.py
docker compose -f labs/e13e14/compose.yaml -p e14-241880617 down
```

## 八、边界声明

- 本轮四容器在本人服务器（阿里云 ECS，Ubuntu 22.04）完成，属于"学生实际项目四容器运行"，不是教师固定样例彩排，也不是 CI 运行；CI 侧另有 `.github/workflows/e13e14.yml` 的 `four-services` 作业。
- `data/`、`work/` 被 `.gitignore` 忽略；本目录是挑选后的关键产物，其余原始文件用 `SHA256SUMS` 覆盖到逐文件哈希。
