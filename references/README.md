# 论文原文与官方资料

更新：2026-11-13。学术基线为 Infer/Pulse + feTruth；商用基线仅保留 Microsoft AppCAT for Java、SUSE Security／NeuVector 开源发行版。其他学术文献继续作为背景材料，不代表已完成对应工具复现。

论文放在 papers/，可离线阅读；正式引用以 DOI 和会议官方发表信息为准。[调研结果](../docs/成熟度评估baseline调研结果.md)记录当前选择与证据范围。

## 1. 已下载的论文

| 对应条目 | 论文题名 | 发表信息 | 本地全文 | 页数 |
|---|---|---|---|---:|
| GLITCH | GLITCH: Automated Polyglot Security Smell Detection in Infrastructure as Code | ASE 2022 Research Papers | [glitch-ase2022.pdf](papers/glitch-ase2022.pdf) | 12 |
| Infer/Pulse | Local Reasoning About the Presence of Bugs: Incorrectness Separation Logic | CAV 2020，225–252 页 | [pulse-cav2020.pdf](papers/pulse-cav2020.pdf) | 28 |
| Pulse-X（相关方法，未运行其归档） | Finding Real Bugs in Big Programs with Incorrectness Logic | OOPSLA 2022 / PACMPL 6, OOPSLA1, Article 81 | [pulse-x-oopsla2022.pdf](papers/pulse-x-oopsla2022.pdf) | 27 |
| feTruth | Deep Learning Based Feature Envy Detection Boosted by Real-World Examples | ESEC/FSE 2023 | [fetruth-fse2023.pdf](papers/fetruth-fse2023.pdf) | 13 |
| Kivi | Kivi: Verification for Cluster Management | USENIX ATC 2024，509–527 页 | [kivi-atc2024.pdf](papers/kivi-atc2024.pdf) | 20（含封面） |
| Reynard | Automated Network-Level Fault Injection Testing of Microservice Architectures | ICSE 2026 | [reynard-icse2026.pdf](papers/reynard-icse2026.pdf) | 12 |
| Filibuster | Service-Level Fault Injection Testing | SoCC 2021 | [filibuster-socc2021.pdf](papers/filibuster-socc2021.pdf) | 15 |
| Arcan | Arcan: a Tool for Architectural Smells Detection | ICSA Workshops（ICSAW）2017 | [arcan-2017.pdf](papers/arcan-2017.pdf) | 4 |
| DECOR | DECOR: A Method for the Specification and Detection of Code and Design Smells | IEEE TSE，36(1): 20–36，2010 | [decor-tse2010.pdf](papers/decor-tse2010.pdf) | 17 |
| RefactoringMiner | Accurate and Efficient Refactoring Detection in Commit History | ICSE 2018 | [refactoringminer-icse2018.pdf](papers/refactoringminer-icse2018.pdf) | 12 |

Infer/Pulse、feTruth 是本轮两项；GLITCH、Kivi、Reynard 的论文和实验保留为历史材料；Filibuster 是此前已运行的会议候选。Arcan、DECOR、RefactoringMiner 目前只完成调研，下载论文不代表完成了工具复现。RefactoringMiner 用于识别提交历史中的重构，可作为后续数据构建或修改核对的辅助工具。

### 原文来源、发表页与实现

新两项的发表页、作者仓库与执行版本关系统一见[最新复审](../docs/学术基线复审结论.md)。以下包含当前方法及历史候选来源。

- **Kivi**：[USENIX 官方 PDF](https://www.usenix.org/system/files/atc24-liu-bingzhe.pdf)；[正式会议页面](https://www.usenix.org/conference/atc24/presentation/liu-bingzhe)；[作者代码](https://github.com/bingzheliu/Kivi)。本轮固定提交 81e6c253573b0cc41727885948c1240892d1a6e2；SPIN 固定提交 090f74209025a53297990ec17deca1bd51cb92a5。实际复现为 C3 固定拓扑模型、作者对照及 YAML 修改对照，未覆盖全部论文实验。
- **feTruth**：[作者提供的 PDF](https://lyoubo.github.io/papers/Deep_Learning_Based_Feature_Envy_Detection_Boosted_by_Real-World_Examples.pdf)；[会议论文页](https://2023.esec-fse.org/details/fse-2023-research-papers/112/Deep-Learning-Based-Feature-Envy-Detection-Boosted-by-Real-World-Examples)；[DOI](https://doi.org/10.1145/3611643.3616353)；[代码仓库](https://github.com/lyoubo/feTruth)；[实验材料](https://doi.org/10.5281/zenodo.8267775)。
- **Reynard**：[作者提供的 PDF](https://burcuku.github.io/home/assets/pdf/icse26.pdf)；[会议论文页](https://conf.researchr.org/details/icse-2026/icse-2026-research-track/151/Automated-Network-Level-Fault-Injection-Testing-of-Microservice-Architectures)；[DOI](https://doi.org/10.1145/3744916.3773193)；[复现版本代码](https://github.com/reynard-testing/reynard/tree/v0.2.2-artifact)。
- **Filibuster**：[作者提供的 PDF](https://rohan.padhye.org/files/filibuster-socc21.pdf)；[DOI](https://doi.org/10.1145/3472883.3487005)；[工具源码](https://github.com/filibuster-testing/filibuster)；[实验系统](https://github.com/filibuster-testing/filibuster-corpus)；[作者方法介绍](https://christophermeiklejohn.com/filibuster/2021/10/02/filibuster-1.html)。
- **Arcan**：[米兰比可卡大学机构库 PDF](https://boa.unimib.it/retrieve/e39773b3-de57-35a3-e053-3a05fe0aac26/PID4705339.pdf)；[DOI](https://doi.org/10.1109/ICSAW.2017.16)。仅保留 ICSA Workshops 2017 学术文献，不作为入选商用方案。
- **DECOR**：[作者团队提供的 PDF](https://assets.ptidej.net/Publications/Documents/TSE09.doc.pdf)；[DOI](https://doi.org/10.1109/TSE.2009.50)；[方法、规则与实现入口](https://www.ptidej.net/research/designsmells)。下载文件名含 `TSE09`，正式卷期为 2010 年；本地文件按正式发表年份命名。
- **RefactoringMiner**：[作者提供的 PDF](https://users.encs.concordia.ca/~nikolaos/publications/ICSE_2018.pdf)；[DOI](https://doi.org/10.1145/3180155.3180206)；[代码仓库](https://github.com/tsantalis/RefactoringMiner)；[官方论文与引用列表](https://github.com/tsantalis/RefactoringMiner/blob/master/documentation/research.md)。此处保存 ICSE 2018 原始方法论文，后续版本论文可从引用列表继续查阅。

## 2. 商用方案官方资料

| 方案 | 官方来源 | 本地复现依据 |
| --- | --- | --- |
| AppCAT | [产品与许可](https://learn.microsoft.com/en-us/azure/migrate/appcat/java?view=migrate)、[CLI](https://learn.microsoft.com/en-us/azure/migrate/appcat/appcat-7-cli-guide?view=migrate) | [固定版本与包校验](../baselines/commercial-manifest.json)、[原生规则](../results/commercial/appcat/20261111-paired/native-local-storage.yaml) |
| NeuVector | [SUSE 部署说明](https://documentation.suse.com/en-us/cloudnative/security/5.6/en/installation.html)、[固定源码](https://github.com/neuvector/neuvector/tree/v5.6.4) | [API 定义](neuvector/apis-5.6.4.yaml)、[原生风险统计源码](neuvector/score-metrics-5.6.4.go) |

安装、命令、原始结果和限制见[两项商用基线复现](../docs/两项商用基线复现.md)。

## 3. 会议分类依据

现有 [ccf-seventh.pdf](ccf-seventh.pdf) 是中国计算机学会 2026 年第七版推荐目录。第 1 页标注 2026 年，第 27 页的 A 类会议表包含 FSE、ICSE、ASE、OOPSLA，第 41 页的 A 类表包含 CAV，第 6 页将 SoCC 列为 B 类。

第 5 页 A 类表列出 ACM SIGOPS ATC，并注明“原 USENIX ATC”。Kivi 的正式发表名称是 USENIX ATC 2024。本轮 ATC 分类核对本地 PDF；CCF 对应在线学科页返回 HTTP 405，未将其记为本轮成功访问。正式论文身份另由 USENIX 会议页确认。

文件来自 [GitHub 镜像](https://github.com/LovenSar/CCF_RANK)，原始下载地址与 SHA256 在 [baselines/manifest.json](../baselines/manifest.json)。分类同时对照 [CCF 官方学科目录](https://www.ccf.org.cn/Academic_Evaluation/TCSE_SS_PDL/)和 [FSE 更名说明](https://www.ccf.org.cn/Academic_Evaluation/By_category/2024-06-28/825349.shtml)。镜像用于本地复核，不把镜像维护者视为分类制定者。

原有 CCF、feTruth、Reynard 在线材料首次核对日期为 2026 年 10 月 13 日；原有六篇论文下载于 2026 年 10 月 21 日。

## 4. 归档说明

[download-manifest.json](download-manifest.json) 保存论文来源、下载时间、页数和 SHA256。商用工具版本、镜像与结果入口记录在[商用清单](../baselines/commercial-manifest.json)。本轮实际运行了 GLITCH 与 Infer/Pulse，旧工具结果按证据复用；见[新复现指南](../docs/两项学术基线复现.md)。
