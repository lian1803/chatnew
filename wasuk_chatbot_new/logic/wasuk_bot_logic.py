from dotenv import load_dotenv
load_dotenv()
import os
from typing import Dict, List, Optional
from openai import OpenAI
from .intent_detector import IntentDetector
from .qa_handler import QAHandler
from .meal_handler import MealHandler

class WasukBotLogic:
    """와석초 챗봇 메인 로직 클래스"""
    
    def __init__(self):
        # OpenAI 클라이언트 초기화
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("경고: OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
            self.openai_client = None
        else:
            self.openai_client = OpenAI(api_key=api_key)
        
        # 각 모듈 초기화
        self.intent_detector = IntentDetector()
        self.qa_handler = QAHandler()
        self.meal_handler = MealHandler()
        
        # 대화 기록 저장 (사용자별)
        self.conversation_memory = {}
        
        # 챗봇 설정
        self.max_conversation_length = 10  # 최대 대화 기록 수
        self.temperature = 0.7
        self.max_tokens = 150
    
    def process_message(self, user_input: str, user_id: str = "default") -> Dict:
        """
        사용자 메시지를 처리하고 카카오톡 응답 형식으로 반환합니다.
        
        Args:
            user_input (str): 사용자 입력 메시지
            user_id (str): 사용자 ID (대화 기록 관리용)
            
        Returns:
            Dict: 카카오톡 응답 형식
        """
        try:
            # 1. 의도 파악
            intent = self.intent_detector.detect(user_input)
            confidence = self.intent_detector.get_confidence_score(user_input, intent)
            
            print(f"의도: {intent}, 신뢰도: {confidence:.2f}")
            
            # 2. 의도별 처리
            if intent == "급식":
                response_text = self.meal_handler.get_meal_info(user_input)
            elif intent == "질문":
                response_text = self.qa_handler.get_answer(user_input)
            elif intent == "인사":
                response_text = self._get_greeting_response(user_input)
            else:
                # 일반 대화 또는 AI 응답
                response_text = self._get_gpt_response(user_input, user_id)
            
            # 3. 대화 기록 업데이트
            self._update_conversation_memory(user_id, user_input, response_text)
            
            # 4. 카카오톡 응답 형식으로 변환
            return self._format_kakao_response(response_text, intent)
            
        except Exception as e:
            print(f"메시지 처리 중 오류: {e}")
            return self._format_kakao_response(
                "죄송합니다. 시스템에 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
                "error"
            )
    
    def _get_greeting_response(self, user_input: str) -> str:
        """인사말에 대한 응답을 생성합니다."""
        user_input = user_input.lower()
        
        if "안녕" in user_input:
            return "안녕하세요! 파주와석초등학교 챗봇입니다. 무엇을 도와드릴까요?"
        elif "고마워" in user_input or "감사" in user_input:
            return "천만에요! 더 궁금한 것이 있으시면 언제든 말씀해 주세요."
        elif "잘가" in user_input or "잘 있어" in user_input:
            return "안녕히 가세요! 또 궁금한 것이 있으시면 언제든 찾아주세요."
        else:
            return "안녕하세요! 무엇을 도와드릴까요?"
    
    def _get_gpt_response(self, user_input: str, user_id: str) -> str:
        """GPT를 사용한 응답을 생성합니다."""
        if not self.openai_client:
            return "죄송합니다. 현재 AI 응답 기능을 사용할 수 없습니다. 학교 관련 질문이나 급식 정보를 문의해 주세요."
        
        try:
            # 대화 컨텍스트 구성
            messages = self._build_conversation_context(user_input, user_id)
            
            # GPT 응답 생성
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"GPT 응답 생성 중 오류: {e}")
            return "죄송합니다. AI 응답 생성 중 오류가 발생했습니다."
    
    def _build_conversation_context(self, user_input: str, user_id: str) -> List[Dict]:
        """대화 컨텍스트를 구성합니다."""
        messages = [
            {
                "role": "system",
                "content": """당신은 파주와석초등학교의 친근하고 도움이 되는 챗봇입니다.

주요 역할:
1. 학교 관련 질문에 친절하고 정확하게 답변
2. 급식 정보 제공
3. 학교 규칙과 절차 안내
4. 학부모님과 학생들을 위한 유용한 정보 제공

답변 스타일:
- 친근하고 공손한 말투 사용
- 명확하고 이해하기 쉬운 설명
- 필요시 구체적인 예시 제공
- 학교 정보에만 집중하여 답변

주의사항:
- 확실하지 않은 정보는 "학교로 문의해 주세요"라고 안내
- 개인정보나 민감한 정보는 제공하지 않음
- 항상 학부모님과 학생들의 입장에서 생각하여 답변"""
            }
        ]
        
        # 이전 대화 기록 추가 (최대 5개)
        if user_id in self.conversation_memory:
            recent_conversations = self.conversation_memory[user_id][-5:]
            for conv in recent_conversations:
                messages.append({"role": "user", "content": conv["user"]})
                messages.append({"role": "assistant", "content": conv["bot"]})
        
        # 현재 사용자 입력 추가
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def _update_conversation_memory(self, user_id: str, user_input: str, bot_response: str):
        """대화 기록을 업데이트합니다."""
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = []
        
        self.conversation_memory[user_id].append({
            "user": user_input,
            "bot": bot_response,
            "timestamp": "now"  # 실제 구현시에는 datetime 사용
        })
        
        # 최대 길이 제한
        if len(self.conversation_memory[user_id]) > self.max_conversation_length:
            self.conversation_memory[user_id] = self.conversation_memory[user_id][-self.max_conversation_length:]
    
    def _format_kakao_response(self, text: str, intent: str = "general") -> Dict:
        """카카오톡 응답 형식으로 변환합니다."""
        response = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": text
                        }
                    }
                ],
                "quickReplies": []
            }
        }
        
        # 의도별 퀵리플라이 추가
        quick_replies = []
        
        if intent == "급식":
            quick_replies.extend([
                {"messageText": "내일 급식 알려줘", "action": "message", "label": "내일 급식"},
                {"messageText": "이번 주 급식 알려줘", "action": "message", "label": "이번 주 급식"}
            ])
        elif intent == "질문":
            quick_replies.extend([
                {"messageText": "급식 메뉴 알려줘", "action": "message", "label": "급식 메뉴"},
                {"messageText": "학교 규칙 알려줘", "action": "message", "label": "학교 규칙"}
            ])
        else:
            quick_replies.extend([
                {"messageText": "급식 메뉴 알려줘", "action": "message", "label": "급식 메뉴"},
                {"messageText": "학교 규칙 알려줘", "action": "message", "label": "학교 규칙"},
                {"messageText": "방과후 프로그램 알려줘", "action": "message", "label": "방과후"}
            ])
        
        response["template"]["quickReplies"] = quick_replies
        
        return response 