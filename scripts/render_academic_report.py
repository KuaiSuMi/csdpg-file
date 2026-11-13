"""Render a readable report from saved native outputs; this is not a tool's native UI."""
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/academic-20261113"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def code(text):
    return "<pre>" + escape(text) + "</pre>"


def table(headers, rows):
    return "<table><thead><tr>" + "".join(f"<th>{escape(str(x))}</th>" for x in headers) + "</tr></thead><tbody>" + "".join(
        "<tr>" + "".join(f"<td>{escape(str(x))}</td>" for x in row) + "</tr>" for row in rows) + "</tbody></table>"


def section(identity, label, title, intro, body, note):
    return f'<section id="{identity}"><div class="eyebrow">{label} · 固定版本功能复现</div><h1>{title}</h1><p>{intro}</p>{body}<footer>{note}<br>来源：本轮原生报告与运行记录的排版汇总，非工具原生 UI · 2026-11-13</footer></section>'


def paired(tool, name):
    cards = []
    for phase, title in [("before", "修改前"), ("after", "修改后")]:
        summary = read(OUT / tool / phase / "summary.json")
        text = (ROOT / "baselines" / tool / "fixtures" / phase / name).read_text(encoding="utf-8")
        cards.append(f'<article><h2>{title} <strong>{summary["findings"]} 条</strong></h2>{code(text)}</article>')
    return '<div class="pair">' + "".join(cards) + '</div>'


def main():
    sections = []
    native = (OUT / "glitch/before/findings.csv").read_text(encoding="utf-8")
    rows = [row.split(",", 3)[1:] for row in native.splitlines()]
    sections.append(section("glitch", "GLITCH · ASE 2022 · CCF-A", "同一套内置规则，修改前后 6 → 0",
        "输入 Ansible 任务文件。检测器、默认词表和 security 检查集合保持不变。",
        paired("glitch", "tasks.yml") + table(["行号", "原生规则", "触发片段"], rows),
        "6 条为规则命中数，同一字段可能重复命中；未实际执行或部署这个 playbook。"))
    summaries = [read(OUT / "glitch" / name / "summary.json") for name in ("ansible-role-nginx", "ansible-role-redis")]
    native = (OUT / "glitch/ansible-role-nginx/findings.csv").read_text(encoding="utf-8")
    rows = [row.split(",", 3) for row in native.splitlines()[:5]]
    sections.append(section("glitch-projects", "GLITCH · 跨项目运行", "只换项目路径，沿用已有规则",
        "两个公开 Ansible role 均保持原样；不修改作者的检测逻辑，也不增加项目规则。",
        table(["项目", "文件", "代码行", "原生提示"], [(r["project"], r["coverage"]["files"], r["coverage"]["lines"], r["findings"]) for r in summaries]) +
        '<h2>nginx 原生提示示例 · 前 5 / 17 条</h2>' + table(["文件", "行", "规则", "片段"], rows) +
        '<div class="note">17 条中有 16 条来自 8 个服务账号字段的 hard-coded user / secret 提示，另有 1 条 HTTP 提示。普通账号不等于泄露密码，告警需要复核。</div>',
        "固定 v1.0.1；只扫描支持的 Ansible 模块结构，不把 Kubernetes YAML 当成 Ansible。"))
    bug = read(OUT / "infer/before/infer-out/report.json")[0]
    assert bug["bug_type"] == "NULLPTR_DEREFERENCE"
    trace = [(s["line_number"], s["description"]) for s in bug["bug_trace"]]
    sections.append(section("infer", "Infer/Pulse · CAV 2020 · CCF-A", "无需业务断言，自动找出空指针路径",
        "固定 Infer 1.3.0，仅启用 Pulse。传入 null 后调用 length()；增加空值处理后不再报告。",
        paired("infer", "NullExample.java") + '<h2>原生 NULLPTR_DEREFERENCE · 调用路径</h2>' + table(["源码行", "bug_trace 原文"], trace),
        "这里验证的是静态错误报告变化；不是业务测试，也不是 Pulse-X 论文全量实验。"))
    summaries = [read(OUT / "infer" / name / "summary.json") for name in ("jsoup", "commons-cli", "maturity-java")]
    bugs = read(OUT / "infer/jsoup/infer-out/report.json")
    sections.append(section("infer-projects", "Infer/Pulse · 跨项目运行", "两个真实 Java 项目与本项目示例",
        "同一分析器和参数，按项目提供源码及正常编译依赖。所有提交均固定，未为获得结果改写项目源码。",
        table(["项目", "Java 文件", "原生告警", "端到端秒数"], [(r["project"], r["coverage"]["files"], r["findings"], r["seconds"]) for r in summaries]) +
        '<h2>jsoup 的 6 条 PULSE_RESOURCE_LEAK</h2>' + table(["文件", "行", "原生类型"], [(b["file"], b["line"], b["bug_type"]) for b in bugs]) +
        '<div class="note">6 条为工具告警，尚未逐条确认；包含 StringReader 等对象，应结合资源语义检查。Commons CLI 与项目示例的 0 条表示本次未报告问题。</div>',
        "耗时包括 Docker 启动、编译与分析，不是论文性能对比。75 / 23 / 4 个输入文件与捕获覆盖相符。"))
    before = read(OUT / "graph/before.kg.json")
    after = read(OUT / "graph/after.kg.json")
    comparison = read(OUT / "graph/comparison.json")
    assert comparison["counts"] == {"not-observed-after": 7}
    rows = []
    for name, graph in [("修改前", before), ("修改后", after)]:
        rows.append((name, len(graph["nodes"]), len(graph["edges"]), graph["meta"]["baseline_runs"]["baseline-glitch"]["findings"], graph["meta"]["baseline_runs"]["baseline-infer"]["findings"]))
    sections.append(section("academic-graph", "maturity-evaluate · 新基线接入", "原生告警进入图谱，保留证据与边界",
        "GLITCH 文件提示关联 Config，Infer 源码提示关联 Module；以 OBSERVED_BY 连接观察结果。",
        '<div class="flow">原生 CSV / JSON <span>→</span> 状态、覆盖与条数核对 <span>→</span> 对象 + Metric + provenance</div>' +
        table(["阶段", "节点", "边", "GLITCH 告警", "Pulse 告警"], rows) +
        '<h2>修改对照</h2><div class="result">7 项 <strong>修改后未观察到</strong></div>' + code(json.dumps(comparison["counts"], indent=2)) +
        '<div class="note">没有把告警消失标成“证明通过”，没有生成统一成熟度总分。两项工具的分析覆盖记录仍保留。</div>',
        "这张图使用两组受控静态输入；不与旧 Kivi/Reynard 图谱或商用扫描结果混算。"))
    style = """body{margin:0;background:#e8edf1;color:#152c36;font:20px/1.5 'Microsoft YaHei',sans-serif}main{width:1440px;margin:auto}section{box-sizing:border-box;background:#fff;padding:52px 60px;margin:28px 0;overflow:hidden}h1{font-size:38px;line-height:1.25;margin:12px 0 18px;font-weight:700}h2{font-size:24px;margin:24px 0 14px}p{color:#4a606c;margin:0 0 26px}.eyebrow{color:#007d78;font-size:17px;letter-spacing:1px;font-weight:700}.pair{display:grid;grid-template-columns:1fr 1fr;gap:22px}article{background:#f5f8fa;padding:14px 20px;border-top:4px solid #0b8c83}article h2{margin:4px 0 14px}strong{color:#087f74}article strong{float:right}pre{font:17px/1.65 Consolas,'Microsoft YaHei',monospace;white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f5f7;padding:20px;border-radius:6px;margin:0 0 14px}article pre{padding:8px 0;background:transparent;font-size:16px}table{border-collapse:collapse;width:100%;font-size:17px;margin:20px 0;table-layout:auto}td,th{text-align:left;padding:12px 14px;border-bottom:1px solid #dce5e9;overflow-wrap:anywhere}th{background:#eaf5f3;color:#16645f;font-weight:700}td{max-width:650px}tr:nth-child(even){background:#fafcfd}.note{background:#fff6df;border-left:4px solid #dba63a;padding:18px 22px;margin-top:24px;font-size:18px}footer{border-top:1px solid #dce5e9;margin-top:30px;padding-top:18px;color:#627782;font-size:16px}.flow{background:#eaf5f3;padding:28px 24px;border-radius:8px;text-align:center;font-size:23px}.flow span{color:#08897f;margin:0 14px}.result{font-size:32px;margin:22px 0}nav{padding:24px 0 0;display:flex;gap:24px}a{color:#087f74}h3{font-size:24px}"""
    html = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>两项学术基线复现报告</title><style>' + style + '</style><main><nav>' + ''.join(f'<a href="#{x}">{x}</a>' for x in ["glitch", "glitch-projects", "infer", "infer-projects", "academic-graph"]) + '</nav>' + ''.join(sections) + '</main></html>'
    target = OUT / "report.html"
    target.write_text(html, encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
