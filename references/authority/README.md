# 入选基线的来源证据

更新：2026-11-13。当前学术基线为 Infer/Pulse + feTruth，Kivi、Reynard 为历史材料，商业方案仅保留 Microsoft AppCAT for Java 与 SUSE Security／NeuVector 开源发行版。

- [结构化依据](candidate-evidence.json)：当前两项学术来源、历史学术记录与两项商用复现清单。
- [权威性说明](../../docs/候选基线权威性评估.md)：正式发表、厂商依据、部署条件及成本。
- [商用版本清单](../../baselines/commercial-manifest.json)：AppCAT 固定包与 SHA256；NeuVector 版本、Chart 提交、原生结果入口。
- [主调研文档](../../docs/成熟度评估baseline调研结果.md)：实际输出和适用范围。

仓库元数据旧快照仅是历史来源材料；star 不等于用户数量，母公司规模不等于产品采用量。本轮未重新计算混合权威性分数，也未据旧快照推断当前用户规模。

## 固定版本输入输出依据

- [Infer capture 帮助](infer-1.3.0/capture-help.txt)、[report 帮助](infer-1.3.0/report-help.txt)、[reportdiff 帮助](infer-1.3.0/reportdiff-help.txt)、[explore 帮助](infer-1.3.0/explore-help.txt)：本机 1.3.0 镜像原始帮助输出。
- [Pulse 86 项问题类型](infer-pulse-1.3.0-issue-types.json)：官方 1.3.0 页面目录，非本轮全部实测项。
- [AppCAT CLI 与全部枚举](appcat-7.7.0.11-cli.json)：本机 7.7.0.11，无分析操作。
- [NeuVector 5.6.4 API](neuvector-5.6.4-api.yaml)：固定 tag 的官方 OpenAPI schema，含参数及完整响应定义。
- [四项输入输出解释](../../docs/基线输入输出清单.md)。
