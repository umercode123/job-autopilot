"""
Hidden Job Detector
检测公司招聘信号，识别隐藏的工作机会
"""
import os
import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.logger_config import app_logger


# 招聘信号关键词
HIRING_SIGNALS = {
    'strong': [
        'hiring', 'we are hiring', "we're hiring", 'join our team',
        'open positions', 'job opening', 'career opportunity',
        'looking for', 'seeking', 'recruiting'
    ],
    'medium': [
        'growing team', 'expanding', 'scaling', 'new roles',
        'team growth', 'building a team', 'adding to our team'
    ],
    'weak': [
        'funding', 'raised', 'series a', 'series b', 'series c',
        'new office', 'expansion', 'launch', 'growth'
    ]
}

# 增长信号（可能意味着招聘）
GROWTH_SIGNALS = [
    'growth', 'expansion', 'acquired', 'funding', 'investment',
    'new product', 'new market', 'international', 'global expansion'
]


class HiddenJobDetector:
    """
    检测公司招聘信号，识别隐藏的工作机会
    """
    
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
    
    def check_company_signals(self, company_name: str, company_posts: List[str] = None) -> Dict:
        """
        检测公司的招聘信号
        
        Args:
            company_name: 公司名称
            company_posts: 公司最近的LinkedIn帖子（可选）
            
        Returns:
            Dict with is_likely_hiring, signals, confidence
        """
        signals = []
        confidence = 0.0
        
        # 分析帖子内容
        if company_posts:
            for post in company_posts:
                post_signals = self._analyze_post(post)
                signals.extend(post_signals)
        
        # 计算置信度
        strong_count = sum(1 for s in signals if s['strength'] == 'strong')
        medium_count = sum(1 for s in signals if s['strength'] == 'medium')
        weak_count = sum(1 for s in signals if s['strength'] == 'weak')
        
        confidence = min(1.0, (strong_count * 0.4 + medium_count * 0.2 + weak_count * 0.1))
        
        is_likely_hiring = confidence >= 0.3 or strong_count >= 1
        
        result = {
            'company': company_name,
            'is_likely_hiring': is_likely_hiring,
            'confidence': round(confidence, 2),
            'signals': signals,
            'signal_counts': {
                'strong': strong_count,
                'medium': medium_count,
                'weak': weak_count
            },
            'checked_at': datetime.now().isoformat()
        }
        
        app_logger.info(f"Hidden job check for {company_name}: {'Likely hiring' if is_likely_hiring else 'No signals'} (confidence: {confidence:.0%})")
        
        return result
    
    def _analyze_post(self, post_text: str) -> List[Dict]:
        """
        分析单个帖子中的招聘信号
        
        Args:
            post_text: 帖子文本
            
        Returns:
            List of signal dicts
        """
        signals = []
        post_lower = post_text.lower()
        
        for strength, keywords in HIRING_SIGNALS.items():
            for keyword in keywords:
                if keyword in post_lower:
                    signals.append({
                        'keyword': keyword,
                        'strength': strength,
                        'context': self._extract_context(post_text, keyword)
                    })
        
        return signals
    
    def _extract_context(self, text: str, keyword: str, window: int = 50) -> str:
        """提取关键词周围的上下文"""
        text_lower = text.lower()
        idx = text_lower.find(keyword.lower())
        
        if idx == -1:
            return ""
        
        start = max(0, idx - window)
        end = min(len(text), idx + len(keyword) + window)
        
        return "..." + text[start:end] + "..."
    
    async def analyze_with_ai(self, company_name: str, company_info: str) -> Dict:
        """
        使用AI分析公司招聘可能性
        
        Args:
            company_name: 公司名称
            company_info: 公司信息/帖子内容
            
        Returns:
            AI分析结果
        """
        if not self.client:
            return {'ai_analyzed': False}
        
        try:
            prompt = f"""
Analyze this company information for hidden hiring signals:

Company: {company_name}
Information/Posts:
{company_info[:2000]}

Look for:
1. Direct hiring signals (job posts, "we're hiring")
2. Growth signals (funding, expansion, new products)
3. Team growth indicators (new hires, team expansion)
4. News indicating possible hiring (acquisitions, new offices)

Return JSON:
{{
    "is_likely_hiring": true/false,
    "confidence": 0.0-1.0,
    "signals": ["signal1", "signal2"],
    "reasoning": "brief explanation",
    "recommended_action": "reach out now/wait/skip"
}}
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at identifying hidden job opportunities. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            import json
            result = json.loads(response.choices[0].message.content.strip())
            result['ai_analyzed'] = True
            
            return result
            
        except Exception as e:
            app_logger.error(f"AI analysis failed: {e}")
            return {'ai_analyzed': False, 'error': str(e)}
    
    def check_employee_growth(self, current_count: int, previous_count: int, months: int = 3) -> Dict:
        """
        检查员工增长趋势
        
        Args:
            current_count: 当前员工数
            previous_count: 之前员工数
            months: 对比月数
            
        Returns:
            增长分析结果
        """
        if previous_count == 0:
            return {
                'growth_rate': None,
                'is_growing': False,
                'signal': 'insufficient_data'
            }
        
        growth_rate = (current_count - previous_count) / previous_count
        monthly_growth = growth_rate / months if months > 0 else growth_rate
        
        # 月增长超过5%通常意味着积极招聘
        is_fast_growing = monthly_growth >= 0.05
        
        return {
            'current_employees': current_count,
            'previous_employees': previous_count,
            'growth_rate': round(growth_rate * 100, 1),
            'monthly_growth': round(monthly_growth * 100, 1),
            'is_growing': growth_rate > 0,
            'is_fast_growing': is_fast_growing,
            'signal': 'likely_hiring' if is_fast_growing else 'stable' if growth_rate >= 0 else 'contracting'
        }
    
    def get_priority_boost(self, hiring_result: Dict) -> float:
        """
        根据招聘信号计算优先级提升
        
        Args:
            hiring_result: check_company_signals的结果
            
        Returns:
            优先级提升分数 (0-20)
        """
        if not hiring_result.get('is_likely_hiring'):
            return 0.0
        
        confidence = hiring_result.get('confidence', 0)
        strong_signals = hiring_result.get('signal_counts', {}).get('strong', 0)
        
        # 基础分 + 置信度加成 + 强信号加成
        boost = 5.0 + (confidence * 10) + (strong_signals * 2)
        
        return min(20.0, boost)


# 全局实例
hidden_job_detector = HiddenJobDetector()


if __name__ == "__main__":
    print("Hidden Job Detector Test\n" + "=" * 50)
    
    # 测试帖子
    test_posts = [
        "Excited to announce we're hiring! Looking for talented engineers to join our growing team.",
        "Just closed our Series B funding round! Time to scale up.",
        "Great quarterly results! Our team delivered amazing work.",
        "We're expanding to new markets in Europe and Asia.",
    ]
    
    detector = HiddenJobDetector()
    
    result = detector.check_company_signals("Test Company", test_posts)
    
    print(f"\nCompany: {result['company']}")
    print(f"Likely Hiring: {result['is_likely_hiring']}")
    print(f"Confidence: {result['confidence']:.0%}")
    print(f"Signal Counts: {result['signal_counts']}")
    print(f"\nSignals found:")
    for signal in result['signals']:
        print(f"  - [{signal['strength']}] {signal['keyword']}")
