# AI使用记录

工具/模型/日期：WorkBuddy 智能体（GLM），2026-11-03。

输入上下文与问题：
提供E8—E10实验包材料（操作手册、lab.py源码、模板）与实时粘贴的服务器命令输出；
问题包括：实验流程解读、E8/E9/E10逐步命令、断言含义、独立测试的设计方向与报告填写。

模型建议（被采纳部分）：
1. 按手册8的分步路线生成lab_python命令块，并解释每步通过条件；
2. 建议自主测试以手册08的2A为骨架（fixture→scan→修改→commit→scan(p,old)），
   并提出"修改unused.h内容"作为区别于2A的独立输入变化方向，及其预期（key失效→全目标保守刷新，实际图不变）；
3. 给出报告/ADR/AI_USAGE的填写要点与E8实测数据的整理方式；
4. E9阶段：按手册9展开C0→C3分步命令与预期说明；解释复用分支机制（key不含Makefile声明行、
   预处理指令不进key所以函数体变化不失效）与MD/RD分开演化的含义；
   设计E9独立测试方向（helper.c新增include"extra.h"）及其独立预期（MD按目标归属helper.o）；
5. E10阶段：展开六场景×5次成对测量命令与预期表；解读性能数据（复用场景约5.7-5.9倍、
   刷新场景约1.0）；核实lab.py:52-53实现后提出E10测试方向（删RD声明，覆盖MD/RD生命周期
   未涉及的RD消除侧）及其独立预期（复用分支+RD消失+MD保留）。

采纳/拒绝及理由：
采纳上述1—5。理由：命令与手册一致；E8测试与2A形成互补验证维度（声明变化 vs 内容变化）；
E9测试与2C形成区分（2C验证传递include、本测试验证目标归属）；
E10测试与E9的C3形成对照（声明扩张消MD vs 声明收缩消RD），且方向选择基于实现核实而非猜测。
拒绝部分：无重大拒绝；对AI给出的报告初稿逐项核对了服务器实测值
（SHA df672d3c9…、镜像sha256:4004…、trace t.15:579、make-db.txt:1044/1052、
E9内层提交361dde8/aea0819/1b85c32/60a1733、E10内层提交58f291b9…40b6aec5、
30行equal=True、10项测试OK）后才采用。

人工修改：
所有命令由本人在服务器上逐条执行；测试代码（E8版/E9版/E10版）由本人用nano写入test_profile.py并核对缩进；
结论.txt中的证据坐标（t.15:579、make-db:1044/1052）为本人根据本次实际输出确定；
报告中的全部数值均与 $OUT 证据目录逐项对照，非AI生成后未核对的转写。

实际验证命令/输入/结果：
- E8主线：lab_python 分步执行 fixture/scan/buildchecker/scan(old)，
  BASELINE_PASS、BUILDCHECKER_BASELINE_PASS、REUSE_PASS ['main.o','helper.o'] []，各步STEP_EXIT_CODE=0；
- E9主线：lab_python 分步执行 C0 make+scan → C1改函数体 → C2加include → C3补声明，
  C0_BUILD_AND_BASELINE_PASS、C1_REUSE_PASS、C2_REFRESH_PASS、C3_RESOLVED_PASS，各步STEP_EXIT_CODE=0；
- E10主线：六场景各5次成对扫描，30行equal=True，MATRIX_PASS六类各5，
  DYNAMIC_CROSSCHECK_AND_MATRIX_PASS（最终BuildChecker只剩RD）；
- 新增测试：unittest discover 10项全OK（原包7+E8版+E9版+E10版），TEST_EXIT_CODE=0。

贡献边界：
AI辅助了流程解读、命令组织、测试骨架与文档初稿；
输入变化方向确认、独立预期写定、全部执行、结果验证、证据数值核对由本人完成；
E8实验（基线建立、复用验证、BuildChecker交叉核对）、E9实验（C0→C3增量失效与发现演化验证）
与E10实验（六场景一致性矩阵、性能统计、最终动态重检）均由本人在服务器实际运行产生。
