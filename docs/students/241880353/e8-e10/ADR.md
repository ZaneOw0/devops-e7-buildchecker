# 决策记录

背景与约束：A 组 E8–E10 使用课程受限 C/Make 参考实现。`labs/e8e10/lab.py` 的 `scan` 在预处理指令、Makefile 配方、CFLAGS 和编译器版本都不变时复用历史实际图。`main` 上已有 241880106 的间接包含测试和 241880617 的 `unused.h` 内容变化测试。本次个人贡献只增加一个测试，不改检测实现，也不提交。

选择与替代方案：选择 `StudentE8A241880353.test_function_body_change_reuses_historical_graph`。输入把 `helper.c` 的返回值从 0 改成 2，不增加以 `#` 开头的行。预期两个目标复用，实际图和发现保持不变。另一个方案是修改 `scan`，只刷新受影响目标；那会改变全组正在使用的参考行为，这次没有做。

代价与覆盖范围：测试证明函数体变化留在复用分支，不证明细粒度刷新。声明行变化、间接包含和冗余头文件内容变化仍由已有测试覆盖。

验证命令与实际证据：镜像 `course-e8e10:241880353` 中运行 `python3 -m unittest discover -s labs/e8e10 -p test_profile.py -v`。日志 `work/unit-tests-20261109-010847.log`，14 项通过，退出码 0。
