import sqlite3
import re
from typing import Optional, Dict, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class QAHandler:
    """QA 데이터베이스 처리 클래스"""
    
    def __init__(self, db_path: str = '../school_data.db'):
        self.db_path = db_path
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=None,
            ngram_range=(1, 2)
        )
        self.qa_vectors = None
        self.qa_data = []
        self._load_qa_data()
    
    def _load_qa_data(self):
        """QA 데이터를 로드하고 벡터화합니다."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT question, answer, additional_answer, category FROM qa_data')
            self.qa_data = cursor.fetchall()
            conn.close()
            
            if self.qa_data:
                # 질문들을 벡터화
                questions = [qa[0] for qa in self.qa_data]
                self.qa_vectors = self.vectorizer.fit_transform(questions)
                
        except Exception as e:
            print(f"QA 데이터 로드 중 오류: {e}")
            self.qa_data = []
            self.qa_vectors = None
    
    def get_answer(self, user_input: str) -> str:
        """
        사용자 입력에 대한 답변을 찾습니다.
        
        Args:
            user_input (str): 사용자 입력 메시지
            
        Returns:
            str: 답변 텍스트
        """
        if not self.qa_data:
            return "죄송합니다. 현재 QA 데이터를 불러올 수 없습니다."
        
        # 1. 정확한 매칭 시도
        exact_match = self._find_exact_match(user_input)
        if exact_match:
            return self._format_answer(exact_match)
        
        # 2. 유사도 기반 검색
        similar_match = self._find_similar_match(user_input)
        if similar_match:
            return self._format_answer(similar_match)
        
        # 3. 키워드 기반 검색
        keyword_match = self._find_keyword_match(user_input)
        if keyword_match:
            return self._format_answer(keyword_match)
        
        return "죄송합니다. 해당 질문에 대한 답변을 찾을 수 없습니다. 학교로 문의해 주세요."
    
    def _find_exact_match(self, user_input: str) -> Optional[tuple]:
        """정확한 매칭을 찾습니다."""
        user_input = user_input.lower().strip()
        
        for qa in self.qa_data:
            question = qa[0].lower().strip()
            if user_input == question:
                return qa
        
        return None
    
    def _find_similar_match(self, user_input: str, threshold: float = 0.3) -> Optional[tuple]:
        """유사도 기반 매칭을 찾습니다."""
        if self.qa_vectors is None:
            return None
        
        try:
            # 사용자 입력을 벡터화
            user_vector = self.vectorizer.transform([user_input])
            
            # 유사도 계산
            similarities = cosine_similarity(user_vector, self.qa_vectors).flatten()
            
            # 가장 유사한 답변 찾기
            best_idx = np.argmax(similarities)
            best_similarity = similarities[best_idx]
            
            if best_similarity >= threshold:
                return self.qa_data[best_idx]
            
        except Exception as e:
            print(f"유사도 계산 중 오류: {e}")
        
        return None
    
    def _find_keyword_match(self, user_input: str) -> Optional[tuple]:
        """키워드 기반 매칭을 찾습니다."""
        user_input = user_input.lower().strip()
        
        # 사용자 입력에서 키워드 추출
        keywords = self._extract_keywords(user_input)
        
        best_match = None
        best_score = 0
        
        for qa in self.qa_data:
            question = qa[0].lower()
            answer = qa[1].lower()
            
            # 키워드 매칭 점수 계산
            score = 0
            for keyword in keywords:
                if keyword in question:
                    score += 2  # 질문에 키워드가 있으면 높은 점수
                if keyword in answer:
                    score += 1  # 답변에 키워드가 있으면 낮은 점수
            
            if score > best_score:
                best_score = score
                best_match = qa
        
        # 최소 점수 이상일 때만 반환
        if best_score >= 2:
            return best_match
        
        return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """텍스트에서 키워드를 추출합니다."""
        # 한글, 영문, 숫자만 추출
        keywords = re.findall(r'[가-힣a-zA-Z0-9]+', text)
        
        # 2글자 이상만 필터링
        keywords = [kw for kw in keywords if len(kw) >= 2]
        
        # 불용어 제거
        stop_words = {'이', '가', '을', '를', '은', '는', '에', '에서', '로', '으로', '와', '과', '도', '만', '의', '것', '수', '등', '등등'}
        keywords = [kw for kw in keywords if kw not in stop_words]
        
        return keywords
    
    def _format_answer(self, qa: tuple) -> str:
        """답변을 포맷팅합니다."""
        question, answer, additional_answer, category = qa
        
        formatted_answer = answer
        
        # 추가 답변이 있으면 추가
        if additional_answer and additional_answer.strip():
            formatted_answer += f"\n\n{additional_answer}"
        
        return formatted_answer 