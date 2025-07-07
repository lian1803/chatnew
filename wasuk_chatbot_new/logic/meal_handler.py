import sqlite3
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List

class MealHandler:
    """급식 정보 처리 클래스"""
    
    def __init__(self, db_path: str = '../school_data.db'):
        self.db_path = db_path
    
    def get_meal_info(self, user_input: str = "") -> str:
        """
        급식 정보를 조회합니다.
        
        Args:
            user_input (str): 사용자 입력 메시지 (날짜 추출용)
            
        Returns:
            str: 급식 정보 텍스트
        """
        # 날짜 추출
        target_date = self._extract_date(user_input)
        
        if not target_date:
            target_date = datetime.now().strftime("%Y-%m-%d")
        
        # 주말 체크
        weekday = datetime.strptime(target_date, "%Y-%m-%d").weekday()
        if weekday >= 5:  # 토요일(5), 일요일(6)
            return f"{target_date}는 주말(토/일)이라 급식이 없습니다."
        
        # DB에서 급식 정보 조회
        meal_info = self._get_meal_from_db(target_date)
        
        if meal_info:
            return self._format_meal_info(target_date, meal_info)
        else:
            return f"{target_date}에는 식단 정보가 없습니다."
    
    def _extract_date(self, user_input: str) -> Optional[str]:
        """사용자 입력에서 날짜를 추출합니다."""
        today = datetime.now()
        user_input = user_input.lower()
        
        # 키워드 기반 날짜 추출
        if "오늘" in user_input:
            return today.strftime("%Y-%m-%d")
        elif "내일" in user_input:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "어제" in user_input:
            return (today - timedelta(days=1)).strftime("%Y-%m-%d")
        elif "모레" in user_input:
            return (today + timedelta(days=2)).strftime("%Y-%m-%d")
        elif "글피" in user_input:
            return (today + timedelta(days=3)).strftime("%Y-%m-%d")
        
        # 패턴 기반 날짜 추출
        # "5월 20일", "5/20" 같은 패턴
        match = re.search(r'(\d{1,2})[월/\s](\d{1,2})일?', user_input)
        if match:
            month, day = map(int, match.groups())
            # 올해 날짜로 가정
            try:
                return today.replace(month=month, day=day).strftime("%Y-%m-%d")
            except ValueError:
                pass
        
        # "월요일", "화요일" 같은 패턴
        weekday_map = {
            "월요일": 0, "화요일": 1, "수요일": 2, "목요일": 3, "금요일": 4,
            "토요일": 5, "일요일": 6
        }
        
        for weekday_name, weekday_num in weekday_map.items():
            if weekday_name in user_input:
                # 이번 주 해당 요일 계산
                current_weekday = today.weekday()
                days_diff = weekday_num - current_weekday
                target_date = today + timedelta(days=days_diff)
                return target_date.strftime("%Y-%m-%d")
        
        return None
    
    def _get_meal_from_db(self, date: str) -> Optional[str]:
        """DB에서 특정 날짜의 급식 정보를 가져옵니다."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 중식 정보 조회 (기본적으로 중식만 제공)
            cursor.execute(
                'SELECT menu FROM meals WHERE date = ? AND meal_type = "중식"', 
                (date,)
            )
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            print(f"급식 정보 조회 중 오류: {e}")
            return None
    
    def _format_meal_info(self, date: str, menu: str) -> str:
        """급식 정보를 포맷팅합니다."""
        # 날짜를 한국어로 변환
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        weekday_names = ["월", "화", "수", "목", "금", "토", "일"]
        weekday = weekday_names[date_obj.weekday()]
        
        formatted_date = f"{date_obj.month}월 {date_obj.day}일 ({weekday}요일)"
        
        return f"📅 {formatted_date} 중식 메뉴입니다:\n\n🍽️ {menu}"
    
    def get_weekly_meal_info(self) -> str:
        """이번 주 급식 정보를 조회합니다."""
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        
        weekly_meals = []
        
        for i in range(5):  # 월~금
            date = monday + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            meal_info = self._get_meal_from_db(date_str)
            if meal_info:
                weekday_names = ["월", "화", "수", "목", "금"]
                weekday = weekday_names[i]
                weekly_meals.append(f"📅 {date.month}월 {date.day}일 ({weekday}요일)\n🍽️ {meal_info}")
            else:
                weekday_names = ["월", "화", "수", "목", "금"]
                weekday = weekday_names[i]
                weekly_meals.append(f"📅 {date.month}월 {date.day}일 ({weekday}요일)\n🍽️ 급식 정보 없음")
        
        return "📋 이번 주 급식 메뉴입니다:\n\n" + "\n\n".join(weekly_meals) 