# E13 ADR（241880353）

## 个人分支从集成分支拉出

本目录原先停在 `student/241880353/e11-e12`。E13 从 `origin/e13-e14-integration` `4f39fc3` 建 `student/241880353/e13-e14`。E11 未推送的报告和工作总结放进 stash，不带进本分支。

## 清华源样例用本目录 SHA

106 的 `e12-tuna.json` 指向 `76773b7` / `214d221`。那是 106 的 `data/integration-sample/repo`。本目录样例是 `a8e388e` / `38fa178a`。第一次基线因此 `COMMAND_FAILED`，证据保留在 `work/e13-baseline-241880353-01`。第二次用 `e12-tuna-353.json`（同一清华 candidate，本目录 SHA，`build_timeout=1800`）五阶段成功。不把 106 的 sample 仓库拷过来覆盖本目录历史。

## C1 重跑，不用 E11 旧目录

B 项目仍是 E12 B1 bundle。E13 C1 必须新开 `work/e13-c1-b-01`。发现与 E11 `work/e11-a-b1-01` 相同（`MISSING helper.o→output_format.h`），但 job/trace/产物哈希以本轮为准交给 B。

## C2 用“别人的 target SHA”

A 侧 `pipeline.py` 没有 `WRONG_TARGET` 错误码。把 A05 target `90646db8…` 写进 B 项目请求，git 解析失败，外层 `FAILED` / `COMMAND_FAILED`。旧报告是把本轮增量 envelope 的 commit 改成 base，给 B 去拒。

## C7 先失败再成功

失败请求 base 为 40 个 0，与 B3 在 A05 上的做法一致。成功请求与 C1 相同、输出目录不同，用来证明 job/trace/目录隔离。

## 测试放在 e13e14 discover 路径

CI `e13e14.yml` 跑 `labs/e13e14/tests/test_*.py`。新增 `test_student_241880353.py` 覆盖：活报告交接保留 job 与 sha256；base-commit 旧报告被拒；错误 target SHA 被拒。不改 `handoff_a_to_b.py`。
