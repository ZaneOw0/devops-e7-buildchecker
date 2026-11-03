# 决策记录

背景与约束：
E8—E10自主任务要求每人每个实验增加一个有独立预期的测试（或一项实现改动）。E8主题"历史图建立与未变化输入复用"，
E9主题"增量失效与发现演化"（C0→C3），E10主题"一致性与性能"（六场景×5次成对测量+三集合全等断言）。
失效签名key由预处理指令行、Makefile recipe行、CFLAGS、编译器版本构成，key不变则复用历史图，key变化则保守刷新全部目标；
Makefile声明行不在key内。约束：不得破坏原包7项测试；不得在已结束的样例OUT中改文件；报告须写明参考来源与自己改动边界。

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

E10决策：
选择：新增测试 StudentE10A241880617.test_remove_redundant_declaration_clears_rd，
输入变化为Makefile声明行删去unused.h（文件保留在磁盘）。
独立预期：声明不在key→实际图走复用分支（reused=[main.o,helper.o]，refreshed=[]）；
declared['main.o']收缩为['main.c']；RD unused.h从findings消失；MD config.h保留。
动机：E9的C3验证了声明扩张消除MD，MD/RD生命周期中"RD消除"侧此前未被任何人覆盖，
本测试补上这一维，且与E8/E9测试的失效路径（key失效→刷新）形成对照（本测试走复用分支）。
替代方案A（未选）：删除unused.h文件。未选依据：设计前核实lab.py:52-53——directives来自现存文件的glob，
declared来自Makefile解析，二者解耦；删文件既不消除RD（声明仍在），又混入第二种失效源（key文件集合变化），
归因不干净。
替代方案B（未选）：CFLAGS改为-O2再加一轮五次测量。未选原因：与矩阵flags场景（-O0→-O1）机制完全相同，
仅换数值，不构成独立验证维度。

代价与覆盖范围：
E8代价：保守失效粒度粗——unused.h内容变化与实际依赖图完全无关仍导致全刷新，"实际图未变也重扫"是"以正确性优先"策略的固有代价。
E10补充观察：矩阵实测刷新场景full_over_inc≈0.96-0.99，即key失效时增量路径相对全量无收益（小样例下固定开销主导）；
复用场景收益约5.7-5.9倍。三个测试均依赖fixture固定样例，未覆盖多目标部分刷新与真实规模项目场景。

验证命令与实际证据：
docker run --rm --network none --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$PWD:/course" -w /course course-e8e10:241880617 \
  python3 -m unittest discover -s labs/e8e10 -p test_profile.py -v
实际结果（E8轮）：Ran 8 tests，全部OK；E9轮：Ran 9 tests，全部OK；E10轮：Ran 10 tests（原包7+新增3），全部OK，TEST_EXIT_CODE=0。
E10主线：六场景×5=30行equal=True，MATRIX_PASS六类各5，gate.json passed=true；
最终BuildChecker交叉核对SUCCEEDED且findings只剩RD，与扫描器一致（trace_id e6-8943394f…）。
