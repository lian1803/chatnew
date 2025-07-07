from flask import Flask, request, jsonify
import os
from logic.wasuk_bot_logic import WasukBotLogic

app = Flask(__name__)

# 챗봇 로직 초기화
bot_logic = WasukBotLogic()

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    카카오톡 챗봇 웹훅 엔드포인트
    """
    try:
        # 요청 데이터 파싱
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "요청 데이터가 없습니다."}), 400
        
        # 사용자 메시지 추출
        user_message = data.get('userRequest', {}).get('utterance', '')
        user_id = data.get('userRequest', {}).get('user', {}).get('id', 'default')
        
        if not user_message:
            return jsonify({"error": "사용자 메시지가 없습니다."}), 400
        
        print(f"사용자 ID: {user_id}")
        print(f"사용자 메시지: {user_message}")
        
        # 챗봇 로직으로 메시지 처리
        response = bot_logic.process_message(user_message, user_id)
        
        print(f"챗봇 응답: {response}")
        
        return jsonify(response)
        
    except Exception as e:
        print(f"웹훅 처리 중 오류: {e}")
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "죄송합니다. 시스템에 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
                        }
                    }
                ]
            }
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({
        "status": "healthy",
        "service": "wasuk_chatbot",
        "version": "2.0"
    })

@app.route('/', methods=['GET'])
def home():
    """홈페이지"""
    return """
    <html>
    <head>
        <title>파주와석초등학교 챗봇</title>
        <meta charset="utf-8">
        <style>
            body { 
                font-family: Arial, sans-serif; 
                max-width: 800px; 
                margin: 0 auto; 
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { color: #2c3e50; text-align: center; }
            .status { 
                background: #e8f5e8; 
                padding: 15px; 
                border-radius: 5px; 
                margin: 20px 0;
                border-left: 4px solid #27ae60;
            }
            .endpoint {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🍎 파주와석초등학교 챗봇</h1>
            
            <div class="status">
                <strong>✅ 서버 상태:</strong> 정상 운영 중
            </div>
            
            <h2>📋 API 엔드포인트</h2>
            
            <div class="endpoint">
                <strong>POST /webhook</strong><br>
                카카오톡 챗봇 메시지 처리
            </div>
            
            <div class="endpoint">
                <strong>GET /health</strong><br>
                서버 상태 확인
            </div>
            
            <h2>🔧 주요 기능</h2>
            <ul>
                <li>급식 정보 조회</li>
                <li>학교 관련 질문 답변</li>
                <li>AI 기반 대화</li>
                <li>사용자별 대화 기록 관리</li>
            </ul>
            
            <h2>📊 시스템 정보</h2>
            <ul>
                <li><strong>버전:</strong> 2.0 (모듈화 개선)</li>
                <li><strong>구조:</strong> Flask + 모듈화된 로직</li>
                <li><strong>데이터베이스:</strong> SQLite</li>
                <li><strong>AI:</strong> OpenAI GPT-3.5</li>
            </ul>
        </div>
    </body>
    </html>
    """

@app.route('/test', methods=['POST'])
def test_chat():
    """
    테스트용 채팅 엔드포인트
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({"error": "메시지가 없습니다."}), 400
        
        # 챗봇 로직으로 메시지 처리
        response = bot_logic.process_message(user_message, "test_user")
        
        return jsonify({
            "user_message": user_message,
            "bot_response": response
        })
        
    except Exception as e:
        print(f"테스트 채팅 중 오류: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # 환경 변수 확인
    if not os.environ.get('OPENAI_API_KEY'):
        print("⚠️  경고: OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("   AI 응답 기능이 제한됩니다.")
    
    # 서버 시작
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"🚀 와석초 챗봇 서버 시작 중...")
    print(f"   포트: {port}")
    print(f"   디버그 모드: {debug}")
    print(f"   웹훅 URL: http://localhost:{port}/webhook")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 