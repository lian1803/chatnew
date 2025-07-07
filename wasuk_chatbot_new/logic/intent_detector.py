class IntentDetector:
    """사용자 메시지의 의도를 파악하는 클래스"""
    
    def __init__(self):
        # 의도별 키워드 정의
        self.intent_keywords = {
            "급식": [
                "급식", "밥", "메뉴", "식단", "점심", "아침", "저녁", 
                "오늘 뭐 먹어", "내일 뭐 먹어", "급식 메뉴", "식단 알려줘"
            ],
            "질문": [
                "전학", "학교", "규칙", "시험", "방과후", "도서관", "운동장",
                "어떻게", "절차", "신청", "발급", "연락", "상담", "신고",
                "언제", "몇시", "시간", "끝나", "시작", "개학", "방학",
                "어디", "위치", "장소", "보관함", "교실", "반", "행정실"
            ],
            "인사": [
                "안녕", "안녕하세요", "안녕하십니까", "반갑", "고마워", "감사",
                "잘가", "잘 있어", "재미있어", "좋아", "싫어"
            ]
        }
    
    def detect(self, user_input: str) -> str:
        """
        사용자 입력의 의도를 파악합니다.
        
        Args:
            user_input (str): 사용자 입력 메시지
            
        Returns:
            str: 의도 ("급식", "질문", "인사", "일반")
        """
        user_input = user_input.lower().strip()
        
        # 각 의도별로 키워드 매칭
        for intent, keywords in self.intent_keywords.items():
            if any(keyword in user_input for keyword in keywords):
                return intent
        
        # 매칭되는 의도가 없으면 "일반" 반환
        return "일반"
    
    def get_confidence_score(self, user_input: str, intent: str) -> float:
        """
        의도 파악의 신뢰도를 계산합니다.
        
        Args:
            user_input (str): 사용자 입력 메시지
            intent (str): 파악된 의도
            
        Returns:
            float: 신뢰도 점수 (0.0 ~ 1.0)
        """
        user_input = user_input.lower().strip()
        
        if intent not in self.intent_keywords:
            return 0.0
        
        keywords = self.intent_keywords[intent]
        matched_keywords = [kw for kw in keywords if kw in user_input]
        
        # 매칭된 키워드 수 / 전체 키워드 수
        confidence = len(matched_keywords) / len(keywords)
        
        # 최소 신뢰도 보장
        return max(confidence, 0.1) 