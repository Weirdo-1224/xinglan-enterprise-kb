# 知识架构

知识资产按企业基础、公开依据、制度、SOP、FAQ/规则、岗位、历史案例、模板和结构化业务数据分层。`parent_knowledge` 表示可多值的上级知识，`depends_on` 表示执行或派生所需的多项资产，`dependency_rationale` 解释业务原因；三者共同形成 Canonical Facts → 制度 → SOP → FAQ/模板 → 案例/数据的可审计关系，并通过 `business_chain_stage` 连接 18 个业务阶段。

企业事实来自公司 Canonical Facts；项目案例事实分别来自 P001/P002/P003 Canonical Facts。Agent Coverage 按能力逐行映射所需资产类型和具体 ID，不能用“每类至少一个”代替能力证明。

正文生成时，每个 Markdown 文件须使用统一 YAML front matter；结构化数据须使用对应 JSON Schema。Manifest 只表示规划状态，`status=planned` 不代表文件已经存在。
