# ADR：集成接口决策

编号、日期、作者：ADR-E11E12-241880353 / 2026-11-12 / 孔鹏宇 241880353

问题：A 组要把 BuildChecker 全量图接到 EChecker 增量检测，再把增量报告交给 B 组修 Makefile。真实项目来自 B 组 B1，不是课程 `prepare` 样例。需要决定：改不改 `scan`、报告怎么封装、和 B 组怎么交接。

候选方案：
1. 改 `pipeline.snapshot` / `lab.declarations`，为任意文件名和规则做适配。
2. 保持 E8–E10 的 `main.c`/`helper.c`/`config.h` 显式规则接口，真实项目只要仍符合该接口就直接跑；个人贡献放在测试和交接 JSON。
3. 用 SSH `-L` 让 B 组打本机 API；或只把 `incremental-check.json` 文件交给 B2。

采用方案与原因：选 2 和文件交接。B1 项目仍是两个 `.c` 加 `config.h`，多一个 `output_format.h` 不违反 `snapshot` 检查。改检测实现会动全组正在用的参考行为。SSH 是多人分机时的可选项；手册要求的联调在本机五阶段和 localhost API 已经做过。

输入输出字段：消费者认 `e11e12-1` envelope 的 `schema_version`、`job_id`、`trace_id`、`kind`、`commit`、`status`、`data`、`artifacts`。`data` 仍是 `e8e10-1` 的 scan 报告。`commit` 必须等于修复目标，否则 `STALE_REPORT`。产物用 `artifact://job编号/相对路径` 和内容 SHA256。基线 SHA 和目标 SHA 分开记录。

兼容性与测试：不改 `pipeline.py`。`labs/e11e12/test_student_241880353.py` 覆盖 helper 新本地头文件的 MD，以及 envelope 提交不一致。`python3 run_e11e12.py test`，镜像 `course-e11e12:241880353`，12 项通过，日志 `work/unit-tests-e11e12-241880353.log`。
