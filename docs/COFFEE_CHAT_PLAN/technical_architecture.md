# Coffee Chat 技术架构：LinkedIn自动化 + AI Agents + Memory Layer

## 📋 总览

三个核心模块的协作关系：

```
LinkedIn自动化 (MCP)
    ↓
    提取联系人信息
    ↓
AI Agents (OpenAI)
    ↓
    生成个性化消息 + 诈骗检测 + 排序
    ↓
Memory Layer (ChromaDB)
    ↓
    存储历史 + 学习优化
```

---

## 1️⃣ LinkedIn自动化 (MCP-based)

### 架构

```
Chrome DevTools MCP Server (Node.js)
    ↑ (stdio通信)
Python MCP Client
    ↑
LinkedInAutomation类
    ↑
Coffee Chat Center (Streamlit UI)
```

### 完整流程

#### Step 1: 搜索校友

```python
# 输入：公司域名 + 学校
domain = "shopify.com"
school = "University of Western Ontario"

# MCP调用
1. navigate_page(f"https://linkedin.com/search/...")
2. wait_for("Search results")
3. take_snapshot()  # 获取页面内容
```

**搜索策略**（基于域名）：
- **有LinkedIn Company Page**: 用公司filter精确搜索
- **没有Company Page**: 用域名关键词搜索
- **验证**: 检查结果中是否真的包含域名

#### Step 2: 提取联系人

```python
# 从snapshot解析联系人
snapshot = """
uid=1_38 link "Sarah Chen" url="linkedin.com/in/sarah-chen"
uid=1_43 StaticText " • 2nd"
uid=1_44 StaticText "Learning Designer @ Shopify"
uid=1_45 StaticText "Toronto, Ontario, Canada"
...
"""

# 解析逻辑
contacts = []
for line in snapshot.split('\n'):
    if 'linkedin.com/in/' in line:
        name = extract_name(line)
        url = extract_url(line)
        degree = extract_degree(line)  # 2nd, 3rd
        
        contacts.append({
            'name': name,
            'linkedin_url': url,
            'connection_degree': degree,
            'company': company,
            'domain': domain,
            'is_alumni': True,
            'school_name': school
        })
```

#### Step 3: 检测Connection Degree

**关键**：2nd degree可以connect，3rd degree只能follow

```python
if contact['connection_degree'] == '2nd':
    # 可以直接发connection request
    action = "send_connection"
elif contact['connection_degree'] == '3rd':
    # 需要找mutual connection做桥梁
    action = "find_bridge"
```

#### Step 4a: 发送Connection Request (2nd degree)

```python
# MCP操作
1. click(uid_of_connect_button)
2. wait_for("Add a note modal")
3. fill_input(note_textarea, personalized_message)
4. click(send_button)
```

**限速保护**：
- 20 connections/day
- 每次间隔30-60秒（随机）
- 记录到数据库避免重复

#### Step 4b: Mutual Connection Bridge (3rd degree)

```python
# 1. 找到mutual connections
mutuals = extract_mutual_connections(snapshot)
# Returns: [
#   {'name': 'Lisa Wang', 'title': 'HR Manager @ Shopify'},
#   {'name': 'Mike Liu', 'title': 'Software Engineer @ Shopify'}
# ]

# 2. 智能选择bridge（同部门优先）
best_bridge = select_best_bridge(
    target_title="Learning Designer",
    mutuals=mutuals
)
# Chooses: Lisa Wang (HR部门，更相关)

# 3. 先connect with bridge
connect_to_bridge(best_bridge)

# 4. 3-5天后，bridge接受了
send_bridge_request_message(
    bridge=best_bridge,
    target=target_contact
)
```

#### Step 5: 发送Coffee Chat消息

**时机**：Connection接受后

```python
# MCP操作：发送LinkedIn私信
1. navigate_to_linkedin_messages()
2. search_conversation(contact_name)
3. fill_message(personalized_coffee_chat_message)
4. send()
```

---

## 2️⃣ AI Agents (OpenAI GPT-4)

### Agent架构

```
ContactRankerAgent → 评分排序
    ↓
PersonalizationAgent → 生成个性化消息
    ↓
ScamDetectionAgent → 诈骗检测
```

### Agent 1: ContactRankerAgent

**职责**：综合评分，决定优先级

```python
class ContactRankerAgent:
    def rank_contact(self, contact, job, user_profile):
        """
        综合评分 (0-100)
        """
        score = 0
        
        # Factor 1: Job match score (0-10 → 0-40)
        score += contact.job_match_score * 4
        
        # Factor 2: Alumni (+30)
        if contact.is_alumni:
            score += 30
        
        # Factor 3: Connection degree
        if contact.connection_degree == '2nd':
            score += 20  # 容易connect
        elif contact.connection_degree == '3rd':
            score += 10  # 需要桥梁
        
        # Factor 4: Domain verified (+10)
        if contact.domain_verified:
            score += 10
        
        # Factor 5: Mutual connections (0-10)
        score += min(len(contact.mutual_connections), 10)
        
        return score
```

**AI增强**（可选）：
```python
# 用AI分析profile相似度
prompt = f"""
Contact: {contact.title} @ {contact.company}
Your background: {user_profile.summary}

Rate similarity (0-10):
"""
similarity = openai_call(prompt)
score += similarity * 2  # 额外加分
```

### Agent 2: PersonalizationAgent

**职责**：生成个性化connection request和coffee chat消息

```python
class PersonalizationAgent:
    def generate_connection_message(self, contact, job, user_profile):
        """
        生成个性化connection request消息
        """
        prompt = f"""
        You are helping write a LinkedIn connection request.
        
        Contact Information:
        - Name: {contact.name}
        - Title: {contact.title}
        - Company: {contact.company}
        - School: {contact.school_name}
        
        Your Background:
        - Schools: {user_profile.schools}
        - Target Fields: {user_profile.target_fields}
        
        Related Job: {job.title} at {job.company}
        
        Write a connection request message (max 300 chars):
        - Mention shared school (alumni connection)
        - Express interest in their work at {contact.company}
        - Keep it professional and friendly
        - DO NOT mention the job posting directly
        
        IMPORTANT: Make it sound natural, not AI-generated!
        """
        
        message = openai_call(prompt)
        return message
    
    def generate_coffee_chat_message(self, contact, user_profile, conversation_history=None):
        """
        生成coffee chat邀请消息
        """
        # 从Memory Layer获取历史（如果有）
        past_interactions = memory_layer.get_similar_conversations(contact)
        
        prompt = f"""
        Generate a coffee chat invitation message.
        
        Context:
        - Contact: {contact.name}, {contact.title} @ {contact.company}
        - You both went to {contact.school_name}
        - You're interested in {user_profile.target_fields}
        
        Past successful messages (for reference):
        {past_interactions}
        
        Requirements:
        - 80-120 words
        - Mention alumni connection
        - Express genuine interest in their work
        - Ask for 15-20min coffee chat
        - Suggest next week
        - Professional but friendly tone
        
        Generate the message:
        """
        
        message = openai_call(prompt)
        return message
```

**消息模板变化**：
- AI会生成略微不同的消息（避免被标记为spam）
- 基于Memory Layer的成功案例学习

### Agent 3: ScamDetectionAgent

**职责**：检测可疑profile，避免诈骗

```python
class ScamDetectionAgent:
    def analyze_profile(self, contact, linkedin_snapshot):
        """
        分析profile可信度
        """
        risk_score = 0
        flags = []
        
        # 1. Connections数量
        connections = extract_connections_count(linkedin_snapshot)
        if connections < 50:
            risk_score += 3
            flags.append("Low connections")
        
        # 2. Profile photo
        has_photo = check_profile_photo(linkedin_snapshot)
        if not has_photo:
            risk_score += 2
            flags.append("No profile photo")
        
        # 3. Work history
        work_history = extract_work_history(linkedin_snapshot)
        if len(work_history) < 2:
            risk_score += 2
            flags.append("Limited work history")
        
        # 4. AI分析（增强）
        ai_analysis = self._ai_check(contact, linkedin_snapshot)
        risk_score += ai_analysis['risk_score']
        flags.extend(ai_analysis['flags'])
        
        return {
            'risk_score': risk_score,  # 0-10
            'is_safe': risk_score < 7,
            'flags': flags,
            'recommendation': 'safe' if risk_score < 4 else 'caution' if risk_score < 7 else 'skip'
        }
    
    def _ai_check(self, contact, snapshot):
        """
        AI分析profile内容
        """
        prompt = f"""
        Analyze this LinkedIn profile for authenticity:
        
        Name: {contact.name}
        Title: {contact.title}
        Company: {contact.company}
        
        Profile snapshot:
        {snapshot[:1000]}
        
        Red flags to check:
        - Generic/fake-sounding title
        - Company doesn't exist
        - Profile seems auto-generated
        - Suspicious patterns
        
        Return JSON:
        {{"risk_score": 0-5, "flags": ["flag1", "flag2"]}}
        """
        
        result = openai_call(prompt, json_mode=True)
        return result
```

---

## 3️⃣ Memory Layer (ChromaDB)

### 为什么需要Memory？

**问题**：
- 每次生成消息都是"从零开始"
- 不知道哪些消息模板成功率高
- 不记得之前联系过谁、说了什么

**解决**：
- 存储所有交互历史
- 学习成功的消息模板
- 避免重复联系
- 优化outreach策略

### ChromaDB架构

```
ChromaDB (向量数据库)
    ├─ messages_collection (消息历史)
    ├─ contacts_collection (联系人档案)
    └─ interactions_collection (交互记录)
```

### Collection 1: Messages (消息历史)

```python
# 存储每一条发送的消息
message_record = {
    'id': 'msg_001',
    'contact_id': 'contact_12345',
    'type': 'connection_request',  # or 'coffee_chat'
    'message_text': "Hi Sarah, fellow UWO alum here...",
    'sent_at': '2026-01-20T10:00:00',
    'response_status': 'accepted',  # or 'ignored', 'replied'
    'response_time_hours': 24,
    'metadata': {
        'contact_title': 'Learning Designer',
        'contact_company': 'Shopify',
        'school': 'UWO',
        'target_field': 'L&D'
    }
}

# 向量化（用于相似度搜索）
embedding = openai_embedding(message_text)

# 存入ChromaDB
chroma_db.add(
    collection='messages',
    ids=[message_record['id']],
    embeddings=[embedding],
    metadatas=[message_record['metadata']],
    documents=[message_record['message_text']]
)
```

### Collection 2: Contacts (联系人档案)

```python
# 存储联系人详细信息
contact_record = {
    'id': 'contact_12345',
    'name': 'Sarah Chen',
    'title': 'Learning Designer',
    'company': 'Shopify',
    'school': 'UWO',
    'linkedin_url': '...',
    'first_contact_date': '2026-01-20',
    'last_interaction_date': '2026-01-25',
    'total_messages_sent': 2,
    'relationship_status': 'connected',  # pending, connected, coffee_chat_scheduled
    'notes': 'Very responsive, interested in AI in education'
}

# 向量化（基于profile内容）
profile_text = f"{contact.title} at {contact.company}. Interested in {topics}"
embedding = openai_embedding(profile_text)

chroma_db.add(
    collection='contacts',
    ids=[contact_record['id']],
    embeddings=[embedding],
    documents=[profile_text]
)
```

### Collection 3: Interactions (交互记录)

```python
# 记录每次交互
interaction = {
    'id': 'interaction_001',
    'contact_id': 'contact_12345',
    'type': 'coffee_chat_reply',
    'timestamp': '2026-01-25T14:00:00',
    'content': "Thanks for reaching out! I'd love to chat...",
    'sentiment': 'positive',  # AI分析
    'outcome': 'coffee_chat_scheduled',
    'learnings': 'Mentioning alumni connection was effective'
}
```

### 使用Memory优化消息

```python
class MemoryEnh个性化Agent:
    def generate_optimized_message(self, contact, user_profile):
        """
        基于历史学习，生成优化的消息
        """
        # 1. 查询相似的成功案例
        similar_contacts = memory_layer.query_similar_contacts(
            title=contact.title,
            company_type="tech",
            limit=5
        )
        
        successful_messages = [
            c for c in similar_contacts 
            if c.response_status == 'accepted'
        ]
        
        # 2. 提取成功模式
        success_patterns = analyze_patterns(successful_messages)
        # Returns: {
        #   'avg_length': 95,
        #   'common_phrases': ['fellow alum', 'coffee chat', 'learn more'],
        #   'response_rate_by_day': {'Monday': 0.3, 'Tuesday': 0.25, ...}
        # }
        
        # 3. 生成消息（加入学习）
        prompt = f"""
        Generate message based on successful patterns:
        
        Target length: {success_patterns['avg_length']} words
        Effective phrases: {success_patterns['common_phrases']}
        
        Contact: {contact.name}, {contact.title} @ {contact.company}
        
        Generate optimized message:
        """
        
        message = openai_call(prompt)
        
        return message
```

### 学习循环

```
发送消息 → 等待回复 → 记录结果
    ↓
更新Memory (ChromaDB)
    ↓
分析成功率
    ↓
调整策略（消息模板、发送时间、目标筛选）
    ↓
下次发送改进的消息
```

---

## 🔗 三个模块的协作流程

### 完整End-to-End流程

```python
# 1. LinkedIn自动化：搜索校友
contacts = linkedin_automation.search_alumni_by_domain(
    domain="shopify.com",
    schools=["UWO", "York"]
)

# 2. AI Agent：诈骗检测
safe_contacts = []
for contact in contacts:
    risk_analysis = scam_detection_agent.analyze_profile(contact)
    if risk_analysis['is_safe']:
        safe_contacts.append(contact)

# 3. AI Agent：排序
for contact in safe_contacts:
    contact.priority_score = contact_ranker_agent.rank_contact(
        contact, job, user_profile
    )

safe_contacts.sort(key=lambda c: c.priority_score, reverse=True)

# 4. Memory Layer：检查是否已联系
new_contacts = []
for contact in safe_contacts:
    if not memory_layer.has_contacted(contact):
        new_contacts.append(contact)

# 5. AI Agent：生成个性化消息
for contact in new_contacts[:20]:  # Daily limit
    # 从Memory学习
    message = personalization_agent.generate_optimized_message(
        contact, user_profile
    )
    
    # 6. LinkedIn自动化：发送
    linkedin_automation.send_connection_request(
        contact, message
    )
    
    # 7. Memory Layer：记录
    memory_layer.record_message(
        contact=contact,
        message=message,
        type='connection_request'
    )
    
    # 8. 等待30-60秒（随机，看起来更人性化）
    time.sleep(random.randint(30, 60))

# 9. 定期检查回复
check_responses_job()  # 每天运行
```

### 回复检查与学习

```python
def check_responses_job():
    """
    每天检查LinkedIn inbox，记录回复
    """
    # 1. LinkedIn自动化：读取messages
    messages = linkedin_automation.get_recent_messages()
    
    # 2. 匹配到contacts
    for msg in messages:
        contact = find_contact_by_name(msg.sender_name)
        
        if contact:
            # 3. AI分析回复情感
            sentiment = ai_analyze_sentiment(msg.content)
            
            # 4. Memory Layer：更新
            memory_layer.record_interaction(
                contact=contact,
                type='reply_received',
                content=msg.content,
                sentiment=sentiment
            )
            
            # 5. 如果是正面回复，发送coffee chat消息
            if sentiment == 'positive':
                coffee_msg = personalization_agent.generate_coffee_chat_message(
                    contact, user_profile
                )
                linkedin_automation.send_message(contact, coffee_msg)
                memory_layer.record_message(contact, coffee_msg, 'coffee_chat')
```

---

## 📊 数据流示意图

```
[Coffee Chat Center UI]
        ↓ (选择jobs)
[Job Contact Integrator]
        ↓ (提取公司domains)
[LinkedIn Automation MCP]
        ↓ (搜索 → 返回contacts)
[ScamDetectionAgent]
        ↓ (过滤 → 安全contacts)
[ContactRankerAgent]
        ↓ (排序 → 优先级列表)
[Memory Layer]
        ↓ (查重 → 未联系的contacts)
[PersonalizationAgent]
        ↓ (生成消息)
[LinkedIn Automation MCP]
        ↓ (发送connection/message)
[Memory Layer]
        ↓ (记录历史)
[定期检查回复]
        ↓
[Memory Layer学习优化]
```

---

## 🎯 实施优先级

### Phase 1: LinkedIn自动化核心 (2-3小时)
- ✅ 域名驱动搜索
- ✅ 联系人提取
- ✅ Connection degree检测
- ✅ 发送connection request
- ✅ 基本限速保护

### Phase 2: AI Agents基础 (1-2小时)
- ✅ PersonalizationAgent (消息生成)
- ✅ ScamDetectionAgent (基础检测)
- ✅ ContactRankerAgent (评分)

### Phase 3: Memory Layer (1-2小时)
- ✅ ChromaDB设置
- ✅ Messages collection
- ✅ Contacts collection
- ✅ 基础查询和记录

### Phase 4: 集成与优化 (1-2小时)
- ✅ End-to-end流程
- ✅ 回复检查
- ✅ 学习循环
- ✅ Dashboard显示

---

## ❓ 你有什么问题或想调整的吗？

1. LinkedIn自动化的逻辑清楚了吗？
2. AI Agents的职责分工合理吗？
3. Memory Layer的设计符合需求吗？
4. 有没有想要优先实现或调整的部分？
