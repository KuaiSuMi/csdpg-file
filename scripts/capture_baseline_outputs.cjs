// Screenshots of archived source, commands, and native output excerpts.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {pathToFileURL}=require('node:url');
const assert=require('node:assert/strict');
const {chromium}=require('C:/Users/YuRui/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..'),out=path.join(root,'docs/assets/baseline-outputs'),preview=path.join(root,'.runtime/report-screenshots');
fs.mkdirSync(out,{recursive:true});fs.mkdirSync(preview,{recursive:true});
const inputs=new Map();
function read(rel){const b=fs.readFileSync(path.join(root,rel));inputs.set(rel,crypto.createHash('sha256').update(b).digest('hex'));return b.toString('utf8').replace(/^\uFEFF/,'').replace(/\r\n/g,'\n');}
const json=rel=>JSON.parse(read(rel));
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pick=(v,keys)=>Object.fromEntries(keys.map(k=>{if(!(k in v))throw Error('Missing field '+k);return[k,v[k]];}));
const pretty=v=>JSON.stringify(v,null,2);
function excerpt(text,start,end=start){
 const lines=text.split('\n'),a=lines.findIndex(l=>l.includes(start)),b=lines.findIndex((l,i)=>i>=a&&l.includes(end));
 if(a<0||b<a)throw Error('Missing excerpt: '+start+' / '+end);
 const selected=lines.slice(a,b+1),indent=Math.min(...selected.filter(l=>l.trim()).map(l=>l.match(/^\s*/)[0].length));
 return selected.map(l=>l.slice(indent)).join('\n');
}
function code(s,marks=[]){return '<pre>'+String(s).trimEnd().split('\n').map(l=>'<span class="line'+(marks.some(m=>l.includes(m))?' marked':'')+'">'+(esc(l)||' ')+'</span>').join('')+'</pre>';}
const block=(title,text,marks=[])=>'<div class="block"><h3>'+esc(title)+'</h3>'+code(text,marks)+'</div>';
const note=s=>'<p class="note">'+esc(s)+'</p>';
const pair=(left,right)=>'<div class="pair">'+left+right+'</div>';
const omitted='<div class="omitted">…</div>';
const stage=(n,title,body)=>'<section><h2><span>'+n+'</span>'+esc(title)+'</h2>'+body+'</section>';

const css=read('docs/assets/baseline-report.css');
const table=(heads,rows)=>'<table><thead><tr>'+heads.map(x=>'<th>'+esc(x)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+row.map(x=>'<td>'+esc(x)+'</td>').join('')+'</tr>').join('')+'</tbody></table>';
const captions={
 fetruth:{number:1,title:'feTruth：源码与方法移动建议'},
 'fetruth-workflows':{number:2,title:'feTruth：论文重放与新源码分析'},
 infer:{number:4,title:'Infer/Pulse：空指针路径与修改对照'},
 'infer-projects':{number:5,title:'Infer/Pulse：跨项目结果与原生报告'},
 appcat:{number:6,title:'AppCAT：Java 应用迁移问题'},
 'appcat-details':{number:7,title:'AppCAT：规则详情与依赖清单'},
 'appcat-html':{number:8,title:'AppCAT：迁移问题前后对照'},
 neuvector:{number:9,title:'NeuVector：容器 root 风险检查'},
 'neuvector-privileged':{number:10,title:'NeuVector：三组容器权限测试'},
 'neuvector-runtime':{number:11,title:'NeuVector：进程、资源与集群风险'},
 'neuvector-cis':{number:12,title:'NeuVector：节点合规检查'},
 'neuvector-cve':{number:13,title:'NeuVector：漏洞与软件包清单'}
};
function content(d){const c=captions[d.name];return '<header><h1>图 '+c.number+'　'+esc(c.title)+'</h1><div class="date">'+esc(d.date)+'</div></header><p class="result">'+esc(d.result)+'</p>'+stage(1,d.stages?.[0]||'输入：实际分析材料',d.input)+stage(2,d.stages?.[1]||'执行：分析入口与配置',d.run)+stage(3,d.stages?.[2]||'输出：结果、字段与状态',d.output)+'<footer>'+esc(d.kind||'既有实测输入及原生输出的统一重排，非工具原生界面。')+'<br>结果须按覆盖范围解释；建议或告警不等于确认缺陷，未合成成熟度总分。</footer>';}
function html(d){return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>'+esc(captions[d.name].title)+'</title><style>'+css+'</style><main>'+content(d)+'</main></html>';}
const documents=[];
const fb='results/fetruth-project/20261111-141246-910830/';
const fe=json(fb+'summary.json'),fsource=read('baselines/sources/maturity-evaluate/examples/comprehensive_test_repo/java_app/src/main/java/com/example/OrderService.java');
read('scripts/run_fetruth_project.py');
const fsignature=excerpt(fsource,'public String createOrder(');
const fbody=excerpt(fsource,'boolean inStock =','inventoryService.reserveStock');
documents.push({name:'fetruth',title:'feTruth｜Java 源码 → 方法移动建议',date:'2026-11-11',
 input:'<div class="block"><h3>OrderService.java · createOrder 方法节选</h3>'+code(fsignature)+omitted+code(fbody,['inventoryService.checkStock','paymentService.processPayment','inventoryService.reserveStock'])+'</div>',
 run:pair(block('特征提取 · JDK 17','java -Dfile.encoding=UTF-8 -jar testingDataGeneration.jar <Java源码目录>'),block('模型推理 · Python 3.6 容器内','python feTruth.py -a <Java源码目录>')),
 output:block('recommendations.tsv · 原生建议清单',read(fb+'recommendations.tsv'),['Move Method'])+pair(block('features.json · 唯一候选的特征字段',pretty(pick(json(fb+'features.json').RECORDS[0],['source_dist','source_cbmc','source_mcmc','target_class_list','target_dist_list','target_cbmc_list','target_mcmc_list'])),['target_dist_list']),block('summary.json · 适配脚本统计',pretty(pick(fe,['candidate_methods','candidate_pairs','recommendations'])),['"recommendations"'])),
 result:'检查 OrderService.createOrder 后，得到 1 条建议：将该方法移到 PaymentService。'});

const ap='results/output-audit/20261111/appcat/',a0=json(ap+'before/report.json'),a1=json(ap+'after/report.json');
const src0=read('baselines/fixtures/appcat/before/src/main/java/com/example/CloudAudit.java'),src1=read('baselines/fixtures/appcat/after/src/main/java/com/example/CloudAudit.java');
read('scripts/reproduce_appcat.ps1');
const rule='local-storage-00001',incident=a0.projects.flatMap(p=>p.incidents).find(i=>i.ruleId===rule);
const beforeIncident={...pick(incident,['ruleId','location','line']),targets:{'azure-aks':incident.targets['azure-aks']}};
const asummary=r=>pretty({metadata:pick(r.metadata,['status','targetIds']),summary:pick(r.summary,['totalIssues','totalIncidents','totalEffort'])}).replace(/"targetIds": \[\n\s+"azure-aks"\n\s+\]/,'"targetIds": ["azure-aks"]');
const afterRules=a1.projects.flatMap(p=>p.incidents).map(i=>({ruleId:i.ruleId}));
documents.push({name:'appcat',title:'Microsoft AppCAT｜源码 → 云就绪度规则命中',date:'2026-11-11',
 input:pair(block('CloudAudit.java · 修改前，写入本地文件',excerpt(src0,'String order =','return order;'),['FileWriter']),block('CloudAudit.java · 修改后，写入标准输出',excerpt(src1,'String order =','return order;'),['System.out.println'])),
 run:block('同一命令分别扫描修改前、后两份 Maven 工程','appcat.exe analyze --input <源码目录> --output <报告目录> --target azure-aks --mode source-only --disable-telemetry --output-format json'),
 output:pair(block('修改前 · report.json 的 metadata、summary 字段节选',asummary(a0),['totalIssues','totalIncidents']),block('修改后 · report.json 的 metadata、summary 字段节选',asummary(a1),['totalIssues','totalIncidents']))+pair(block('修改前 · projects[].incidents[] 中的本地存储命中',pretty(beforeIncident),['local-storage-00001','mandatory']),block('修改后 · projects[].incidents[] 的全部 ruleId',pretty(afterRules).replace(/\{\n\s+"ruleId": ("[^"]+")\n\s+\}/g,'{ "ruleId": $1 }'),['dockerfile-00000'])),
 result:'文件写日志改为标准输出后，本地存储和默认编码两项提示消失；命中次数从 7 降到 5。'});

const np='results/output-audit/20261111/neuvector-complete/';
const n0=json(np+'before/workload.json').workload,n1=json(np+'after/workload.json').workload;
const b0=json(np+'before/business.json'),b1=json(np+'after/business.json');
const y0=read(np+'before/input.yaml'),y1=read(np+'after/input.yaml'),nrunner=read('scripts/reproduce_neuvector.py');
const nlog=read(np+'commands.log');
const apply=JSON.parse(nlog.split('\n').find(l=>l.startsWith('["kubectl"')&&l.includes('"apply"')));
apply[apply.indexOf('--kubeconfig')+1]='<集群配置>';
apply[apply.indexOf('-n')+1]='<实验命名空间>';
apply[apply.indexOf('-f')+1]='<部署YAML>';
const nyaml=s=>'<div class="block"><h3>Deployment maturity-http · 容器配置节选</h3>'+code(excerpt(s,'- name: http','imagePullPolicy: Never'))+omitted+code(excerpt(s,'securityContext:','privileged:'),['runAsUser:','privileged:'])+'</div>';
const noutput=n=>pretty({workload:pick(n,['pod_name','running','run_as_root','privileged'])});
documents.push({name:'neuvector',title:'NeuVector｜实际容器 → 运行身份风险',date:'2026-11-11',
 input:pair(nyaml(y0).replace('· 容器配置节选','· 修改前'),nyaml(y1).replace('· 容器配置节选','· 修改后')),
 run:block('部署命令 · 两次分别应用修改前、后的 YAML',apply.join(' '))+block('采集脚本 · 按真实 container_id 查询平台 API',excerpt(nrunner,'response = session.get(BASE + "/v1/workload/"')),
 output:pair(block('修改前 · workload.json 字段节选',noutput(n0),['"run_as_root"']),block('修改后 · workload.json 字段节选',noutput(n1),['"run_as_root"']))+pair(block('修改前 · 容器内 HTTP 请求和进程 UID 实测记录',pretty(b0),['"uid"']),block('修改后 · 容器内 HTTP 请求和进程 UID 实测记录',pretty(b1),['"uid"'])),
 result:'容器改用 UID 1000 后，root 标记变为 false；两次 HTTP 检查均返回 200 和 maturity-ok。'});

const dep=json('results/output-audit/20261111/appcat-full/dependencies.json').flatMap(v=>v.dependencies).find(d=>d.name==='commons-io.commons-io');
const localRule=a0.rules[rule],localDescription=localRule.description.split('\n').filter(l=>l.includes('When migrating')||l.includes('**Logging**')).join('\n\n');
documents.push({name:'appcat-details',title:'AppCAT｜规则、技术栈、依赖与 YAML 输出',date:'2026-11-11',
 input:block('额外依赖样例 · pom.xml 原文',excerpt(read('results/output-audit/20261111/appcat-dependency-input/pom.xml'),'<dependencies>','</dependencies>')),
 run:block('分别运行完整依赖分析和 YAML 导出','appcat.exe analyze --input <依赖样例> --output <完整报告> --target azure-aks --mode full --disable-telemetry --output-format json\n\nappcat.exe analyze --input <修改前源码> --output <YAML报告> --target azure-aks --mode full --disable-telemetry --output-format yaml'),
 output:pair(block('rules.local-storage-00001 · 原生规则字段',pretty(pick(localRule,['id','title','severity','effort']))+'\n\n'+localDescription,['mandatory']),block('projects[].properties · 原生技术信息',pretty(a0.projects[0].properties)))+block('incidents[].snippet · 原生代码片段节选',incident.snippet.split('\n').filter(l=>/^\s*(3|9|10|11|12)\s/.test(l)).join('\n'),['FileWriter'])+pair(block('dependencies.json · 所加依赖的字段',pretty(pick(dep,['name','version','type','labels']))),block('report.yaml · 原生汇总节选',excerpt(read('results/output-audit/20261111/appcat-yaml/report.yaml'),'summary:','  totalEffort:')))+pair(block('修改前 · 审计文件与业务标准输出',read(ap+'before/business/orders.log')+read(ap+'before/business/stdout.txt')),block('修改后 · 业务标准输出',read(ap+'after/business/stdout.txt'))),
 result:'full 模式列出 commons-io 依赖；JSON 与 YAML 汇总一致。规则定位到源码片段，业务契约前后均通过。'});

const npriv=json(np+'privileged/workload.json').workload,failedPriv=json('results/output-audit/20261111/neuvector/privileged/workload.json').workload;
function flagRows(){return ['before','privileged','after'].map(p=>{const w=json(np+p+'/workload.json').workload,b=json(np+p+'/business.json');return[p,w.running,w.run_as_root,w.privileged,b.uid,b.status,JSON.stringify(b.body)].join(' | ');}).join('\n');}
documents.push({name:'neuvector-privileged',title:'NeuVector｜三组容器配置与特权识别',date:'2026-11-11',
 input:pair(block('特权组 · 实际 input.yaml',excerpt(read(np+'privileged/input.yaml'),'securityContext:','privileged:')),block('修改后 · 实际 input.yaml',excerpt(y1,'securityContext:','privileged:'))),
 run:block('平台字段与实际进程分别采集','GET /v1/workload/<containerID>\nkubectl exec <Pod> -- cat /proc/1/status\nkubectl exec <Pod> -- node <HTTP与UID检查代码>'),
 output:block('三组 API 与业务结果 · 原字段逐项抽取','phase | running | run_as_root | privileged | uid | status | body\n'+flagRows(),['privileged |'])+pair(block('普通 root 容器 · /proc/1/status 原文',read(np+'before/process-status.txt').split('\n').filter(l=>/^Uid:|^CapEff:/.test(l)).join('\n')),block('特权 root 容器 · /proc/1/status 原文',read(np+'privileged/process-status.txt').split('\n').filter(l=>/^Uid:|^CapEff:/.test(l)).join('\n')))+pair(block('首次特权测试 · API 字段节选',pretty(pick(failedPriv,['pod_name','running','run_as_root','privileged'])),['"privileged"']),block('重新部署后 · API 字段节选',pretty(pick(npriv,['pod_name','running','run_as_root','privileged'])),['"privileged"'])),
 result:'三组复测的字段与配置一致。首次特权测试曾返回 false，已保留原记录；接入时需同时核对实际 Pod 配置。'});

const nstats=json(np+'after/stats-response.json'),nproc=json(np+'after/process-response.json'),nscore=json(np+'after/score-metrics.json');
documents.push({name:'neuvector-runtime',title:'NeuVector｜进程、资源统计与扫描前状态',date:'2026-11-11',
 input:block('workload.json · 实际运行对象',pretty(pick(n1,['domain','pod_name','image','running','policy_mode','profile_mode']))),
 run:block('使用同一 containerID 读取原生 API','GET /v1/workload/<containerID>/process\nGET /v1/workload/<containerID>/process_history\nGET /v1/workload/<containerID>/stats\nGET /v1/workload/<containerID>/config\nGET /v1/system/score/metrics\nGET /v1/workload/<containerID>/compliance\nGET /v1/scan/workload/<containerID>'),
 output:pair(block('process · 当前进程字段',pretty({http_status:nproc.http_status,processes:nproc.body.processes.map(p=>pick(p,['name','user','root','status','action']))})),block('stats · span_1 原始数值',pretty(nstats.body.stats.span_1)))+pair(block('security_scores · 全局各项分数',pretty(nscore.security_scores)),block('config · 原生响应',pretty(json(np+'after/config-response.json'))))+pair(block('compliance · 原生响应',pretty(json(np+'after/compliance-response.json'))),block('scan · 原生响应',pretty(json(np+'after/scan-response.json'))+'\n\n'+pretty({scan_summary:pick(n1.scan_summary,['status','scanned_at','scanner_version'])}))),
 result:'此图采集于启用扫描前：容器合规列表、漏洞列表和扫描时间为空。节点 CIS 与后续 CVE 扫描另行展示。'});

const nscan='results/output-audit/20261111/neuvector-scanning/';
const cis=json(nscan+'bench-kubernetes-after.json');
const cisCounts=Object.fromEntries(['PASS','WARN','MANUAL'].map(level=>[level,cis.body.items.filter(v=>v.level===level).length]));
documents.push({name:'neuvector-cis',title:'NeuVector｜Kubernetes 合规检查与修复建议',date:'2026-11-11',
 input:block('实际节点 · GET /v1/host 的字段节选',pretty(pick(json(nscan+'hosts.json').body.hosts[0],['name','platform','runtime']))),
 run:block('触发检查并读取报告','POST /v1/bench/host/<节点ID>/kubernetes\nGET /v1/bench/host/<节点ID>/kubernetes\nGET /v1/host/<节点ID>/compliance'),
 output:block('原生报告版本、运行时间及 items 按 level 计数',pretty({cis_version:cis.body.cis_version,run_at:cis.body.run_at,items:cis.body.items.length,counts:cisCounts}),['PASS','WARN','MANUAL'])+pair(...['PASS','WARN'].map(level=>block(level+' · 原生检查项字段',pretty(pick(cis.body.items.find(v=>v.level===level),['test_number','level','automated','description','remediation'])),['"level"'])))+block('MANUAL · 原生检查项字段',pretty(pick(cis.body.items.find(v=>v.level==='MANUAL'),['test_number','level','automated','description','remediation'])),['MANUAL']),
 result:'原生报告共 130 项：52 项 PASS、38 项 WARN、40 项 MANUAL；每项保留检查编号、说明和修复建议。'});

const scanned=json(nscan+'cve/workload-scanned.json').workload,cve=json(nscan+'cve/scan-report.json').body.report;
documents.push({name:'neuvector-cve',title:'NeuVector｜容器漏洞与软件包清单',date:'2026-11-11',
 input:block('实际被扫描容器 · workload 字段节选',pretty(pick(scanned,['domain','pod_name','image','running']))),
 run:block('启用 Scanner 后，触发并读取同一容器的扫描结果','POST /v1/scan/workload/<containerID>\nGET /v1/workload/<containerID>\nGET /v1/scan/workload/<containerID>'),
 output:pair(block('workload.scan_summary · 原生扫描汇总',pretty(scanned.scan_summary),['"high"','"medium"','succeeded','finished']),block('scan-report.modules · 前三条原生记录',pretty(cve.modules.slice(0,3))))+pair(...cve.vulnerabilities.slice(0,2).map(v=>block('vulnerabilities[] · 原生漏洞记录节选',pretty(pick(v,['name','severity','package_name','package_version','fixed_version','score_v3','vectors_v3','description'])),['"severity"','"fixed_version"'])))+block('对原生数组计数',pretty({vulnerabilities:cve.vulnerabilities.length,modules:cve.modules.length})),
 result:'扫描成功完成：27 条漏洞记录（12 High、15 Medium），209 个软件包；明细给出当前版本、修复版本及 CVSS 分数。'});


const fp=json('results/fetruth-paper/comparison.json'),fresh=json('results/fetruth/execution.json');
assert.equal(fp.exact_match,true);assert.equal(fp.matching_recommendations,16);
documents.push({name:'fetruth-workflows',date:'2026-10 / 11 既有实验',
 result:'论文归档重放 16/16 一致；新提取 jsoup 源码得到 180 条候选。两条流程分开记录。',
 input:pair(block('论文重放','固定归档 v1.0.0\n作者已提取的 jsoup 特征 + 归档模型\n不在本次重新提取源码'),block('新项目分析','固定新源码工作流\njsoup 1.15.3 或本项目 Java 示例\nJAR 提取特征 + implementation 模型')),
 run:pair(block('论文归档入口','python evaluate.py jsoup'),block('新源码入口','java -jar testingDataGeneration.jar <Java工程>\npython feTruth.py -a <Java工程>')),
 output:table(['输入 / 流程','候选方法','候选关系','输出建议'],[['论文归档 jsoup','作者归档特征','作者归档特征',fp.observed_recommendations+'（16/16 一致）'],['jsoup 新源码',fresh.candidate_methods,fresh.candidate_pairs,fresh.recommendations],['项目 Java 示例',fe.candidate_methods,fe.candidate_pairs,fe.recommendations]])+block('论文重放 · 前三条原生建议',read('results/fetruth-paper/jsoup.txt').split('\n').slice(0,4).join('\n'))+note('新源码工作流与论文归档模型存在已记录差异；180 条不能写成 180 个已确认缺陷，也不能拿来替代 16/16 的复现证据。')});
const ir='results/academic-20261113/infer/';
const bug=json(ir+'before/infer-out/report.json')[0],after=json(ir+'after/infer-out/report.json');
assert.equal(bug.bug_type,'NULLPTR_DEREFERENCE');assert.equal(after.length,0);
documents.push({name:'infer',date:'2026-11-13',result:'同一 Pulse 分析器：空指针报告 1 → 0，保留完整四步错误路径。',
 input:pair(block('修改前 · NullExample.java',read('baselines/infer/fixtures/before/NullExample.java')),block('修改后 · NullExample.java',read('baselines/infer/fixtures/after/NullExample.java'))),
 run:block('相同构建与分析入口','infer run --pulse-only --jobs 2 --results-dir <输出目录> -- javac -encoding UTF-8 -g -d <classes目录> <源码文件>'),
 output:block('report.json · 原生错误与定位',pretty(pick(bug,['bug_type','severity','file','line','procedure','qualifier'])))+table(['源码行','调用路径原文'],bug.bug_trace.map(x=>[x.line_number,x.description]))+pair(block('修改后 · 原生 report.json',pretty(after)),block('本次覆盖','修改前、后均捕获 1 个 Java 文件\n退出状态、日志、覆盖量另行归档\n零报告不等于程序没有任何错误'))});
const projects=['jsoup','commons-cli','maturity-java'].map(n=>json(ir+n+'/summary.json'));
const leaks=json(ir+'jsoup/infer-out/report.json');
documents.push({name:'infer-projects',date:'2026-11-13',result:'相同分析器用于两个真实 Java 项目和本项目示例：原生告警分别为 6、0、0。',
 input:table(['项目','Java 文件','原生告警','端到端秒数'],projects.map(x=>[x.project,x.coverage.files,x.findings,x.seconds])),
 run:block('捕获 → 分析 → 报告','源码 + 正常编译依赖 → 中间表示 / 函数摘要\nPulse 路径分析 → report.json + report.txt\n本地归档 process.json / summary.json / stdout / stderr'),
 output:table(['文件','行','原生类型'],leaks.map(x=>[x.file,x.line,x.bug_type]))+block('原生 report.json · 已出现的完整顶层字段',Object.keys(bug).join(' / '))+note('六条资源告警尚未逐条确认，包含 StringReader 等对象；需要结合资源语义复核。C/C++/ObjC、Hack 及实验性语言没有在本轮实测。')});
function addAppcatSummary(){
const before=json(ap+'before/report.json'),after=json(ap+'after/report.json');
 const levels={mandatory:'必须处理',potential:'潜在问题',optional:'可选改进'};
 function summarize(report){
  assert.equal(report.metadata.status,'Complete');
  const incidents=report.projects.flatMap(p=>p.incidents);
  const ids=[...new Set(incidents.map(i=>i.ruleId))];
  assert.equal(ids.length,report.summary.totalIssues);
  const issues=ids.filter(id=>Object.hasOwn(levels,report.rules[id].severity));
  return {issues,information:ids.filter(id=>report.rules[id].severity==='information').length,
   counts:Object.fromEntries(Object.keys(levels).map(level=>[level,issues.filter(id=>report.rules[id].severity===level).length])),
   occurrences:id=>incidents.filter(i=>i.ruleId===id)};
 }
 const left=summarize(before),right=summarize(after),props=before.projects[0].properties;
 assert.deepEqual(props,after.projects[0].properties);
 assert.deepEqual([left.issues.length,right.issues.length,left.information,right.information],[4,2,2,2]);
 const labels={
  'dockerfile-00000':'缺少 Dockerfile',
  'local-storage-00001':'使用本地文件存储',
  'utf-8-by-default-00000':'默认字符编码兼容性',
  'azure-java-version-02000':'Java 版本升级建议'
 };
 assert.deepEqual([...new Set([...left.issues,...right.issues])].sort(),Object.keys(labels).sort());
 const rows=Object.entries(labels).map(([id,title])=>{
  const severity=(before.rules[id]||after.rules[id]).severity;
  const locations=[...new Set([...left.occurrences(id),...right.occurrences(id)].map(i=>i.location?i.location.split('/').at(-1)+(i.line?':'+i.line:''):'项目级检查'))].join('、');
  const a=Number(left.issues.includes(id)),b=Number(right.issues.includes(id));
  return {id,title,severity,locations,before:a,after:b,state:b?'仍有提示':'未再命中'};
 });
 const cards=[['迁移问题 · 去重规则',left.issues.length,right.issues.length],...Object.entries(levels).map(([key,title])=>[title+' · 规则',left.counts[key],right.counts[key]])]
  .map(([title,a,b])=>`<div class="card"><span>${esc(title)}</span><strong>${a}<i>→</i>${b}</strong></div>`).join('');
 const body=rows.map(r=>`<tr><td><b>${esc(r.title)}</b><small>${esc(r.id)}</small></td><td><span class="severity ${r.severity}">${levels[r.severity]}</span></td><td>${r.before}</td><td>${r.after}</td><td class="${r.after?'remaining':'resolved'}">${r.state}</td><td>${esc(r.locations)}</td></tr>`).join('');
 
 documents.push({name:'appcat-html',date:'2026-11-11',result:'4 类迁移问题中，修改后有 2 类未再命中；另有 2 类技术发现信息。',
 input:table(['应用','Java','构建','迁移目标'],[[props.appName,props.jdkVersion,props.tools.join(' / '),'Azure AKS']]),
 run:block('相同内置规则、前后两份输入','source-only · azure-aks · JSON + HTML\n前后 metadata.status 均为 Complete\n按 ruleId 去重统计迁移问题；information 单独计算'),
 output:'<div class="cards">'+cards+'</div><table><thead><tr><th>问题 / 原生规则</th><th>严重程度</th><th>修改前</th><th>修改后</th><th>本次结果</th><th>原生定位</th></tr></thead><tbody>'+body+'</tbody></table>'+note('原生 totalIssues '+before.summary.totalIssues+' → '+after.summary.totalIssues+'；totalIncidents '+before.summary.totalIncidents+' → '+after.summary.totalIncidents+'。工作量是工具估计，不是实际工时。')});
}
addAppcatSummary();
for(const p of json('docs/assets/baseline-io.json')){
 captions[p.name]={number:p.number,title:p.title};
 documents.push({name:p.name,date:'接口核对 · 2026-11-13',kind:'固定版本的输入输出类型清单；已实测与官方支持但未实测分别标注，非新增运行结果。',result:p.note,
 stages:['输入类型与准备条件','执行与本轮选择','输出载体及全部结果状态'],
 input:table(['入口 / 材料','具体内容','验证状态'],p.inputs),
 run:note('本轮仅采用默认检查或固定预训练模型，不编写逐项目业务规则。完整字段、可选接口和原始文件链接见输入输出清单。'),
 output:table(['输出类别','内容'],p.outputs)});
}
documents.sort((a,b)=>captions[a.name].number-captions[b.name].number);
assert.deepEqual(documents.map(x=>captions[x.name].number),Array.from({length:16},(_,i)=>i+1));
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Users/YuRui/AppData/Local/ms-playwright/chromium-1248/chrome-win64/chrome.exe'});
 const panels=[];
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1100},deviceScaleFactor:1.5});
  for(const d of documents){
   const markup=html(d);assert.ok(!/[A-Za-z]:\\|YuRui|\/opt\/|\.runtime/.test(markup),'Machine path in '+d.name);
   fs.writeFileSync(path.join(preview,d.name+'.html'),markup);
   await page.setContent(markup,{waitUntil:'load'});await page.evaluate(()=>document.fonts.ready);
   const clipped=await page.locator('main,section,pre,td,th,.block').evaluateAll(nodes=>nodes.filter(n=>n.scrollWidth>n.clientWidth+1).length);
   assert.equal(clipped,0,'Clipped text: '+d.name);
   const box=await page.locator('main').boundingBox();assert.equal(box.width,1440);
   const file='docs/assets/baseline-outputs/'+d.name+'.png';
   await page.locator('main').screenshot({path:path.join(root,file)});
   panels.push({name:d.name,number:captions[d.name].number,file,box,clipped,text:await page.locator('main').innerText()});
   console.log(d.name+'.png '+Math.round(box.height)+'px');
  }
 }finally{await browser.close();}
 const dir=path.join(root,'results/report-verification');fs.mkdirSync(dir,{recursive:true});
 const all='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Infer + feTruth · 四项基线输入输出报告</title><style>'+css+'</style><nav class="gallery">'+documents.map(d=>'<a href="#'+d.name+'">图 '+captions[d.name].number+' '+esc(captions[d.name].title)+'</a>').join('')+'</nav>'+documents.map(d=>'<main id="'+d.name+'">'+content(d)+'</main>').join('')+'</html>';
 fs.writeFileSync(path.join(dir,'baseline-report.html'),all);
 fs.writeFileSync(path.join(root,'results/baseline-output-screenshots.json'),JSON.stringify({selected_academic:['infer','fetruth'],selected_commercial:['appcat','neuvector'],style:'docs/assets/baseline-report.css',capture_type:'Uniform reports derived from archived native evidence and explicitly labelled interface inventories; not native UIs',files:panels.map(x=>x.file),panels,input_sha256:Object.fromEntries(inputs)},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
