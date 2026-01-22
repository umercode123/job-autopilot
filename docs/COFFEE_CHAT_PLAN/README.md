# Coffee Chat Plan - 核心文档

## 📚 保留的核心文档（6个）

### 1. **README.md** (本文件)
项目概览和文档索引

### 2. **technical_architecture.md** ⭐ 最重要
完整技术架构文档：
- LinkedIn自动化 (MCP-based)
  - 域名驱动搜索
  - Connection degree检测
  - 发送connection request
  - Mutual connection桥梁
- AI Agents
  - PersonalizationAgent (消息生成)
  - ScamDetectionAgent (profile验证)
  - ContactRankerAgent (优先级排序)
- Memory Layer (ChromaDB → Pinecone)
  - Messages collection
  - Contacts collection
  - 学习循环

### 3. **implementation_plan.md**
实施计划：
- 数据库设计 (UserProfile, CoffeeChatContact, etc.)
- UI页面规划
- 实施阶段与时间估算

### 4. **sme_search_strategy.md**
中小企业搜索策略：
- 基于域名的公司识别
- 域名验证逻辑
- 优先级评分系统（平等对待大厂+中小企业）

### 5. **MCP_ARCHITECTURE.md**
Chrome DevTools MCP集成架构：
- MCP server通信机制
- Browser automation原理

### 6. **task.md**
当前任务追踪

---

## 🎯 实施优先级

### ✅ 已完成
- User Profile页面
- Coffee Chat Center基础UI
- Job Contact Integrator (集成job scraper)
- Load Jobs功能
- 数据库设计

### 🔄 当前进行中
- **LinkedIn自动化** (Phase 1)
  - ⏳ 域名驱动搜索实现
  - ⏳ 联系人提取
  - ⏳ Connection request发送

### 📋 待实施
- **AI Agents** (Phase 2)
  - PersonalizationAgent
  - ScamDetectionAgent
  - ContactRankerAgent

- **Memory Layer** (Phase 3)
  - ChromaDB设置
  - 消息历史存储
  - 学习优化
  - (后续迁移到Pinecone)

---

## 📝 技术笔记

- **Memory Layer**: 先用ChromaDB验证逻辑，确认后迁移到Pinecone
- **User Profile**: LinkedIn自动化完成后再完善
- **Framework**: 保持Streamlit，通过cache和fragment优化性能

---

## ✂️ 清理记录

### 已删除文档 (2026-01-20)
- ~~confidence_boost.md~~ (信心建设，非技术文档)
- ~~completeness_checklist.md~~ (过时，包含Apollo等未使用功能)
- ~~simplified_workflow.md~~ (已合并到technical_architecture.md)
- ~~GETTING_STARTED.md~~ (内容与README重复)
- ~~linkedin_degree_strategy.md~~ (已合并到technical_architecture.md)
- ~~job_scraper_integration.md~~ (已实现完成)
- ~~smart_alumni_search_flow.md~~ (已合并到technical_architecture.md)
- ~~morning_feedback_additions.md~~ (临时讨论记录)
- ~~additional_features.md~~ (已整合到其他文档)

保留**6个核心技术文档**，删除**9个过时/重复文档**
