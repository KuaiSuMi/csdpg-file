# 成熟度评估基线调研与复现

当前四项基线：**Infer/Pulse + feTruth（学术）**，**AppCAT + NeuVector（商用）**。学术两项均有 CCF-A 研究论文依据；实际部署侧由 NeuVector 覆盖。

- [图文调研报告](docs/成熟度评估baseline调研结果.md)：16 张统一样式截图，输入、执行、输出与结果解释。
- [完整输入输出清单](docs/基线输入输出清单.md)：四项固定版本的入口、材料、中间文件、最终输出、字段、状态及支持范围。
- [HTML 图集](results/report-verification/baseline-report.html)：连续查看与保存全部截图内容。
- [学术选型结论](docs/学术基线复审结论.md)、[固定选型与结果入口](baselines/academic-review-manifest.json)。
- [Infer + feTruth 复现指南](docs/两项学术基线复现.md)、[AppCAT + NeuVector 复现指南](docs/两项商用基线复现.md)。
- [原始项目要求](docs/原始项目要求.md)、[论文依据](docs/候选基线权威性评估.md)。

| 基线 | 已有结果 | 解释 |
| --- | --- | --- |
| Infer/Pulse | Java 三项目 6 / 0 / 0 条；空指针 1→0 | 告警尚需复核，0 条只代表本次未报告 |
| feTruth | 论文重放 16/16；新 jsoup 源码 180 条；项目示例 1 条 | 不同输入与模型工作流分开，均非确认缺陷数 |
| AppCAT | 总问题 6→4；去重迁移问题 4→2 | 技术发现信息与迁移问题分开 |
| NeuVector | root true→false；CIS 130 项；CVE 27 条 | 各实验独立，空扫描列表不是通过 |

重绘当前报告：`node scripts/capture_baseline_outputs.cjs`。验证报告与归档结果：`python scripts/verify_academic_results.py`。本次未重跑未变化的业务扫描，也未将旧工具图谱数字当作当前组合的结果。
