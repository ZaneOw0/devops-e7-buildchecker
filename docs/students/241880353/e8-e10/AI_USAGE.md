# AI使用记录

工具/模型/日期：Cursor 中的 Grok 4.7；2026-11-09。学号 241880353；A 组 E8–E10。

输入上下文与问题：
课程材料在 `devops-materials/DevOps_E8_E10`。问题包括 E8–E10 要做什么、克隆到服务器还是本机、GitHub 登录、个人分支、镜像、三次手册怎么核对，以及提交应该有几条。

模型建议：
1. 把组仓库克隆到服务器 `~/devops-students/241880353/buildchecker`，从当时的 `main` 建立本地分支 `student/241880353/e8-e10`。
2. 按 A 组手册分步运行，E8、E9、E10 各用一个新的 `work/` 目录。
3. 个人测试不重复组里已有的间接包含和 `unused.h` 内容变化，改为只改 `helper.c` 的函数体，预期历史图继续复用。
4. 本地只做一次提交，把测试和三份文档放在一起。`work/` 不进入 Git。同学的多条提交来自他们分次记录实验和后来的 Actions 证据，不是必须凑满同样的条数。

采纳/拒绝及理由：
采纳 1–3。镜像、三次手册路线和测试代码先由模型在服务器上执行并写入；随后本人要求改为自己执行命令。本人在终端重新核对了 E8、E9、E10 的结果，并自己运行了 14 项单元测试，结果与已保存证据一致。
拒绝在本人确认前提交或推送。SSH 密钥曾因 `github.com` 超时而生成，后来没有使用，并已删除。

人工修改：
本人执行并确认的命令是 E8、E9、E10 的结果核对，以及下面的单元测试。测试文件和三份文档的初稿由模型根据当时的运行输出写成；本记录在提交前按实际分工改过。报告中的 OUT、提交号、证据行号和计时来自本次 `work/` 目录，不是另外两位同学报告里的数字。

实际验证命令/输入/结果：
本人在 `~/devops-students/241880353/buildchecker` 执行核对和测试。

- E8：`work/e8-A-manual.3tHweu`。历史图来自 BuildChecker，`findings_status` 为 `SUCCEEDED`；`reused` 为 `main.o`、`helper.o`，`refreshed` 为空；发现为 MD `main.o -> config.h`、RD `main.o -> unused.h`。
- E9：`work/e9-A-manual.ccvWqV`。C0 与 C1 有 MD `config.h` 和 RD `unused.h`；C2 新增 MD `extra.h`；C3 只剩 RD `unused.h`。
- E10：`work/e10-A-manual.LEj7d7`。六段变化与预期一致，30 行全部相同，`passed` 为 `True`；最终 BuildChecker 状态 `SUCCEEDED`，只剩 RD `unused.h`。
- 测试：本人运行 `python3 -m unittest discover -s labs/e8e10 -p test_profile.py -v`，`Ran 14 tests`，结果 `OK`。其中 `test_function_body_change_reuses_historical_graph` 通过。

贡献边界：
课程参考实现是 `labs/e8e10/lab.py`，这次没有改检测算法。新增内容是函数体复用测试和三份记录。模型起草了测试和文档；实验是否通过由本人在终端核对。
