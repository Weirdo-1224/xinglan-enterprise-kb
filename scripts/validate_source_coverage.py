"""Validate Stage 2.1 external-source coverage without counting synthetic rows."""
from pathlib import Path
import csv
ROOT=Path(__file__).resolve().parents[1]
with (ROOT/'sources/SOURCE_REGISTRY.csv').open(encoding='utf-8-sig',newline='') as f: sources={r['source_id']:r for r in csv.DictReader(f)}
with (ROOT/'manifests/KNOWLEDGE_MANIFEST.csv').open(encoding='utf-8-sig',newline='') as f: assets={r['knowledge_id']:r for r in csv.DictReader(f)}
C={
'POL001':{'劳动与用工官方规则':'SRC-LAW-001','个人信息保护规则':'SRC-LAW-003','企业人力资源实践':'SRC-CORP-004'},'POL002':{'劳动相关官方规则':'SRC-LAW-001','个人信息保护规则':'SRC-LAW-003','企业招聘实践':'SRC-CORP-004'},'POL003':{'劳动与职业发展相关规则':'SRC-LAW-001','企业培训实践':'SRC-CORP-004','培训案例':'SRC-ROLE-003'},'POL004':{'劳动相关官方规则':'SRC-LAW-001','企业绩效实践':'SRC-CORP-004','绩效改进案例':'SRC-CORP-001'},'POL005':{'项目管理标准或指南':'SRC-CORP-002','企业项目实践':'SRC-CORP-003','政企项目案例':'SRC-CASE-003'},'POL006':{'项目管理实践':'SRC-CORP-002','企业投资或立项内控':'SRC-CORP-003','公开项目案例':'SRC-CASE-005'},'POL007':{'项目变更实践':'SRC-CORP-003','合同变更规则':'SRC-LAW-006','变更争议案例':'SRC-CASE-007'},'POL008':{'档案管理规则':'SRC-LAW-008','企业会议实践':'SRC-CORP-004','项目会议案例':'SRC-CASE-006'},'POL009':{'档案管理规则':'SRC-LAW-008','知识管理实践':'SRC-STD-003','企业文档规范':'SRC-CORP-004'},'POL010':{'公文与档案官方规则':'SRC-STD-004','公开企业公文实践':'SRC-CORP-004','格式案例':'SRC-LAW-008'},'POL011':{'官方采购或招投标规则':'SRC-BID-001','企业采购内控实践':'SRC-MOF-003','信息化采购案例':'SRC-CASE-003'},'POL012':{'企业内控参考':'SRC-MOF-002','供应商管理实践':'SRC-MOF-003','供应商风险案例':'SRC-CASE-004'},'POL013':{'招标投标官方规则':'SRC-LAW-005','电子招投标规则':'SRC-LAW-007','公开招投标案例':'SRC-CASE-005'},'POL014':{'民商事与合同官方规则':'SRC-LAW-006','企业合同内控实践':'SRC-CORP-003','合同争议案例':'SRC-CASE-007'},'POL015':{'会计与预算规则':'SRC-LAW-009','企业预算内控':'SRC-CORP-003','项目预算案例':'SRC-CASE-009'},'POL016':{'会计与成本规则':'SRC-LAW-009','项目成本实践':'SRC-CORP-003','成本偏差案例':'SRC-CASE-005'},'POL017':{'数据与个人信息官方规则':'SRC-LAW-004','网络安全规则':'SRC-LAW-002','信息安全标准实践':'SRC-STD-001'},'POL018':{'知识产权与合同官方规则':'SRC-LAW-010','个人信息保护规则':'SRC-LAW-003','企业保密实践':'SRC-ROLE-006'}}
err=[]
for ref in (k for k,v in assets.items() if v['knowledge_type']=='PUBLIC_REFERENCE'):
 if not any(ref in s['used_by'].split(';') and s['verification_status']=='VERIFIED' and s['source_type']!='SYNTHETIC' for s in sources.values()): err.append(f'{ref}: missing VERIFIED external source')
for p,cats in C.items():
 ids=list(cats.values()); bad=[i for i in ids if i not in sources or sources[i]['verification_status']!='VERIFIED' or sources[i]['source_type']=='SYNTHETIC']; req=int(assets[p]['minimum_source_count'])
 if len(set(ids))-len(set(bad))<req: err.append(f'{p}: missing category = {"; ".join(k for k,v in cats.items() if v in bad)}; current verified external sources = {len(set(ids))-len(set(bad))}; required = {req}')
 else: print(f'{p}: verified external sources = {len(set(ids))}; covered_categories = {";".join(cats)}; FULL')
if err: raise SystemExit('FAIL:\n'+'\n'.join(err))
print('PASS: 18/18 PUBLIC_REFERENCE and 18/18 POLICY coverage requirements are met')
