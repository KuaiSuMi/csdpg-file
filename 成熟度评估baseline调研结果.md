# 成熟度评估 baseline 调研结果

更新：2026-11-11

## 1 方案选择

选用 feTruth、Kivi、Reynard、Microsoft AppCAT for Java 和 SUSE Security／NeuVector。源码评估采用 feTruth、AppCAT；实际部署评估采用 NeuVector；Kivi 和 Reynard 分别检查配置模型与故障下的业务行为。

| 方案 | 输入 | 输出内容 | 核心机制 | 选择理由 |
| --- | --- | --- | --- | --- |
| feTruth | Java 源码 | 方法移动建议（TSV）；候选方法、目标类、耦合特征和覆盖统计（JSON） | 名称词向量与结构耦合特征识别 Feature Envy 异味 | 将类依赖落实到方法职责和移动建议 |
| Kivi | Kubernetes 配置模型及待验证性质 | 性质结果、反例路径、搜索状态数和配置差异（JSON、日志） | Promela 建模，SPIN 搜索反例 | 检查调度、扩容约束的组合问题 |
| Reynard | 微服务、请求、故障设置和业务断言 | 实际故障、调用轨迹、业务响应、断言结果（JSON）；测试汇总（JUnit XML） | 代理注入故障，检查响应；SER 减少重复探索 | 验证服务降级和修改后的业务行为 |
| Microsoft AppCAT for Java | Java 源码及 Maven 工程描述 | 规则 ID、源码位置、严重程度、修改建议、工作量和命中汇总（JSON） | 按目标云平台规则分析源码与技术使用 | 提供工业云就绪度规则，可在本地完成前后对照 |
| SUSE Security／NeuVector | 实际 Kubernetes 工作负载与容器状态 | 容器及 Pod 定位、运行身份风险、运行状态、全局风险分数（JSON） | Enforcer 采集，Controller 汇总，API 输出 | 为源码和模型分析补充真实部署证据 |

## 2 来源与运行环境

| 方案 | 权威来源 |
| --- | --- |
| feTruth | ESEC/FSE 2023；作者仓库 lyoubo/feTruth，1 star |
| Kivi | USENIX ATC 2024；作者仓库 bingzheliu/Kivi，23 stars |
| Reynard | ICSE 2026 Research Track；作者仓库 reynard-testing/reynard，4 stars |
| AppCAT | 微软 Azure Migrate 官方 Java 云就绪度评估工具，免费使用 |
| NeuVector | SUSE 容器安全产品；本次采用免费的 NeuVector 开源发行版 |

Star 数采集于 2026-10-29；商业产品说明依据 Microsoft Learn 和 SUSE 官方文档。

项目部署：在 Python 虚拟环境中安装 maturity-evaluate 及依赖，准备 JDK 17、Maven 和 Docker。部署侧准备 Kubernetes 集群和 Helm，本地实验使用 kind。各工具按下节安装，结果按类、服务和 Pod 关联到项目图谱。

## 3 各方案复现与输出

配图展示实际源码、配置、执行命令和输出文本节选，黄色标出关键行。命令中的尖括号为路径或命名空间占位符。

### 3.1 feTruth

1. 从作者仓库获取源码、模型和词向量文件。
2. 在 Python 3.6 容器中安装 TensorFlow 2.4.0、Keras 2.4.3。
3. 用 `testingDataGeneration.jar` 从 Java 工程提取特征，再在容器内执行 `python feTruth.py -a <源码目录>`。

输出为 TSV 建议清单和 JSON 特征、统计。

| 输出 | 字段 | 含义 |
| --- | --- | --- |
| 方法移动建议 | `Refactoring Type`、`Source Method`、`Target Class` | 重构类型、完整源方法签名、建议迁入的类 |
| 候选特征 | `source_class_name`、`method_signature`、`target_class_list` 及耦合特征 | 参与推理的方法、候选类及结构关系 |
| 覆盖统计 | `candidate_methods`、`candidate_pairs`、`recommendations` | 候选方法数、方法与目标类组合数、建议数 |

样例得到 1 条 `Move Method` 建议：将 `OrderService.createOrder` 移入 `PaymentService`，涉及 1 个候选方法、2 个候选目标类。

![feTruth：Java 源码、模型推理和方法移动建议](assets/baseline-outputs/fetruth.png)

### 3.2 Kivi

1. 在 Linux 容器中准备 Kivi、SPIN 和 GCC。
2. 输入节点、Pod、扩容策略和调度约束，设置待验证性质，由 Kivi 生成 Promela 模型。
3. 用 SPIN 和 GCC 编译、运行验证程序；修改配置后重复验证，比较错误数和反例。

| 输出 | 字段或记录 | 含义 |
| --- | --- | --- |
| 检查对象与性质 | 资源身份、`intent` | 定位部署模型及待验证性质；本例为 Pod 始终可调度 |
| 性质结果 | `status`、`spin_errors` | `fail` 表示发现反例；`pass` 表示模型搜索完成且无反例 |
| 搜索过程 | `stored_states`、反例记录 | 保存的状态数，以及触发失败的状态和动作顺序 |
| 输入与修改 | 节点及 Pod 分布、调度约束、配置补丁 | 复查约束变化如何影响验证结果 |

固定拓扑模型有三个节点，分属两个 zone。Pod 从 5 个扩到 6 个时，节点和 zone 的 `maxSkew=1` 无法同时满足。将 zone 的 `maxSkew` 改为 2 后，节点可分布为 2、2、2，两个 zone 分别为 4、2。

| 组别 | 性质结果 | SPIN errors | 搜索状态数 |
| --- | --- | --- | --- |
| 修改前 | fail | 1 | 220 |
| 修改后 | pass | 0 | 1,830 |

![Kivi：部署模型、SPIN 验证和调度结果](assets/baseline-outputs/kivi.png)

### 3.3 Reynard

1. 构建 Reynard 的 Controller、Proxy 镜像和 Java 测试工程；先启动被测服务，再启动故障控制器。
2. 编写请求和业务断言，通过 Maven 执行测试，向下游调用注入故障。
3. 修改服务后，使用相同请求、故障和断言再次测试，比较 JSON 响应记录和 JUnit 结果。

| 输出 | 字段 | 含义 |
| --- | --- | --- |
| 场景与依赖 | `scenario`、`phase`、`service`、`dependency` | 业务场景、实验阶段、入口服务和故障依赖 |
| 调用轨迹 | `trace_id`、`span_id`、调用栈 | 关联入口请求、下游调用和返回结果 |
| 故障设置与执行 | `faultload`、`fault_count`、`injected_fault` | 注入类型、参数、数量及代理实际执行的故障 |
| 业务响应 | `http_status`、`body`、`passed` | 状态码、响应体及业务断言结果 |
| 测试汇总 | `tests`、`failures`、`errors`、`skipped` | 执行数、断言失败数、测试异常数、跳过数 |

场景为 `frontend → recommendations`。健康请求返回 `200 + ["product-1"]`；下游分别返回 HTTP 500、502、503、504 时，入口预期返回 `200 + []`。

| 检查 | 修改前 | 启用空列表降级后 |
| --- | --- | --- |
| 健康请求 | 200，商品列表，断言通过 | 同左 |
| 四种下游错误 | 入口返回 500，4 次断言失败 | 入口返回 200、空列表，4 次断言通过 |
| tests / failures / errors / skipped | 5 / 4 / 0 / 0 | 5 / 0 / 0 / 0 |

四种错误响应对应同一个降级问题。

![Reynard：服务请求、故障注入和业务响应](assets/baseline-outputs/reynard.png)

### 3.4 Microsoft AppCAT for Java

1. 安装官方 CLI 7.7.0.11 和 JDK 17，准备两份含 POM 的 Maven Java 工程。
2. 使用 `appcat analyze`，由 `--input`、`--output` 指定输入和结果位置；固定参数为 `--target azure-aks --mode source-only --disable-telemetry --output-format json`，启用默认规则。
3. 将审计日志从 `FileWriter` 写本地文件改为标准输出，重新扫描，并检查订单结果、非法数量拒绝行为和审计文本。

输出包括原生 JSON 和 HTML 报告。

| 输出 | 字段 | 含义 |
| --- | --- | --- |
| 分析状态与目标 | `metadata.status`、`targetIds` | 分析是否完成及目标平台 |
| 规则说明 | `rules` 中的 `id`、`title`、`description` | 检查项、问题说明和修改建议 |
| 命中位置 | `ruleId`、`incidentId`、`location`、`line`、`snippet` | 规则、命中实例、文件、行号和代码片段 |
| 分类与工作量 | `severity`、`labels`、`effort` | 必须、可选、潜在或信息项，以及修改工作量估计 |
| 汇总 | `totalIssues`、`totalIncidents`、`totalEffort` | 规则项数、命中实例数和工作量；规则项包含技术发现信息 |

| 检查 | 修改前 | 修改后 |
| --- | --- | --- |
| 原生报告状态 | Complete | Complete |
| 本地存储规则 `local-storage-00001` 命中 | 1 | 0 |
| 默认编码规则 `utf-8-by-default-00000` 命中 | 1 | 0 |
| totalIssues / totalIncidents | 6 / 7 | 4 / 5 |
| `type=violation` 实例数 | 5 | 3 |
| 订单结果、非法数量两项契约 | 2/2 通过 | 2/2 通过 |
| 审计文本 | `AUDIT ORD-book-2`，写入文件 | 同文，写入标准输出 |

移除同一处 `FileWriter` 后，本地存储和默认编码两项提示同时消失，剩余提示为 Java 版本和 Dockerfile。

![AppCAT：Java 工程、云就绪度扫描和规则命中结果](assets/baseline-outputs/appcat.png)

### 3.5 SUSE Security／NeuVector

1. 准备 kind 集群，通过官方 Helm Chart 部署 Controller、Enforcer、Manager，三者镜像均指定为 5.6.4。实验使用单节点，CVE Scanner、Updater 关闭。
2. 设置本地平台管理员密码，通过端口转发访问 Controller API，并取得登录会话。
3. 在独立命名空间部署 HTTP 服务，用实际 Pod 的 `containerID` 查询工作负载 API；同时读取容器 UID 和 HTTP 响应。
4. 将 `securityContext.runAsUser` 从 0 改为 1000，保持镜像和业务代码一致，重复采集并比较结果。

输出为平台工作负载 JSON、部署快照和业务检查记录。

| 输出 | 字段或记录 | 含义 |
| --- | --- | --- |
| 对象身份 | `id`、`domain`、`pod_name`、Pod UID 标签 | 实际容器、命名空间和 Pod，绑定平台与集群对象 |
| 运行风险 | `run_as_root`、`privileged` | 是否以 root 运行、是否为特权容器 |
| 运行状态 | `running` | 容器是否运行 |
| 业务检查 | 实际 UID、HTTP 状态码与响应体 | 核对进程身份和服务行为 |
| 平台概览 | `security_risk_score` | 全局风险分数，与目标容器字段分别记录 |

| 检查 | 修改前 | 修改后 |
| --- | --- | --- |
| 原生 running | true | true |
| 原生 run_as_root | true | false |
| 实际进程 UID | 0 | 1000 |
| HTTP 状态及响应 | 200，`maturity-ok` | 同左 |
| 原生 privileged | false | false |
| 全局 security_risk_score | 44 | 44 |

![NeuVector：容器部署、运行身份采集和风险字段](assets/baseline-outputs/neuvector.png)

## 4 项目接入与进度

| 来源 | 对象绑定 | 当前进度 |
| --- | --- | --- |
| feTruth | 类节点及方法签名 | 已接入图谱；方法移动建议待验证 |
| Kivi | Deployment 模型及待验证性质 | 已接入图谱并完成固定模型验证；待接入真实集群配置 |
| Reynard | Service、调用关系、故障场景 | 已接入图谱；完成示例服务前后验证 |
| AppCAT | 源码版本、规则 ID、文件及位置 | 已归档原生报告与业务检查；待实现读取器 |
| NeuVector | 集群、命名空间、Pod UID、容器 ID | 已归档运行风险与业务检查；待实现读取器 |

下一步：补齐两项商业结果读取器，接入 otel-demo 做对照实验，再扩展 Python、FaaS 支持。
