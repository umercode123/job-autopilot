# LinkedIn Automation 详细实施计划 v7

---

## 🔧 LLM选择建议

| 用途 | 推荐 | 原因 |
|------|------|------|
| **简历优化** | GPT-4o | 长篇创意写作 |
| **文字润色/消息** | **Gemini 2.5 Flash** | 快、便宜、短文本好 |
| **Profile分析** | GPT-4o-mini | 便宜 |
| **打分** | GPT-4o-mini | 便宜 |

### 建议配置
```python
# modules/llm_config.py
import google.generativeai as genai
import os

LLM_CONFIG = {
    'resume': 'gpt-4o',
    'message_generation': 'gemini-2.5-flash',  # 更新到2.5
    'profile_analysis': 'gpt-4o-mini',
    'ranking': 'gpt-4o-mini',
}

# Gemini初始化
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

async def call_gemini(prompt):
    response = await gemini_model.generate_content_async(prompt)
    return response.text
```

---

## 📊 Rate Limiting（限流控制）

### 具体实现
```python
# modules/rate_limiter.py
import json
from datetime import datetime, date
from pathlib import Path

class RateLimiter:
    """
    每日限流控制，持久化存储
    """
    def __init__(self, state_file='data/rate_limit_state.json'):
        self.state_file = Path(state_file)
        self.daily_limit = 20
        self.note_limit = 5
        self._load_state()
    
    def _load_state(self):
        if self.state_file.exists():
            with open(self.state_file) as f:
                self.state = json.load(f)
            # 检查是否是新的一天
            if self.state.get('date') != str(date.today()):
                self._reset_daily()
        else:
            self._reset_daily()
    
    def _reset_daily(self):
        self.state = {
            'date': str(date.today()),
            'connections_sent': 0,
            'notes_sent': 0,
            'last_contact_id': None
        }
        self._save_state()
    
    def _save_state(self):
        self.state_file.parent.mkdir(exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f)
    
    def can_send_connection(self) -> bool:
        return self.state['connections_sent'] < self.daily_limit
    
    def can_send_note(self) -> bool:
        return self.state['notes_sent'] < self.note_limit
    
    def record_connection(self, contact_id):
        self.state['connections_sent'] += 1
        self.state['last_contact_id'] = contact_id
        self._save_state()
    
    def record_note(self):
        self.state['notes_sent'] += 1
        self._save_state()
    
    def get_remaining(self):
        return {
            'connections': self.daily_limit - self.state['connections_sent'],
            'notes': self.note_limit - self.state['notes_sent']
        }
```

---

## 📝 Logging配置

### 日志文件结构
```
logs/
├── linkedin_automation.log      # 主日志
├── agent_errors.log            # Agent错误专用
└── daily/
    └── 2026-01-22.log          # 每日日志归档
```

### 配置代码
```python
# modules/logging_config.py
import logging
from datetime import date
from pathlib import Path

def setup_logging():
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    (logs_dir / 'daily').mkdir(exist_ok=True)
    
    # 主日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(logs_dir / 'linkedin_automation.log'),
            logging.FileHandler(logs_dir / 'daily' / f'{date.today()}.log'),
            logging.StreamHandler()
        ]
    )
    
    # Agent错误专用
    agent_logger = logging.getLogger('agents')
    agent_handler = logging.FileHandler(logs_dir / 'agent_errors.log')
    agent_handler.setLevel(logging.ERROR)
    agent_logger.addHandler(agent_handler)
    
    return logging.getLogger('linkedin_automation')
```

---

## 🔄 中断恢复机制

### 检查点保存
```python
# modules/checkpoint.py
import json
from pathlib import Path

class Checkpoint:
    """
    保存处理进度，支持中断恢复
    """
    def __init__(self, checkpoint_file='data/checkpoint.json'):
        self.checkpoint_file = Path(checkpoint_file)
        self._load()
    
    def _load(self):
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file) as f:
                self.state = json.load(f)
        else:
            self.state = {
                'current_company': None,
                'processed_contacts': [],
                'pending_contacts': []
            }
    
    def save(self):
        self.checkpoint_file.parent.mkdir(exist_ok=True)
        with open(self.checkpoint_file, 'w') as f:
            json.dump(self.state, f)
    
    def mark_contact_processed(self, contact_id):
        self.state['processed_contacts'].append(contact_id)
        self._remove_from_pending(contact_id)
        self.save()
    
    def set_pending_contacts(self, contacts):
        self.state['pending_contacts'] = [c['id'] for c in contacts]
        self.save()
    
    def get_resume_point(self):
        """获取需要恢复处理的contacts"""
        return [c for c in self.state['pending_contacts'] 
                if c not in self.state['processed_contacts']]
    
    def clear(self):
        self.state = {
            'current_company': None,
            'processed_contacts': [],
            'pending_contacts': []
        }
        self.save()
```

### AgentManager集成恢复
```python
class AgentManager:
    def __init__(self):
        self.checkpoint = Checkpoint()
        self.rate_limiter = RateLimiter()
        # ... 其他agents
    
    async def process_contacts(self, contacts, user_profile):
        # 检查是否有未完成的任务
        resume_point = self.checkpoint.get_resume_point()
        if resume_point:
            logger.info(f"Resuming from checkpoint: {len(resume_point)} contacts remaining")
            contacts = [c for c in contacts if c['id'] in resume_point]
        
        # 保存pending
        self.checkpoint.set_pending_contacts(contacts)
        
        for contact in contacts:
            # 检查限流
            if not self.rate_limiter.can_send_connection():
                logger.info("Daily limit reached, stopping")
                break
            
            # 处理contact...
            
            # 标记完成
            self.checkpoint.mark_contact_processed(contact['id'])
            self.rate_limiter.record_connection(contact['id'])
```

---

## 🛡️ 新增安全特性

### 1. AI自主纠错（防止人名/公司名搞混）
```python
class DataValidator:
    """
    验证AI提取的数据是否正确
    """
    async def validate_contact_data(self, contact):
        # 检查人名是否看起来像公司名
        if looks_like_company_name(contact['name']):
            # 可能搞混了，重新检查
            return {"valid": False, "error": "name_looks_like_company"}
        
        # 检查公司名是否看起来像人名
        if looks_like_person_name(contact['company']):
            return {"valid": False, "error": "company_looks_like_person"}
        
        # 用GPT再次确认
        prompt = f"""
        Verify this contact data:
        Name: {contact['name']}
        Company: {contact['company']}
        Title: {contact['title']}
        
        Is the name a real person name? Is company a real company?
        Return JSON: {{"valid": true/false, "corrections": {{}}}}
        """
        return await call_gpt(prompt)

def looks_like_company_name(name):
    company_indicators = ['Inc', 'Ltd', 'Corp', 'LLC', 'Company', 'Technologies']
    return any(ind in name for ind in company_indicators)
```

### 2. 发消息前读对方Profile和Posts
```python
async def prepare_personalized_message(contact_uid):
    """
    发消息前必须先读对方profile
    """
    # Step 1: 打开对方profile
    await click(contact_uid)
    await wait_for("Experience")
    
    # Step 2: 提取profile信息
    profile_snapshot = await take_snapshot()
    profile_data = extract_profile_details(profile_snapshot)
    
    # Step 3: 滚动查看最近posts
    await scroll_to_activity()
    activity_snapshot = await take_snapshot()
    recent_posts = extract_recent_posts(activity_snapshot)
    
    # Step 4: AI生成个性化消息（基于profile和posts）
    prompt = f"""
    Generate a personalized coffee chat message based on:
    
    Profile:
    - Name: {profile_data['name']}
    - Title: {profile_data['title']}
    - Experience: {profile_data['experience'][:500]}
    
    Recent Activity:
    {recent_posts[:3] if recent_posts else "No recent posts"}
    
    My background: {user_profile['background']}
    Shared: Same school ({user_profile['school']})
    
    Requirements:
    - Reference something specific from their profile or posts
    - Keep it genuine and brief (max 200 chars)
    - End with AI disclosure
    """
    
    message = await call_gemini(prompt)
    message += "\n\n(AI-assisted via github.com/Schlaflied/job-autopilot)"
    
    return message
```

---

## 🤖 Agent编排架构（新增）

### Agent Manager模式

```python
class AgentManager:
    """
    负责编排所有AI Agents，协调执行顺序，处理错误和重试
    """
    def __init__(self):
        self.scam_detector = ScamDetectionAgent()
        self.ranker = ContactRankerAgent()
        self.personalizer = PersonalizationAgent()
        self.validator = DataValidator()
    
    async def process_contacts(self, contacts, user_profile):
        """
        编排流程：验证 → 过滤 → 打分 → 个性化
        """
        results = []
        
        for contact in contacts:
            try:
                # Step 1: 数据验证
                validation = await self.validator.validate_contact_data(contact)
                if not validation['valid']:
                    contact = await self._self_correct(contact, validation)
                
                # Step 2: 诈骗检测
                scam_result = await self.scam_detector.analyze(contact)
                if scam_result['risk_score'] >= 7:
                    continue  # 跳过高风险
                
                # Step 3: 打分
                rank_result = await self.ranker.rank_contact(contact, user_profile)
                contact['priority_score'] = rank_result['score']
                
                # Step 4: 决定是否个性化note
                if rank_result['score'] >= 80:
                    note = await self.personalizer.generate_note(contact)
                    
                    # Step 5: 审核消息是否有"人味" ✨新增
                    note = await self.reviewer.review_message(note, contact)
                    contact['note'] = note
                
                results.append(contact)
                
            except Exception as e:
                # 错误处理：记录并继续
                log_error(f"Agent error for {contact['name']}: {e}")
                continue
        
        # Step 6: 按分数排序
        return sorted(results, key=lambda x: x['priority_score'], reverse=True)
    
    async def _self_correct(self, contact, validation):
        """
        自我纠错：AI尝试修正数据问题
        """
        if validation['error'] == 'name_looks_like_company':
            # 可能name和company字段搞反了，交换
            contact['name'], contact['company'] = contact['company'], contact['name']
        
        # 用GPT再次验证
        return await self.validator.validate_with_gpt(contact)
```

### ReviewerAgent（消息审核）

```python
class ReviewerAgent:
    """
    审核AI生成的消息是否有"人味"
    """
    MAX_REVISIONS = 3
    
    async def review_message(self, message, contact):
        prompt = f"""
        Review this LinkedIn connection note for human-like quality:
        
        Message: "{message}"
        
        Check for:
        1. Does it sound robotic or templated? (BAD)
        2. Is it too formal/stiff? (BAD)
        3. Does it mention specific details about the person? (GOOD)
        4. Does it feel genuine and conversational? (GOOD)
        
        Return JSON:
        {{
            "score": 0-10,
            "is_human_like": true/false,
            "issues": ["too formal", "generic"],
            "suggestion": "Try adding..."
        }}
        """
        
        for attempt in range(self.MAX_REVISIONS):
            result = await call_gpt(prompt, model="gpt-4o-mini")
            
            if result['is_human_like'] and result['score'] >= 7:
                return message
            
            # 需要修改，重新生成
            message = await self._revise_message(message, result['suggestion'], contact)
        
        # 3次后仍不满意，返回最后版本 + 警告日志
        logger.warning(f"Message for {contact['name']} may lack human touch")
        return message
    
    async def _revise_message(self, original, suggestion, contact):
        prompt = f"""
        Revise this LinkedIn message to be more human-like:
        
        Original: "{original}"
        Issue: {suggestion}
        
        Make it more conversational and genuine.
        Keep it brief (max 200 chars).
        """
        return await call_gemini(prompt)
```

### 编排流程图

```
Contacts List
     │
     ▼
┌────────────────┐
│ DataValidator  │ ──→ 数据有问题? ──→ Self-Correct ──┐
└────────────────┘                                     │
     │ ✓                                               │
     ▼                                                 │
┌────────────────┐                                     │
│ScamDetection   │ ──→ Risk >= 7? ──→ Skip            │
└────────────────┘                                     │
     │ ✓                                               │
     ▼                                                 │
┌────────────────┐                                     │
│ContactRanker   │ ──→ Score < 50? ──→ Low Priority   │
└────────────────┘                                     │
     │ Score >= 80                                     │
     ▼                                                 │
┌────────────────┐                                     │
│Personalization │ ──→ Generate Note                  │
└────────────────┘                                     │
     │                                                 │
     ▼                                                 │
┌────────────────┐                                     │
│ ReviewerAgent  │ ──→ 人味不够? ──→ 重新生成(最多3次) │
└────────────────┘                                     │
     │ ✓                                               │
     ▼                                                 │
 Sorted Results ◄──────────────────────────────────────┘
```

### 自我纠错机制

```python
class SelfCorrectionMixin:
    """
    所有Agent共享的自我纠错能力
    """
    MAX_RETRIES = 3
    
    async def execute_with_retry(self, func, *args):
        for attempt in range(self.MAX_RETRIES):
            try:
                result = await func(*args)
                
                # 验证结果
                if self._is_valid_result(result):
                    return result
                
                # 结果无效，重试
                log_warning(f"Invalid result on attempt {attempt + 1}, retrying...")
                
            except Exception as e:
                log_error(f"Error on attempt {attempt + 1}: {e}")
        
        # 所有重试失败
        return self._get_fallback_result()
```

---

## 📋 Phase规划（更新）

| Phase | 内容 | 时间 |
|-------|------|------|
| 0 | 安全检查 | 30分钟 |
| 1 | 工作流修复 | 1-2小时 |
| 2 | AI Agents实现 + **Agent Manager** + 数据验证 | 1-2小时 |
| 3 | Memory Layer | 1-2小时 |
| **4** | **Hidden Job信号检测** | 1小时 |
| 5 | 每日状态检查 | 1小时 |
| 6 | 消息功能 + **Profile读取** | TBD |

---

## Phase 0: 安全检查

### 修改的文件
| 文件 | 改动 |
|------|------|
| `scripts/linkedin_auto_connect.py` | 添加登录检测、周末检测、验证码检测 |
| `modules/gmail_service.py` | 添加通知邮件发送方法 |

### 具体改动
```python
# linkedin_auto_connect.py 新增
def is_weekend():
    return datetime.now().weekday() >= 5

async def check_login_status(snapshot):
    if "Sign in" in snapshot:
        return "logged_out"
    if "verification" in snapshot.lower():
        send_email_notification("LinkedIn验证码", "请手动处理")
        return "verification_required"
    return "logged_in"
```

---

## Phase 1: 工作流修复

### 修改的文件
| 文件 | 改动 |
|------|------|
| `pages/coffee_chat_center.py` | 修复启动稳定性、添加状态反馈 |
| `scripts/linkedin_auto_connect.py` | 新工作流：先搜公司再找校友 |
| `modules/linkedin_automation.py` | 添加公司验证、多学校轮询 |

### 新工作流代码
```python
async def search_company_alumni(company_name, schools):
    # Step 1: 搜索公司
    await navigate(f"linkedin.com/search/companies?keywords={company_name}")
    snapshot = await take_snapshot()
    
    # Step 2: 检查公司是否存在
    if not company_exists(snapshot):
        return {"status": "company_not_found"}
    
    # Step 3: 进入公司主页 → People
    await click(company_link)
    await click(people_tab)
    
    # Step 4: 遍历所有学校
    all_contacts = []
    for school in schools:
        await fill(school_filter, school['name'])
        contacts = extract_contacts(await take_snapshot())
        all_contacts.extend(contacts)
    
    return {"status": "success", "contacts": deduplicate(all_contacts)}
```

---

## Phase 2: AI Agents实现

### 修改的文件
| 文件 | 改动 |
|------|------|
| `modules/coffee_chat_agents.py` | 真正调用GPT/Gemini |
| `modules/llm_config.py` | 新文件：LLM配置 |

### ContactRankerAgent (用GPT-4o-mini)
```python
async def rank_contact(self, contact, user_profile):
    prompt = f"""
    Rank this LinkedIn contact for coffee chat relevance (0-100):
    
    Contact: {contact['name']}, {contact['title']} at {contact['company']}
    Is Alumni: {contact.get('is_alumni', False)}
    
    User's target: {user_profile['target_fields']}
    User's background: {user_profile['background']}
    
    Return JSON: {{"score": 0-100, "reason": "..."}}
    """
    return await call_gpt(prompt, model="gpt-4o-mini")
```

### PersonalizationAgent (用Gemini)
```python
async def should_send_note(self, contact, daily_note_count):
    if daily_note_count >= 5:
        return False, None
    
    # 用Gemini生成消息
    prompt = f"""
    Generate a brief LinkedIn connection note (max 200 chars):
    - I'm a {user['background']} graduate from {user['school']}
    - Contact: {contact['name']} at {contact['company']}
    - Shared: Same school alumni
    
    Keep it personal and genuine. Include AI disclosure at end.
    """
    message = await call_gemini(prompt)
    message += "\n\n(AI-assisted via job-autopilot)"
    return True, message
```

---

## Phase 3: Memory Layer

### 修改的文件
| 文件 | 改动 |
|------|------|
| `modules/coffee_chat_memory.py` | 增量添加、搜索历史 |
| `scripts/import_connections.py` | 新文件：导入现有connections |

### 增量添加
```python
def save_contact(self, contact_id, profile_text, metadata):
    # 检查是否已存在
    existing = self.contacts.get(ids=[contact_id])
    if existing['ids']:
        return  # 跳过已存在的
    
    # 生成embedding并添加
    embedding = get_embedding(profile_text)
    self.contacts.add(
        ids=[contact_id],
        embeddings=[embedding],
        documents=[profile_text],
        metadatas=[metadata]
    )
```

### 搜索历史
```python
def has_searched_company(self, company_name):
    # 查询搜索历史
    result = self.search_history.get(where={"company": company_name})
    return len(result['ids']) > 0

def save_search(self, company_name, school, results_count):
    self.search_history.add(
        ids=[f"{company_name}_{school}_{datetime.now().isoformat()}"],
        documents=[f"Searched {company_name} for {school}"],
        metadatas={"company": company_name, "school": school, "count": results_count}
    )
```

---

## Phase 4: Hidden Job信号检测

### 修改的文件
| 文件 | 改动 |
|------|------|
| `modules/hidden_job_detector.py` | 新文件：检测公司招聘信号 |
| `pages/coffee_chat_center.py` | 显示Hidden Job信号 |

### 检测逻辑
```python
class HiddenJobDetector:
    async def check_company_signals(self, company_name):
        signals = []
        
        # 1. 检查LinkedIn公司主页
        # 看最近posts是否提到hiring, growing, expanding
        
        # 2. 用GPT分析公司新闻
        # 融资、扩张、新产品
        
        # 3. 检查员工增长趋势
        # 对比3个月前员工数
        
        return {
            "is_likely_hiring": len(signals) >= 2,
            "signals": signals,
            "confidence": 0.8 if len(signals) >= 2 else 0.3
        }
```

---

## Phase 5: 每日状态检查

### 修改的文件
| 文件 | 改动 |
|------|------|
| `scripts/daily_check.py` | 新文件：每日运行 |
| `modules/coffee_chat_memory.py` | 状态更新方法 |

### 每日检查脚本
```python
async def daily_check():
    # 1. 打开LinkedIn → My Network → Sent
    await navigate("linkedin.com/mynetwork/invitation-manager/sent/")
    
    # 2. 获取pending requests
    pending = extract_pending_requests(await take_snapshot())
    
    # 3. 对比Memory，找出被接受的
    for contact_id in memory.get_pending():
        if contact_id not in pending:
            memory.update_status(contact_id, "accepted")
    
    # 4. 打印统计
    stats = memory.get_stats()
    print(f"Sent: {stats['sent']}, Accepted: {stats['accepted']}")
```

---

## Phase 6: 消息功能（未来）

### 前提条件
- Job Scraper有数据
- 连接已被接受

### 逻辑
```python
async def send_coffee_chat_messages():
    # 获取已接受的连接
    accepted = memory.get_contacts(status="accepted")
    
    # 筛选：公司在job_scraper中
    for contact in accepted:
        if job_has_company(contact['company']):
            message = await personalization_agent.generate_message(contact)
            await send_linkedin_message(contact, message)
```

---

## ❓ 还有什么问题？
