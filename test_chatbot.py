#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
와석초 챗봇 테스트 스크립트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic.wasuk_bot_logic import WasukBotLogic

def test_chatbot():
    """챗봇 테스트 함수"""
    
    print("🍎 와석초 챗봇 테스트 시작")
    print("=" * 50)
    
    # 챗봇 초기화
    try:
        bot = WasukBotLogic()
        print("✅ 챗봇 초기화 성공")
    except Exception as e:
        print(f"❌ 챗봇 초기화 실패: {e}")
        return
    
    # 테스트 케이스들
    test_cases = [
        "전학가고 싶은데",
        "오늘 급식 뭐야?",
        "안녕하세요",
        "내일 급식 알려줘",
        "학교 규칙 알려줘",
        "방과후 프로그램은 어떻게 신청하나요?",
        "고마워요",
        "이번 주 급식 메뉴 알려줘"
    ]
    
    for i, test_message in enumerate(test_cases, 1):
        print(f"\n📝 테스트 {i}: '{test_message}'")
        print("-" * 30)
        
        try:
            # 챗봇 응답 생성
            response = bot.process_message(test_message, "test_user")
            
            # 응답 출력
            if isinstance(response, dict) and 'template' in response:
                text_output = response['template']['outputs'][0]['simpleText']['text']
                print(f"🤖 챗봇 응답: {text_output}")
                
                # 퀵리플라이 출력
                if 'quickReplies' in response['template']:
                    quick_replies = response['template']['quickReplies']
                    if quick_replies:
                        print("🔘 퀵리플라이:")
                        for qr in quick_replies:
                            print(f"   - {qr['label']}: {qr['messageText']}")
            else:
                print(f"🤖 챗봇 응답: {response}")
                
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
    
    print("\n" + "=" * 50)
    print("✅ 테스트 완료!")

if __name__ == "__main__":
    test_chatbot() 