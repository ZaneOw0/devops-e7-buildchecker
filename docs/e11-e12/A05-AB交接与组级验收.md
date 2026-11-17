# A05 E11–E12：A/B 交接与组级验收

整理人：李泽同 241880106（A 组交接与集成）　日期：2026-11-17
A 组仓库：https://github.com/ZaneOw0/devops-e7-buildchecker （集成分支 `e11-e12-integration`）
B 组仓库：https://github.com/Rowan-hhh/devops-e4-draft （集成分支 `e11-e12-integration`）

## 1. 分工

|成员|学号|E11–E12 负责|PR|个人目录|
|---|---|---|---|---|
|孔鹏宇|241880353|E11-A/B、E12 固定样例与本机 API；真实项目 E11-A，向 B2 交付增量报告|#10（已合入集成分支）|`docs/students/241880353/e11-e12/`|
|饶嘉俊|241880617|换提交实验；A 组仓库内真实项目五阶段；pinned FROM 适配；契约测试 7 项|#12（已合入集成分支；#11 因作者账号不符关闭）|`docs/students/241880617/e11-e12/`|
|李泽同|241880106|跨机 SSH 转发联调、A/B 交接链核对、组级验收、集成到 main|本人 PR（待提交）|`docs/students/241880106/e11-e12/`|

## 2. A/B 真实交接链

真实项目由 B 组 B1（241880360）维护并以 bundle 交付，A、B 两侧各自独立跑通，所有标识可以首尾对上：

```text
B1 project.bundle  sha256 0a74f580…ce608   (B 仓库 reports/E12/B1/, PR #22)
  base   0b62c79a6adb4cd913a814068074575afdbbd18b
  target 745ecf2621c8221b97bf0a5435ace50150ef57d4   helper.c 新增 #include "output_format.h"，Makefile 未声明
        │
        ▼  A：BuildChecker 全量 → EChecker 增量（241880353）
A incremental-check.json  sha256 66e3bfb2…e38a83
  job-701e024edd564902a625716aa9547cf7 / trace-be8e398fc0564ebcb177991840937797
  发现：MISSING helper.o → output_format.h
        │
        ▼  B2（241880610）消费该报告，PR #23
B2 patch:  -helper.o: helper.c   +helper.o: helper.c output_format.h      validation 5/5，最终无 MISSING
        │
        ├─▶ B3（241880300）CI 内 API 联调 job-171994714e734e78a5cdc29346d12a92，PR #24
        ├─▶ B4（241880179）B 仓库最终五阶段 job-a8c716a97754454d990c997cc9929d4b，accepted=true，PR #25
        ├─▶ A 仓库 CLI 五阶段（241880617）job-87743e5eb8134a23ba3f9f487b5814f3，accepted=true
        └─▶ A 仓库跨机 API 五阶段（241880106）job-8863b7eb236943f5aa85ff5934921b30，accepted=true
```

一致性核对（2026-11-17，本人在服务器上执行 `sha256sum` 与 JSON 读取）：

|对象|A 侧|B 侧|一致|
|---|---|---|---|
|B1 bundle|本人从 B 仓库 `reports/E12/B1/project.bundle` 下载：`0a74f580…ce608`|B1 README 同值|✅|
|A 增量报告|241880353 报告：`66e3bfb2…e38a83`|B2/B4 README 同值|✅|
|候选 Dockerfile|`docs/students/241880617/e11-e12/real-candidate.Dockerfile` = 服务器 `data/real-candidate.Dockerfile` = `c7b2ba5b…44af`|—|✅|
|修复补丁|CLI `work/e12-real-01/candidate.patch` = 跨机下载 `xmachine/run-01/files/candidate.patch` = `a7a3be54…142a`|B2 补丁内容相同（一行）|✅|
|复验|两次 A 侧运行 `recheck.json` commit `745ecf26…`，findings 为空|B4 final findings 0|✅|

## 3. 跨机 API 联调（手册 02 §3）

- API：服务器 `127.0.0.1:8081`（本人镜像 `course-e11e12:241880106`，未开放公网端口）。
- 客户端：本人笔记本 `lima-mac.local`，`ssh -N -L 18081:127.0.0.1:8081 <account>@<api-server>`，请求一律发往 `http://127.0.0.1:18081`。
- 结果：`job-8863b7eb236943f5aa85ff5934921b30` / `trace-9769ebf088df433b86390186a9465a42`，SUCCEEDED，清单 174 个产物，四份关键产物三方哈希一致；同键复用、同键改 target 409、越界路径 404、重启后仍可查询。
- 证据：`docs/students/241880106/e11-e12/xmachine/run-01/`；服务端访问日志中客户端地址为 Docker 网桥 `172.17.0.1`（隧道经 sshd 转入），与本机 curl 的记录一一对应。

## 4. 组级验收清单（手册 03 §3）

|#|验收项|结论|证据|
|---|---|---|---|
|1|E11-A：BuildChecker 图接入历史缓存；增量与全量一致|✅|`work/e11-a-01/`（241880353）；换提交 `e11-a-swap-c2b/c3b`（241880617）；本人复跑 `work/e11-a-241880106-01/`|
|2|E11-B：DRAFT 实际构建与镜像运行；固定 MD→Patch→accepted→无 MD|✅|`work/e11-b-01/`（241880353）；本人复跑 `work/e11-b-241880106-01/`|
|3|E12：五阶段完整，修复输入取自本轮真实报告|✅|固定样例 `work/e12-01/`；真实项目 `work/e12-real-01/`（241880617）与跨机 `job-8863b7eb…`（241880106）|
|4|报告 schema、commit、job_id、trace_id、产物 SHA 对应|✅|各人 `数据与联调记录.csv`；本文件 §2 一致性表|
|5|API 提交、轮询、下载；相同幂等键同一任务；冲突请求被拒|✅|本机：241880353、241880617；跨机：`xmachine/run-01/summary.json`；`SERVER_RESTARTED` 探针 `job-d09e0f38…`（241880617）|
|6|真实仓库和提交范围有来源记录，与生成样例分开提交|✅|真实项目来源与 base/target 见 §2；样例标记 `course-generated`；`data/` 不入库|
|7|至少一项新增适配或契约测试，代码经个人分支和 PR 提交|✅|`test_student_241880353.py`（2 项）、`test_student_241880617.py`（7 项）+ `autobuild.py` 修复；全部经 PR #10/#12；`run_e11e12.py test` 共 19 项 OK|

## 5. 已知问题与处理

|问题|处理|
|---|---|
|`test_student_241880617.py` 末行为 `'__&#8203;main__'`（混入 HTML 转义），直接 `python3 文件名` 时不执行测试；`unittest discover` 不受影响|本人 PR 中改为 `'__main__'`|
|241880617 报告中 E11-A 固定样例 `job-7bc187d4…` 与 STALE 演示 `job-f24e0b2d…` 和 241880353 的运行 job_id 相同|属引用组内已有运行；本人在验收清单中按原作者标注出处，建议 241880617 在报告中注明“沿用 241880353 的运行”|
|241880353 报告中 PR 一栏为“推送后补”|本人 PR 中补为 #10|
|main 分支保护只要求 `e7-a-quality-gate`|合入 main 前按手册 04 增加必需检查 `e11e12-integration`|

## 6. 合并顺序

1. ✅ PR #10（241880353）→ `e11-e12-integration`
2. ✅ PR #12（241880617）→ `e11-e12-integration`
3. ⏳ 本人个人分支 `student/241880106/e11-e12` → `e11-e12-integration`
4. ⏳ main 分支保护增加 `e11e12-integration` 必需检查
5. ⏳ `e11-e12-integration` → `main`，三项 CI（E7 质量门禁、E8–E10 回归、E11–E12 集成）全部通过后合并
