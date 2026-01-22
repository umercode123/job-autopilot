# Task: LinkedIn Coffee Chat 策略 - Playwright + AI Agents 集成

## 目标
基于 career coach 建议的 **Coffee Chat 策略**：
1. **优先目标**：Potential Supervisor（潜在主管）
2. **校友优先**：意向部门的校友最容易建立联系
3. **技术栈**：chrome-devtools MCP + LangChain + crewAI
4. **人工介入**：支持 headful 模式，允许手动调整

## 任务清单

### 1. 项目分析 ✅
- [x] 查看 `APOLLO_AGENT_PLAN.md` 方案文档
- [x] 分析 `apollo_automation.py` 的 Playwright 实现
- [x] 分析 `ai_agent.py` 的 AI 功能
- [x] 了解项目整体架构和技术栈

### 2. Coffee Chat 策略设计
- [x] 确认优先级：校友 > Potential Supervisor > 同职位员工
- [/] 设计 LinkedIn 搜索策略（MCP chrome-devtools）
- [/] 设计 LangChain + crewAI multi-agent 架构
- [ ] 配置跨领域搜索（HR+edu, HR+AI, edu+AI）
- [ ] 定义 AI disclosure 邮件模板

### 3. 实施计划
- [/] 创建详细的实施计划文档
- [ ] 定义验证策略
- [ ] 获取用户确认后开始实施
