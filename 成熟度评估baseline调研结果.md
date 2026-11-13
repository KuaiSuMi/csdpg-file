# 成熟度评估 baseline 调研结果

更新：2026-11-13。学术基线固定为 **Infer/Pulse + feTruth**，商用基线保留 **Microsoft AppCAT for Java + SUSE Security/NeuVector**。两项学术均有 CCF-A 研究论文依据，不需要逐项目编写业务规则。BARO、Parfum、GLITCH、Kivi、Reynard 不计入当前四项主基线。

本报告复用已核验的原始实验，统一重绘 16 张截图。各图使用相同字号、配色、标题、输入—执行—输出结构；图中注明实测日期或接口核对状态。它们是原生数据的报告重排，不冒充工具原生界面。16 张图均嵌入下文。

[完整输入输出清单](#inputs-outputs)覆盖四项固定版本的分析入口、必需与可选材料、中间文件、最终输出、字段和结果状态，并附完整 CLI/API 与 Pulse 问题类型目录。**官方支持但未实测的入口单独标注**，不把可能出现的输出伪造成实测截图。

## 1. 选型与分工

| 类别 | 基线与版本 | 输入 | 输出 | 当前证据 |
| --- | --- | --- | --- | --- |
| 学术 | Infer 1.3.0 / Pulse，CAV 2020，CCF-A | 支持语言源码、编译依赖、正常构建命令 | 程序错误类型、文件行号、原因、调用路径 | Java 三项目 6 / 0 / 0 条；空指针对照 1→0 |
| 学术 | feTruth，ESEC/FSE 2023，CCF-A | Java 源码，或论文归档特征；固定模型 | Feature Envy 候选及 Move Method 建议 | 论文重放 16/16 一致；新 jsoup 源码 180 条候选；项目示例 1 条 |
| 商用 | AppCAT 7.7.0.11 | 应用源码或二进制、迁移目标；本轮 Java 源码 | 迁移规则、位置、严重程度、建议、技术栈和依赖 | 原生总问题 6→4；去重迁移问题 4→2 |
| 商用 | NeuVector 5.6.4 | 实际集群/容器、节点、镜像、运行监测数据 | 权限风险、进程和网络、CIS、CVE、全局风险分项 | root true→false；CIS 130 项；CVE 27 条 |

Infer 对照源码正确性诊断，feTruth 对照方法职责与重构建议。两项都属于源码侧；实际部署侧由 NeuVector 覆盖。该组合不单独验证微服务业务容错或自动修复能力，不能合成一个未经定义的成熟度总分。

“简单配置”限定在各工具支持范围：Infer 需要可正常构建的项目；feTruth 首次需准备旧 Python/Keras 环境和模型；AppCAT 需要迁移目标；NeuVector 需要平台与扫描组件。之后复用检测器/模型，不为每个业务编写断言。

Infer 的研究依据是 CAV 2020 论文 *Local Reasoning About the Presence of Bugs: Incorrectness Separation Logic*，DOI [10.1007/978-3-030-53291-8_14](https://link.springer.com/chapter/10.1007/978-3-030-53291-8_14)。本轮执行 Infer 1.3.0 Pulse，不是 CAV 原始归档程序，也不是 OOPSLA 2022 Pulse-X 原型。

feTruth 的依据是 ESEC/FSE 2023 研究论文 *Deep Learning Based Feature Envy Detection Boosted by Real-World Examples*，DOI [10.1145/3611643.3616353](https://doi.org/10.1145/3611643.3616353)，对应[会议论文页](https://2023.esec-fse.org/details/fse-2023-research-papers/112/Deep-Learning-Based-Feature-Envy-Detection-Boosted-by-Real-World-Examples)、[作者代码](https://github.com/lyoubo/feTruth)与[论文归档](https://doi.org/10.5281/zenodo.8267775)。[CCF 目录归档](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/references/ccf-seventh.pdf)第 27、41 页分别列 FSE、CAV 为 A 类；论文等级只用于准入，不替代效果验证。

feTruth 源码固定为 `b4f8d5c4fbf655e5615246f2849ccc3825db8e7d`，论文归档 v1.0.0 固定为 `a89644539cd639ee7adc21543aae20f8895c47d6`。完整版本记录见[选型清单归档](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/baselines/academic-review-manifest.json)。

## 2. feTruth：Java 方法职责与移动建议

输入 Java 工程后，作者 JAR 提取候选方法、候选类及结构指标；预处理名称、距离和耦合特征，使用 Word2Vec 与预训练模型判断 Feature Envy。默认阈值 0.95；每个被报告的方法选择得分最高的候选类。模型无需按业务重写规则，但建议必须复核。

### 2.1 实际项目输入和输出

本项目 Java 示例提取 1 个候选方法、2 个候选关系，输出 1 条建议：`OrderService.createOrder` 移到 `PaymentService`。这是方法职责候选，不是业务错误证明，也没有自动修改源码。

![图 1 feTruth：源码、提取与方法移动建议](https://raw.githubusercontent.com/KuaiSuMi/csdpg-file/a60c36726c5fcd872b817f08e815d24816ade0e4/docs/assets/baseline-outputs/fetruth.png)

原始文件：[特征 JSON](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/results/fetruth-project/20261111-141246-910830/features.json)、[建议 TSV](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/results/fetruth-project/20261111-141246-910830/recommendations.tsv)、[运行汇总](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/results/fetruth-project/20261111-141246-910830/summary.json)。图中的 `target_*_list` 按 `target_class_list` 顺序一一对应；不能把不同候选类的特征拼在一起。

### 2.2 论文重放与新源码分析

| 流程 | 输入和模型 | 结果 | 含义 |
| --- | --- | --- | --- |
| 论文归档重放 | v1.0.0 归档特征与模型 | 16 条，16/16 与归档结果一致 | 复现该归档输入的输出 |
| jsoup 新源码 | 重新提取 204 个方法、300 个候选关系；源码工作流模型 | 180 条候选 | 新源码功能运行，不是确认了 180 个缺陷 |
| 项目 Java 示例 | 1 个方法、2 个候选关系 | 1 条候选 | 源码入口能用于另一项目样例 |

![图 2 feTruth：两种工作流与输出对照](https://raw.githubusercontent.com/KuaiSuMi/csdpg-file/a60c36726c5fcd872b817f08e815d24816ade0e4/docs/assets/baseline-outputs/fetruth-workflows.png)

[论文对照](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/results/fetruth-paper/comparison.json)、[论文原生输出](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/results/fetruth-paper/jsoup.txt)、[新源码执行记录](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/results/fetruth/execution.json)、[新源码原生输出](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/results/fetruth/jsoup.txt)。[模型差异诊断](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/results/fetruth-model-diagnostics.json)记录了源码工作流模型与归档的差异，不能混用模型与输入后仍声称精确复现论文。

### 2.3 全部输入输出类型

![图 3 feTruth：输入输出清单](https://raw.githubusercontent.com/KuaiSuMi/csdpg-file/a60c36726c5fcd872b817f08e815d24816ade0e4/docs/assets/baseline-outputs/fetruth-io.png)

原生最终文件只有重构类型、源方法、目标类三列；概率分数属于模型内部计算，没有写入该文件。零建议、无候选、提取失败和模型加载失败必须分别说明。完整字段和安装条件见[输入输出清单](#inputs-outputs)。

## 3. Infer/Pulse：源码错误与路径证据

Infer 捕获正常编译过程形成中间表示；Pulse 跟踪程序路径中的值和内存状态，使用函数摘要进行跨函数分析。本轮固定 1.3.0 并只启用 Pulse，不把其他 Infer 检查器的能力算入本基线。

### 3.1 空指针输入与修改对照

受控 Java 样例将 `null` 传给调用 `length()` 的方法。原生报告给出 `NULLPTR_DEREFERENCE`、文件行号和四步错误路径。增加空值处理后，同一分析器输出空数组；前后均捕获 1 个 Java 文件。

![图 4 Infer/Pulse：源码与原生错误路径](https://raw.githubusercontent.com/KuaiSuMi/csdpg-file/a60c36726c5fcd872b817f08e815d24816ade0e4/docs/assets/baseline-outputs/infer.png)

原始文件：[修改前 JSON](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/results/academic-20261113/infer/before/infer-out/report.json)、[修改后 JSON](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/results/academic-20261113/infer/after/infer-out/report.json)、[修改前源码](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/baselines/infer/fixtures/before/NullExample.java)、[修改后源码](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/baselines/infer/fixtures/after/NullExample.java)。

### 3.2 跨项目输入与报告内容

jsoup、Commons CLI、本项目 Java 示例分别捕获 75、23、4 个 Java 文件，报告 6、0、0 条。jsoup 的 6 条均为 `PULSE_RESOURCE_LEAK`，尚未逐条确认，其中涉及 StringReader 等对象，需要核对资源语义。

![图 5 Infer/Pulse：项目结果与报告字段](https://raw.githubusercontent.com/KuaiSuMi/csdpg-file/a60c36726c5fcd872b817f08e815d24816ade0e4/docs/assets/baseline-outputs/infer-projects.png)

[运行汇总](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/results/academic-20261113/infer/summary.json)、[jsoup 原生文本](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/results/academic-20261113/infer/jsoup/infer-out/report.txt)。无告警只表示在本次捕获与分析范围内未报告，编译失败、零捕获和不支持语言均不能算作通过。

## 4. AppCAT：迁移问题、依赖与报告

### 4.1 Java 源码与规则命中

同一 Maven Java 工程将本地文件日志改为标准输出。扫描均以 `azure-aks` 为迁移目标，使用内置规则；不需要 Azure 资源。`local-storage-00001` 从 1 次命中变为 0 次，总命中次数 7→5。

![图 6 AppCAT：源码和迁移规则报告](https://raw.githubusercontent.com/KuaiSuMi/csdpg-file/a60c36726c5fcd872b817f08e815d24816ade0e4/docs/assets/baseline-outputs/appcat.png)

### 4.2 规则详情、依赖和 YAML

原生报告包含问题解释、建议、严重程度、工作量估计、源码位置和片段。`full` 模式额外解析依赖；现有实验另存 JSON、YAML 和静态 HTML。业务检查是本地对照测试，不是 AppCAT 自带的业务判定。

![图 7 AppCAT：规则、依赖与业务辅助证据](https://raw.githubusercontent.com/KuaiSuMi/csdpg-file/a60c36726c5fcd872b817f08e815d24816ade0e4/docs/assets/baseline-outputs/appcat-details.png)

原始文件：[修改前 JSON](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/results/output-audit/20261111/appcat/before/report.json)、[修改后 JSON](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/results/output-audit/20261111/appcat/after/report.json)、[依赖 JSON](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/results/output-audit/20261111/appcat-full/dependencies.json)、[YAML](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/results/output-audit/20261111/appcat-yaml/report.yaml)。

### 4.3 图 8：直观的前后对照

图 8 与其他截图使用同一模板，展示实际问题和前后变化。去重迁移问题 4→2；前后另有各 2 类技术发现信息，所以原生 `totalIssues` 为 6→4。工作量是工具估计，不是实际工时。原生 HTML 仍可单独查阅，[原生 UI 截图](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/docs/assets/baseline-outputs/appcat-native.png)保留原貌，不混入统一排版图集。

![图 8 AppCAT：中文问题与前后对照](https://raw.githubusercontent.com/KuaiSuMi/csdpg-file/a60c36726c5fcd872b817f08e815d24816ade0e4/docs/assets/baseline-outputs/appcat-html.png)

## 5. NeuVector：实际部署与运行风险

### 5.1 运行身份与特权

配置 `runAsUser` 从 0 改为 1000，实际容器 UID 同步改变，API `run_as_root` 由 true 变为 false；两次 HTTP 均返回 `200 + maturity-ok`。Deployment YAML 是建立实验对象的配置，平台真正检查的是实际容器。

![图 9 NeuVector：root 风险与运行身份](https://raw.githubusercontent.com/KuaiSuMi/csdpg-file/a60c36726c5fcd872b817f08e815d24816ade0e4/docs/assets/baseline-outputs/neuvector.png)

三组权限实验分别为普通 root、特权 root、非 root。首次特权测试平台字段与配置不一致，重新部署后才一致；两次记录保留，不删除失败证据。

![图 10 NeuVector：三组权限与首次不一致记录](https://raw.githubusercontent.com/KuaiSuMi/csdpg-file/a60c36726c5fcd872b817f08e815d24816ade0e4/docs/assets/baseline-outputs/neuvector-privileged.png)

### 5.2 进程、资源、网络和风险分项

按真实容器 ID 读取进程、历史、资源统计、配置和扫描状态。该阶段的全局风险分数为 48，统计整个集群；当时尚未启用漏洞扫描，所以空列表和空扫描时间不代表无漏洞。

![图 11 NeuVector：运行数据与扫描前状态](https://raw.githubusercontent.com/KuaiSuMi/csdpg-file/a60c36726c5fcd872b817f08e815d24816ade0e4/docs/assets/baseline-outputs/neuvector-runtime.png)

### 5.3 合规与漏洞

节点 CIS 1.8.0 报告共 130 项：52 PASS、38 WARN、40 MANUAL，每项保留编号、说明及修复建议。

![图 12 NeuVector：CIS 合规检查](https://raw.githubusercontent.com/KuaiSuMi/csdpg-file/a60c36726c5fcd872b817f08e815d24816ade0e4/docs/assets/baseline-outputs/neuvector-cis.png)

后续对 `node:22-alpine` 容器扫描，返回 27 条漏洞（12 High、15 Medium）及 209 个软件包。报告包含当前版本、修复版本和 CVSS；这些是该次漏洞库和镜像版本下的结果。

![图 13 NeuVector：CVE 与软件包清单](https://raw.githubusercontent.com/KuaiSuMi/csdpg-file/a60c36726c5fcd872b817f08e815d24816ade0e4/docs/assets/baseline-outputs/neuvector-cve.png)

原始目录：[权限与运行数据](https://github.com/KuaiSuMi/csdpg-file/tree/a60c36726c5fcd872b817f08e815d24816ade0e4/results/output-audit/20261111/neuvector-complete)、[CIS 与漏洞](https://github.com/KuaiSuMi/csdpg-file/tree/a60c36726c5fcd872b817f08e815d24816ade0e4/results/output-audit/20261111/neuvector-scanning)。

## 6. 其余完整接口清单

以下是接口清单，不是额外执行成功的实验截图。Infer 的官方目录还包括其他语言相关问题类型，AppCAT 的本机模式包括 `issue-only`，NeuVector 还提供镜像仓库、CI、事件和策略接口。

![图 14 Infer/Pulse：输入输出类型及未实测入口](https://raw.githubusercontent.com/KuaiSuMi/csdpg-file/a60c36726c5fcd872b817f08e815d24816ade0e4/docs/assets/baseline-outputs/infer-io.png)

![图 15 AppCAT：输入输出类型及可选模式](https://raw.githubusercontent.com/KuaiSuMi/csdpg-file/a60c36726c5fcd872b817f08e815d24816ade0e4/docs/assets/baseline-outputs/appcat-io.png)

![图 16 NeuVector：输入输出类型与状态](https://raw.githubusercontent.com/KuaiSuMi/csdpg-file/a60c36726c5fcd872b817f08e815d24816ade0e4/docs/assets/baseline-outputs/neuvector-io.png)

各项字段、完整枚举、结果状态和正式资料见[输入输出清单](#inputs-outputs)。

## 7. 复现与接入

换项目时，Infer 更换正常构建命令并确保重新捕获源码；feTruth 先运行作者 JAR 提取特征，再以固定模型推理；AppCAT 更换应用路径和迁移目标；NeuVector 接入实际平台并按真实容器 ID 查询。具体输入、输出和执行状态见第 8 节。

本报告复用已核验的原生实验，没有重新训练或重新扫描业务项目。为使当前仓库只保留这一份报告，截图、原始结果和固定版本接口目录均引用清理前提交的不可变链接，在线查看需联网。它们用于查证当次实验，不代表新的执行结果。

现有图谱读取器分别支持四项工具的证据导入；本次未重新合并执行新的“四项联合前后实验”，不沿用旧 GLITCH/Kivi/Reynard 图谱数字冒充当前组合。建议、告警、合规状态和风险指标保留原始含义，不相加成统一分数。

<a id="inputs-outputs"></a>

## 8. 四项基线完整输入输出清单

更新：2026-11-13。对应当前固定版本：Infer 1.3.0 / Pulse、feTruth 固定源码与论文归档、AppCAT 7.7.0.11、NeuVector 5.6.4。

这里的“完整”覆盖分析入口、必需与可选输入、处理中间文件、结果载体、字段类别和所有需区分的执行状态；具体问题类型、可选参数及 API 全字段通过固定版本目录链接查询。不同语言、选项与平台产生的字段可能不同，未执行的能力不会写成已验证。没有将任意输入值、未来版本或所有管理功能都视作已复现。

### 8.1. Infer/Pulse

#### 输入方式

| 入口 | 必需输入 | 可选输入/配置 | 当前状态 |
| --- | --- | --- | --- |
| 构建捕获 `infer run --pulse-only -- <build>` | 支持语言的源码、正常编译环境、构建命令、依赖 | include/classpath、编译选项、输出目录、作业数 | Java/javac 已实测 |
| `infer capture --compilation-database ...` | C/C++ 编译数据库、对应源码与头文件 | 多个数据库、经过 shell 转义的数据库 | 1.3.0 CLI 已核对，未执行 C/C++ |
| 分阶段 `capture → analyze → report` | 同一版本的捕获结果和分析配置 | 结果目录、文件范围 | 接口已核对 |
| 重读、合并、比较已有结果 | JSON 结果、前后版本报告或多个结果目录 | 报告过滤、`--merge-report`、`--report-current/previous` | 接口已核对，未把它们写成新增扫描 |
| 可选高级配置 | `.inferconfig`、环境变量、模型/污点配置、抑制选项 | 官方支持但非本轮默认基线输入 | 本轮不编写定制业务规则 |

[官方 Pulse 1.3.0](https://fbinfer.com/docs/checker-pulse/)列 Java、C/C++/ObjC、Hack 为支持，Erlang/Rust 为实验性，Python、C#/.Net、Swift 不支持。支持语言不等于本地已经验证该语言；当前实验仅 Java。

#### 输出与字段

| 载体 | 内容 | 原生或本地 | 状态 |
| --- | --- | --- | --- |
| `infer-out/report.json` | 逐项诊断、类型、严重程度、文件与过程位置、说明、调用路径、标识及可选扩展 | 原生 | 已保存 |
| `infer-out/report.txt`、stdout | 易读问题说明与路径摘要；控制台可限制显示数量 | 原生 | 已保存；完整条数以 JSON 为准 |
| `infer explore --html` | HTML 问题报告 | 原生可选 | CLI 支持，未生成本轮原生 HTML |
| `infer report --issues-tests` | 可选择字段的测试用文本 | 原生可选 | CLI 支持，未执行 |
| `infer reportdiff` | introduced / fixed / preexisting 等差异集合 | 原生可选 | CLI 支持，未执行 |
| 合并报告 | 多个结果目录的 JSON 合并去重 | 原生可选 | CLI 支持，未执行 |
| `capture.db`、`results.db` | 捕获的中间表示、分析摘要与内部数据 | 原生内部文件 | 已保存；不是直接质量分数 |
| `logs`、`stats/`、`tmp/`、其他分析器报告文件 | 分析日志、统计、临时产物；cost/config 文件不代表启用了相应分析器 | 原生执行材料 | 已保存 |
| `summary.json`、`process.json`、`sources.txt`、stdout/stderr 文件 | 命令、退出码、文件覆盖、耗时、计数 | 本地封装 | 已保存，不能标为原生诊断格式 |

本轮诊断的顶层字段包括：`bug_type`、`qualifier`、`severity`、`category`、`line`、`column`、`procedure`、`procedure_start_line`、`file`、`bug_trace`、`bug_trace_length`、`bug_trace_max_depth`、`key`、`node_key`、`hash`、`bug_type_hum`、`extras`。路径项包含 `level`、`filename`、`line_number`、`column_number`、`description`。其他输出可含 `suggestion`、抑制原因等可选字段，不能假设每条都存在。

完整问题类型见[86 项 Pulse 类型目录](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/references/authority/infer-pulse-1.3.0-issue-types.json)；这里只将 `NULLPTR_DEREFERENCE` 与 `PULSE_RESOURCE_LEAK` 标为本地已出现。其余类型受语言、开关、模型和分析范围限制，尤其 `_LATENT` 不能一概视为默认会报告的确认错误。

完整固定版本命令帮助：[capture](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/references/authority/infer-1.3.0/capture-help.txt)、[report](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/references/authority/infer-1.3.0/report-help.txt)、[reportdiff](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/references/authority/infer-1.3.0/reportdiff-help.txt)、[explore](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/references/authority/infer-1.3.0/explore-help.txt)。它们来自本机固定镜像的帮助输出，不是臆测参数。

#### 状态判定

- 有告警：记录原生项和路径，不自动计为真缺陷。
- 零告警：仅在构建成功、捕获量合理、分析完成后写“已覆盖，本次未报告”。
- 零捕获：可能没有触发重新编译；不是通过。
- 构建/依赖错误、分析崩溃或超时：记失败或未完成，不产生合格结论。
- 不支持的语言或没有捕获到的文件：记未覆盖。

### 8.2. feTruth

#### 输入方式

| 入口 | 输入 | 说明 |
| --- | --- | --- |
| 新 Java 项目 | Java 工程目录，`testingDataGeneration.jar`，JDK | 先执行 JAR，再运行 `feTruth.py -a <目录>`；当前源码中自动调用 JAR 的代码被注释，不能省略提取步骤 |
| 预训练推理 | `testing_data/<项目>.json`、`feTruth.h5`、Word2Vec 及其两个数组文件 | 固定 Python 3.6/Keras 环境；模型文件不是用户业务规则 |
| 论文归档重放 | 固定 v1.0.0 的特征/预处理文件和配套模型 | `evaluate.py jsoup`；与新源码流程分开 |
| 重新训练（可选研究流程） | 作者有标签正负样本、名称/耦合特征、Word2Vec、训练参数 | 作者提供 `train.py`；本轮未训练，不是换项目的必需操作 |
| 帮助/参数错误 | `-h` 等帮助参数、无参数或错误路径 | 原程序会打印提示；部分错误路径直接退出，不能只靠退出码认定成功 |

普通推理不接受 Kubernetes 清单、运行指标或其他语言源码作为等价输入，也不直接把一个业务断言文件当输入。[作者仓库与说明](https://github.com/lyoubo/feTruth)。

#### 全部特征字段与中间文件

源码提取结果根节点为 `RECORDS` 数组。本地记录包含：`id`、`project_name`、`source_class_name`、`method_name`、`method_signature`、`source_dist`、`source_cbmc`、`source_mcmc`、`target_class_list`、`target_dist_list`、`target_cbmc_list`、`target_mcmc_list`。

| 字段组 | 含义 |
| --- | --- |
| `source_class_name`、`method_signature` | 原类及完整方法签名；定位候选，不是源码行号 |
| `source_dist` / `target_dist_list` | 方法与原类/候选目标类的距离 |
| `*_cbmc`、`*_mcmc` | 作者定义的结构耦合与消息耦合指标 |
| `target_*_list` | 候选目标序列，按相同位置对齐，不能分别排序后组合 |

预处理还产生 `test_name.txt`、`test_dist.txt`、`test_cbmc.txt`、`test_mcmc.txt`。模型将名称向量和结构指标一起输入，默认阈值 0.95，选择得分最高的可接受目标。中间预测分数没有作为原生结果列导出。

#### 输出类型

| 输出 | 内容 | 状态 |
| --- | --- | --- |
| 原生 stdout、`output/<项目>.txt` | 三列：`Refactoring Type`、`Source Method`、`Target Class`；当前类型为 `Move Method` | 已保存 |
| 论文归档原生文件 | `jsoup(feTruth).txt` 等归档流程结果 | 已重放并对照 16/16 |
| 本地 `recommendations.tsv` | 原生建议文件的归档副本 | 已保存 |
| `features.json` / `jsoup-features.json` | 提取的候选方法与目标特征 | 已保存 |
| 本地 `summary.json` / `execution.json` | 候选数、关系数、建议数、版本、阈值、模型/特征校验值、退出状态 | 已保存 |
| 提取/推理日志、归档对比和模型诊断 | 排查提取失败、模型加载和流程差异 | 已保存 |
| 训练模型与训练日志 | 可选重新训练流程的产物 | 未执行，不计入本次复现 |

**没有原生自动补丁、修复后源码、业务测试结论、源码行号或完整成熟度评分。** 移动建议需人工或后续 Agent 验证。零建议不等于不存在设计问题；无候选、提取失败、特征错位、模型不兼容必须单独标记。

### 8.3. AppCAT 7.7.0.11

#### 输入方式与配置

| 输入 | 可选范围 | 本轮情况 |
| --- | --- | --- |
| `--input` | 一个或多个应用源码目录/二进制文件 | 已测 Java 源码，未测二进制及批量 |
| `--output` | 新报告目录；`--overwrite` 为可选覆盖 | 已保存独立前后目录 |
| `--mode` | **issue-only / source-only / full** | 本机 CLI 均声明；已测 source-only/full |
| 技术与目标 | `--source`、`--target`、`--capability`、`--os` | AKS 目标实测；完整枚举见下 |
| 范围与依赖 | 包过滤、已知库开关、Maven settings、代理 | full 模式已验证一个新增依赖 |
| 规则 | 默认规则开关、标签过滤、可选 `--rules` 文件/目录 | 本轮使用默认规则，不编写业务规则 |
| 输出选择 | JSON/YAML、静态报告开关、代码上下文行数、命中筛选、bulk | JSON/YAML/HTML 已验证 |
| 辅助命令 | dry-run、version、规则格式 transform | 不等于已经执行应用扫描 |

本地 CLI 的默认 `--output-format` 为 JSON，并包含 issue-only；[在线 7.x 文档](https://learn.microsoft.com/en-us/azure/migrate/appcat/appcat-7-cli-guide?view=migrate)部分条目不同，因此本报告以[固定 7.7.0.11 帮助与全部枚举](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/references/authority/appcat-7.7.0.11-cli.json)为准。

目标为 `azure-aks`、`azure-appservice`、`azure-container-apps`；能力为 `containerization`、`jakarta-ee`、`openjdk11`、`openjdk17`、`openjdk21`、`openjdk25`；OS 为 `linux`、`windows`。全部 source 标识保存于上述 JSON 的 `--list-sources`，不同标识表示检测/迁移技术，不表示每项都已实际验证。

#### 输出类型与字段

| 文件/区域 | 内容 |
| --- | --- |
| `report.json` 或 `report.yaml` | `version`、`producer`、`metadata`、`summary`、`projects`、`rules` |
| `metadata` | 起止时间、状态、隐私模式、目标 ID/显示名、能力与 OS |
| `summary` | 项目数、总问题、总命中、工作量、严重程度和分类统计 |
| `projects[].properties` | 应用名、JDK、语言、构建工具、框架等发现信息 |
| `projects[].incidents[]` | ruleId、incidentId、位置类型/路径、行列、代码片段、目标严重度/工作量、标签；项目级项可无文件位置 |
| `rules` | 规则 ID、标题、说明、建议、严重程度、工作量及相关元信息 |
| `dependencies.json` | 依模式生成依赖名称、版本、类型、标签等；不应在 source-only 结果中虚构完整依赖 |
| `static-report/` | 原生 HTML 报告及资源，除非显式跳过 |
| 日志与临时材料 | 执行、分析错误与环境诊断；`--no-cleanup` 可保留临时资源 |
| 本地辅助文件 | 前后汇总、业务 stdout/订单审计文件、业务检查 JSON；不是 AppCAT 原生输出 |

原生等级可能包括 mandatory、potential、optional 和 information。information 为技术发现；`totalIssues`、命中次数、去重迁移规则不能混用。报告完成且无迁移问题、仅有信息项、执行失败/不完整、依赖解析不全应分别说明。`effort` 是估计量，不是工时，也不是缺陷数量。

### 8.4. NeuVector 5.6.4

#### 输入对象

| 输入入口 | 必需材料 | 当前状态 |
| --- | --- | --- |
| 部署/容器检查 | 安装好的平台、访问地址、认证、实际节点/Pod/容器 ID、作用域 | 权限风险已实测 |
| 运行监测 | 实际进程、资源、网络活动、策略模式 | 数据读取已实测；事件拦截未验证 |
| 节点合规 | 节点 ID、可用的合规扫描组件 | CIS 已实测 |
| 镜像漏洞 | 运行容器/镜像身份、Scanner、漏洞库 | 容器扫描已实测 |
| 仓库与 CI 扫描 | 镜像仓库/标签/凭据或 CI 中的镜像 | 官方接口支持，未实测 |
| 策略/准入/响应 | 内置或配置的安全策略、准入规则、响应规则 | 可选能力，未作为本轮业务正确性判定 |

工具从实际环境采集，不是只读取静态 Deployment YAML。kubeconfig、密码文件、端口转发用于本地实验接入，真实凭据不进入报告截图。

#### 所有结果类别

| 类别 | 原生输出内容 | 当前证据 |
| --- | --- | --- |
| 对象与身份 | 域/命名空间、节点/Pod/容器/镜像、running、run_as_root、privileged、策略/配置模式 | 已保存 workload、配置等 JSON |
| 进程及历史 | 名称、用户、root、状态、动作等 | 已保存 process/process_history |
| 资源及网络 | CPU/内存、收发量、连接与资源统计；字段依时间跨度和接口变化 | 已保存 stats；不声称网络策略已验收 |
| 集群风险 | security_risk_score 及权限、暴露、服务模式等分项 | 已保存，属于全局指标 |
| 合规 | cis_version、run_at、items；编号、level、automated、description、remediation | 已有 PASS/WARN/MANUAL 全部三类示例 |
| 漏洞 | 扫描状态/时间/引擎版本、各严重度数量、CVE、软件包/当前版本/修复版本、CVSS、说明 | 已有 High/Medium；其他严重度未因此算作实测 |
| 软件包 | modules 数组及包信息，可能关联漏洞 | 已保存 209 项 |
| 安全/流量事件与响应 | 告警、策略命中、连接和响应动作，依启用功能与权限 | 官方支持，未复现完整事件/拦截流程 |
| 展示与集成 | Console、报告、REST JSON，通知/外部集成依配置开启 | 本轮以 API 原始文件为证据 |
| 执行状态 | HTTP 状态、平台错误、扫描状态、空/非空结果 | 必须与结果一起保存 |

固定版完整 API 参数、响应对象和可选字段见[官方 v5.6.4 API 快照](https://github.com/KuaiSuMi/csdpg-file/blob/a60c36726c5fcd872b817f08e815d24816ade0e4/references/authority/neuvector-5.6.4-api.yaml)，来源为[对应版本源码](https://github.com/neuvector/neuvector/blob/v5.6.4/controller/api/apis.yaml)。[官方说明](https://open-docs.neuvector.com/automation/automation/)明确建议按发行版选 API schema，避免拿主分支未发布能力描述 5.6.4。

本轮常用 API 是 workload/detail、process、process_history、stats、config、score/metrics、bench/host/.../kubernetes、host/.../compliance、scan/workload。`pods.json`、`deployment.json`、`input.yaml`、`business.json`、进程 UID 与 HTTP 检查是本地实验辅助材料，不能都称为 NeuVector 原生输出。

成功且有结果、成功但为空、未扫描、扫描失败、鉴权失败、对象不存在/标识不匹配均需分开。权限字段与实际配置不一致时先记录不一致并核对容器身份，不能直接写通过。

### 8.5. 共同解释规则

| 状态 | 可以写 | 不能写 |
| --- | --- | --- |
| 有告警/建议 | 原生输出了多少条，覆盖了哪些对象 | 已证实同样数量的缺陷 |
| 正常结束且零项 | 在明确覆盖范围内未报告 | 系统完全成熟/安全 |
| 无数据/未采集/未扫描 | 此项未得到有效证据 | 检查通过 |
| 进程/API 失败 | 执行失败或未完成，附原因 | 零问题 |
| 官方支持但未运行 | 文档/接口已核对，效果未验证 | 已复现 |
| 前后项减少 | 本次未再命中/原生状态改变 | 自动证明修复正确 |

全部实测图片已嵌入本报告前文。图 3、14、15、16 是接口清单，其他图基于既有实测数据；二者在图中明确标识。
