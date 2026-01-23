"""
Agent Manager
编排所有AI Agents，协调执行顺序，处理错误和重试
"""
import os
import sys
from typing import Dict, List, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.logger_config import app_logger
from modules.coffee_chat_agents import ContactRankerAgent, ScamDetectionAgent, PersonalizationAgent
from modules.coffee_chat_memory import CoffeeChatMemory
from modules.data_validator import DataValidator
from modules.hidden_job_detector import HiddenJobDetector
from modules.rate_limiter import RateLimiter
from modules.checkpoint import Checkpoint


class ReviewerAgent:
    """
    审核AI生成的消息是否有"人味"
    """
    MAX_REVISIONS = 3
    
    def __init__(self):
        self.client = None
        self._init_openai()
    
    def _init_openai(self):
        """初始化OpenAI客户端"""
        try:
            from openai import OpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.client = OpenAI(api_key=api_key)
        except Exception as e:
            app_logger.warning(f"OpenAI not available: {e}")
    
    def review_message(self, message: str, contact: Dict) -> str:
        """
        审核消息是否有"人味"
        
        Args:
            message: 生成的消息
            contact: 联系人信息
            
        Returns:
            审核/修改后的消息
        """
        if not self.client or not message:
            return message
        
        try:
            for attempt in range(self.MAX_REVISIONS):
                result = self._evaluate_message(message, contact)
                
                if result.get('is_human_like') and result.get('score', 0) >= 7:
                    app_logger.info(f"Message approved (score: {result.get('score')})")
                    return message
                
                # 需要修改
                app_logger.info(f"Message revision needed (score: {result.get('score')}, attempt {attempt + 1})")
                message = self._revise_message(message, result.get('suggestion', ''), contact)
            
            # 3次后仍不满意，返回最后版本
            app_logger.warning(f"Message for {contact.get('name')} may lack human touch after {self.MAX_REVISIONS} revisions")
            return message
            
        except Exception as e:
            app_logger.error(f"Message review failed: {e}")
            return message
    
    def _evaluate_message(self, message: str, contact: Dict) -> Dict:
        """Evaluate message for human-like quality"""
        try:
            prompt = f"""
Review this LinkedIn connection note for human-like quality:

Message: "{message}"
Contact: {contact.get('name', 'Unknown')} at {contact.get('company', 'Unknown')}

Check for:
1. Does it sound robotic or templated? (BAD)
2. Is it too formal/stiff? (BAD)
3. Does it mention specific details about the person? (GOOD)
4. Does it feel genuine and conversational? (GOOD)
5. Is it appropriately brief (under 300 chars)? (GOOD)

Return JSON only:
{{
    "score": 0-10,
    "is_human_like": true/false,
    "issues": ["issue1", "issue2"],
    "suggestion": "specific improvement suggestion"
}}
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at detecting AI-generated text. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            import json
            return json.loads(response.choices[0].message.content.strip())
            
        except Exception as e:
            app_logger.error(f"Message evaluation failed: {e}")
            return {'score': 7, 'is_human_like': True}  # Default to pass
    
    def _revise_message(self, original: str, suggestion: str, contact: Dict) -> str:
        """修改消息使其更有人味"""
        try:
            prompt = f"""
Revise this LinkedIn message to be more human-like:

Original: "{original}"
Contact: {contact.get('name', 'there')} at {contact.get('company', '')}
Issue: {suggestion}

Requirements:
- Make it more conversational and genuine
- Add a specific, personal touch
- Keep it brief (max 200 chars before AI disclosure)
- Don't be generic or templated
- Sound like a real person wrote it

Return ONLY the revised message text, nothing else.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are helping make messages sound more human and genuine."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.8
            )
            
            revised = response.choices[0].message.content.strip().strip('"')
            
            # Ensure under 300 chars
            if len(revised) > 280:
                revised = revised[:277] + "..."
            
            return revised
            
        except Exception as e:
            app_logger.error(f"Message revision failed: {e}")
            return original


class AgentManager:
    """
    负责编排所有AI Agents，协调执行顺序，处理错误和重试
    
    Pipeline:
    1. DataValidator - 验证数据正确性
    2. ScamDetectionAgent - 诈骗检测
    3. ContactRankerAgent - 打分排序
    4. PersonalizationAgent - 生成消息
    5. ReviewerAgent - 审核消息
    """
    
    def __init__(self):
        self.validator = DataValidator()
        self.scam_detector = ScamDetectionAgent()
        self.ranker = ContactRankerAgent()
        self.personalizer = PersonalizationAgent()
        self.reviewer = ReviewerAgent()
        self.memory = CoffeeChatMemory()
        self.hidden_job_detector = HiddenJobDetector()
        self.rate_limiter = RateLimiter()
        self.checkpoint = Checkpoint()
        
        app_logger.info("AgentManager initialized with all agents")
    
    async def process_contacts(
        self,
        contacts: List[Dict],
        user_profile: Dict = None,
        generate_notes: bool = True
    ) -> List[Dict]:
        """
        编排流程：验证 → 过滤 → 打分 → 个性化 → 审核
        
        Args:
            contacts: 联系人列表
            user_profile: 用户配置
            generate_notes: 是否生成个性化消息
            
        Returns:
            处理后的联系人列表（按分数排序）
        """
        results = []
        skipped = {'validation': 0, 'scam': 0, 'duplicate': 0}
        
        for contact in contacts:
            try:
                contact_id = contact.get('linkedin_url', contact.get('name', ''))
                
                # Step 0: 检查是否已处理
                if self.memory.has_contacted(contact_id):
                    skipped['duplicate'] += 1
                    continue
                
                # Step 1: 数据验证
                validation = self.validator.validate_contact_data(contact)
                if not validation['valid']:
                    # 尝试自动纠正
                    contact = self.validator.auto_correct(contact, validation)
                    
                    # 重新验证
                    recheck = self.validator.validate_contact_data(contact)
                    if not recheck['valid']:
                        app_logger.warning(f"Validation failed for {contact.get('name')}: {recheck['error']}")
                        skipped['validation'] += 1
                        continue
                
                # Step 2: 诈骗检测
                scam_result = self.scam_detector.analyze_profile(contact)
                if scam_result['risk_score'] >= 7:
                    app_logger.info(f"Scam detected for {contact.get('name')}: {scam_result['flags']}")
                    skipped['scam'] += 1
                    continue
                
                contact['scam_risk'] = scam_result['risk_score']
                
                # Step 3: 打分
                score = self.ranker.rank_contact(contact, user_profile=user_profile)
                contact['priority_score'] = score
                
                # Step 4: 检查Hidden Job信号（如果有公司帖子）
                company_posts = contact.get('company_posts', [])
                if company_posts:
                    hiring_result = self.hidden_job_detector.check_company_signals(
                        contact.get('company', ''),
                        company_posts
                    )
                    if hiring_result['is_likely_hiring']:
                        # 加分
                        boost = self.hidden_job_detector.get_priority_boost(hiring_result)
                        contact['priority_score'] = min(100, contact['priority_score'] + boost)
                        contact['hiring_signals'] = hiring_result['signals']
                
                # Step 5: 生成个性化消息（高分联系人）
                if generate_notes and contact['priority_score'] >= 70:
                    if self.rate_limiter.can_send_note():
                        note = self.personalizer.generate_connection_message(contact)
                        
                        # Step 6: 审核消息
                        note = self.reviewer.review_message(note, contact)
                        
                        # 添加AI披露
                        if note and "(AI-assisted" not in note:
                            note += "\n\n(AI-assisted via job-autopilot)"
                        
                        contact['note'] = note
                
                results.append(contact)
                
            except Exception as e:
                app_logger.error(f"Agent error for {contact.get('name', 'Unknown')}: {e}")
                continue
        
        # 按分数排序
        results = sorted(results, key=lambda x: x.get('priority_score', 0), reverse=True)
        
        app_logger.info(
            f"AgentManager processed {len(contacts)} contacts: "
            f"{len(results)} valid, "
            f"{skipped['duplicate']} duplicates, "
            f"{skipped['validation']} validation failed, "
            f"{skipped['scam']} scam detected"
        )
        
        return results
    
    def process_contacts_sync(
        self,
        contacts: List[Dict],
        user_profile: Dict = None,
        generate_notes: bool = True
    ) -> List[Dict]:
        """
        同步版本的process_contacts
        """
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.process_contacts(contacts, user_profile, generate_notes)
        )
    
    def quick_filter(self, contacts: List[Dict]) -> List[Dict]:
        """
        快速过滤（不调用AI）
        只做基本的验证和去重
        
        Args:
            contacts: 联系人列表
            
        Returns:
            过滤后的列表
        """
        filtered = []
        
        for contact in contacts:
            contact_id = contact.get('linkedin_url', contact.get('name', ''))
            
            # 去重
            if self.memory.has_contacted(contact_id):
                continue
            
            # 基本验证
            validation = self.validator.validate_contact_data(contact)
            if validation['valid']:
                filtered.append(contact)
            elif validation.get('corrections', {}).get('swap_name_company'):
                # 自动纠正
                corrected = self.validator.auto_correct(contact, validation)
                filtered.append(corrected)
        
        return filtered


# 全局实例
agent_manager = AgentManager()


if __name__ == "__main__":
    print("Agent Manager Test\n" + "=" * 60)
    
    # 测试数据
    test_contacts = [
        {
            'name': 'John Smith',
            'company': 'Google',
            'title': 'Software Engineer',
            'school': 'UWO',
            'connection_degree': '2nd',
            'linkedin_url': 'https://www.linkedin.com/in/johnsmith'
        },
        {
            'name': 'ACME Inc',  # 搞反了
            'company': 'Jane Doe',
            'title': 'Manager',
            'linkedin_url': 'https://www.linkedin.com/in/janedoe'
        },
        {
            'name': 'Recruiter Pro',  # 可疑
            'company': 'Unknown Startup',
            'title': 'CEO & Founder',
            'connections_count': 10,
            'linkedin_url': 'https://www.linkedin.com/in/scammer'
        }
    ]
    
    manager = AgentManager()
    
    print("\nProcessing contacts...")
    results = manager.process_contacts_sync(test_contacts, generate_notes=False)
    
    print(f"\nResults: {len(results)} valid contacts")
    for contact in results:
        print(f"  - {contact['name']} @ {contact['company']}")
        print(f"    Score: {contact.get('priority_score', 0):.1f}")
        print(f"    Scam Risk: {contact.get('scam_risk', 0)}")
