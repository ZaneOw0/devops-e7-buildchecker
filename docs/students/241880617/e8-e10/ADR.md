# 决策记录

背景与约束：
E8—E10自主任务要求每人每个实验增加一个有独立预期的测试（或一项实现改动）。E8主题是"历史图建立与未变化输入复用"，
E9主题是"增量失效与发现演化"（C0→C3）。失效签名key由预处理指令行、Makefile recipe行、CFLAGS、编译器版本构成，
key不变则复用历史图，key变化则保守刷新全部目标；Makefile声明行不在key内。
约束：不得破坏原包7项测试；不得在已结束的样例OUT中改文件；报告须写明参考来源与自己改动边界。

E8决策：
选择：新增测试 StudentE8A241880617.test_unused_header_content_change_forces_refresh，
输入变化为修改"被声明依赖但从未被实际包含"的 unused.h 文件内容。
替代方案A（未选）：手册08参考用例2A——只补main.o的config.h声明。未选原因：2A是手册给出的参考，
直接照抄不属于独立设计，且它验证的是"key不变时声明图更新"，与我想验证的失效方向不同。
替代方案B（未选）：修改CFLAGS触发刷新。未选原因：flags变化属于E10六场景的验证范围，留给E10更合适。
替代方案C（未选）：修改lab.py实现。未选原因：E8阶段尚未发现实现缺陷，无动机支撑实现改动。

E9决策：
选择：新增测试 StudentE9A241880617.test_helper_include_adds_target_specific_md，
输入变化为helper.c新增 #include "extra.h"。
独立预期：key失效→全目标保守刷新；actual['helper.o']=['extra.h','helper.c']；
added新增MISSING helper.o→extra.h（MD按目标归属helper.o，而非main.o）；main.o实际依赖不变。
替代方案（未选）：手册08参考用例2C——在config.h中加入include"extra.h"使main.o经传递包含依赖extra.h。
未选原因：2C验证的是"间接include引起的传递失效"，直接照抄不属于独立设计；
我改在helper.c直接包含，验证的是另一个维度——扫描器按目标区分实际依赖（MD落在helper.o而非main.o），
两个方向互补但不重复。
代价：该测试与E8测试同为"预处理指令变化→全刷新"路径，未覆盖"key不变但声明变化"的分支
（该分支由C3主线性质与2A参考覆盖）；测试粒度依赖fixture固定样例，未覆盖多目标部分刷新场景。

代价与覆盖范围（E8）：
保守失效粒度粗——unused.h内容变化虽然与实际依赖图完全无关（无人包含它），
仍导致main.o与helper.o全部刷新，存在"实际图未变也重扫"的开销；这是"以正确性优先"策略的固有代价。
覆盖范围：仅覆盖"单头文件内容变化"维度；间接include传递失效由2C场景覆盖，C2主线场景覆盖直接include新增。

验证命令与实际证据：
docker run --rm --network none --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$PWD:/course" -w /course course-e8e10:241880617 \
  python3 -m unittest discover -s labs/e8e10 -p test_profile.py -v
实际结果（E8轮）：Ran 8 tests（原包7项+本人E8测试）全部OK，TEST_EXIT_CODE=0。
实际结果（E9轮）：Ran 9 tests（原包7项+E8测试+E9测试）全部OK，TEST_EXIT_CODE=0；
E9主线四步验证 C0_BUILD_AND_BASELINE_PASS / C1_REUSE_PASS / C2_REFRESH_PASS / C3_RESOLVED_PASS
各步STEP_EXIT_CODE=0，内层提交361dde8→aea0819→1b85c32→60a1733。
