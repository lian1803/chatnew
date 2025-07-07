import time
import json
import sqlite3
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
import os
import re

class UnifiedCrawler:
    def __init__(self, db_path='school_data.db'):
        self.db_path = db_path
        self.driver = None
        self.init_db()
    
    def init_db(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 공지사항 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE,
                content TEXT,
                url TEXT,
                created_at TEXT,
                tags TEXT,
                category TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 식단 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                meal_type TEXT,
                menu TEXT,
                image_url TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("데이터베이스 초기화 완료.")
    
    def setup_driver(self):
        """Selenium 드라이버 설정"""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        service = Service()
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(3)
        return self.driver
    
    def get_latest_notice_date(self):
        """DB에서 가장 최신 공지사항 날짜 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT created_at FROM notices ORDER BY created_at DESC LIMIT 1')
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def get_latest_meal_date(self):
        """DB에서 가장 최신 식단 날짜 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT date FROM meals ORDER BY date DESC LIMIT 1')
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def save_notice_to_db(self, notice):
        """공지사항을 DB에 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO notices (title, content, url, created_at, tags, category)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (notice['title'], notice['content'], notice['url'], 
                 notice['created_at'], notice['tags'], notice['category']))
            conn.commit()
            return cursor.rowcount > 0  # 새로 추가된 경우 True
        except Exception as e:
            print(f"공지사항 저장 중 오류: {e}")
            return False
        finally:
            conn.close()
    
    def save_meal_to_db(self, meal):
        """식단을 DB에 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO meals (date, meal_type, menu, image_url)
                VALUES (?, ?, ?, ?)
            ''', (meal['date'], meal['meal_type'], meal['menu'], meal['image_url']))
            conn.commit()
            return cursor.rowcount > 0  # 새로 추가된 경우 True
        except Exception as e:
            print(f"식단 저장 중 오류: {e}")
            return False
        finally:
            conn.close()
    
    def extract_notice_content(self, driver):
        """공지사항 내용 추출"""
        try:
            el = driver.find_element(By.CSS_SELECTOR, "div.bbsV_cont")
            return el.text.strip()
        except Exception:
            return ""
    
    def crawl_notices(self, max_notices=100):
        """공지사항 크롤링"""
        print("\n=== 공지사항 크롤링 시작 ===")
        
        latest_date = self.get_latest_notice_date()
        if latest_date:
            print(f"최신 공지사항 날짜: {latest_date}")
        else:
            print("기존 공지사항이 없습니다. 처음부터 크롤링합니다.")
        
        url = "https://pajuwaseok-e.goepj.kr/pajuwaseok-e/na/ntt/selectNttList.do?mi=8476&bbsId=5794"
        new_notices = 0
        page = 1
        
        while new_notices < max_notices:
            print(f"\n--- 페이지 {page} 처리 중 ---")
            
            if page == 1:
                self.driver.get(url)
            else:
                try:
                    btn = self.driver.find_element(By.CSS_SELECTOR, f"a[onclick*='goPaging({page})']")
                    btn.click()
                    time.sleep(2)
                except Exception as e:
                    print(f"페이지네이션 오류: {e}")
                    break
            
            # 현재 페이지의 모든 링크 가져오기
            links = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr td.ta_l > a")
            print(f"현재 페이지 링크 수: {len(links)}")
            
            page_has_new = False
            for i in range(len(links)):
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr td.ta_l > a")
                    a = links[i]
                    title = a.text.strip()
                    
                    if not title:
                        continue
                    
                    row = a.find_element(By.XPATH, "./ancestor::tr")
                    created_at = row.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text.strip()
                    
                    # 최신 날짜 체크
                    if latest_date and created_at <= latest_date:
                        print(f"기존 데이터 이후: {title[:30]}... (스킵)")
                        continue
                    
                    print(f"새 공지사항 발견: {title[:50]}...")
                    
                    # 상세 페이지로 이동
                    a.click()
                    time.sleep(1)
                    
                    detail_url = self.driver.current_url
                    content = self.extract_notice_content(self.driver)
                    
                    self.driver.back()
                    time.sleep(1)
                    
                    notice = {
                        "title": title,
                        "url": detail_url,
                        "content": content,
                        "created_at": created_at,
                        "tags": title,
                        "category": None
                    }
                    
                    if self.save_notice_to_db(notice):
                        new_notices += 1
                        page_has_new = True
                        print(f"새 공지사항 저장 완료: {new_notices}개")
                    
                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    print(f"공지사항 처리 중 오류: {e}")
                    continue
            
            if not page_has_new:
                print("새 공지사항이 없습니다. 크롤링 종료.")
                break
            
            page += 1
        
        print(f"공지사항 크롤링 완료. 새로 추가된 공지사항: {new_notices}개")
        return new_notices
    
    def extract_weekday_lunch(self, driver):
        """주중 중식 메뉴 추출"""
        results = []
        try:
            date_els = driver.find_elements(By.CSS_SELECTOR, 'thead tr th')[1:]
            dates = [el.text.split('\n')[1] for el in date_els]
            
            for i in range(1, 6):  # 월~금
                menu = ''
                img_url = ''
                
                try:
                    xpath = f'//*[@id="detailForm"]/div/table/tbody/tr[2]/td[{i+1}]/p[4]'
                    menu = driver.find_element(By.XPATH, xpath).text.strip()
                except Exception:
                    pass
                
                try:
                    td_xpath = f'//*[@id="detailForm"]/div/table/tbody/tr[2]/td[{i+1}]'
                    td_html = driver.find_element(By.XPATH, td_xpath).get_attribute('innerHTML')
                    img_match = re.search(r'<img[^>]+src=["\"]([^"\"]+)["\"]', td_html)
                    if img_match:
                        img_url = img_match.group(1)
                except Exception:
                    pass
                
                if menu:  # 메뉴가 있는 경우만 추가
                    results.append({
                        'date': dates[i],
                        'meal_type': '중식',
                        'menu': menu,
                        'image_url': img_url
                    })
        except Exception as e:
            print(f"주중 중식 추출 중 오류: {e}")
        
        return results
    
    def crawl_meals(self, max_weeks=20):
        """식단 크롤링"""
        print("\n=== 식단 크롤링 시작 ===")
        
        latest_date = self.get_latest_meal_date()
        if latest_date:
            print(f"최신 식단 날짜: {latest_date}")
        else:
            print("기존 식단이 없습니다. 처음부터 크롤링합니다.")
        
        url = 'https://pajuwaseok-e.goepj.kr/pajuwaseok-e/ad/fm/foodmenu/selectFoodMenuView.do?mi=8432'
        new_meals = 0
        week_count = 0
        
        try:
            print('[INFO] 식단 페이지 진입 시도')
            self.driver.get(url)
            
            while week_count < max_weeks:
                try:
                    print(f'[INFO] {week_count+1}번째 주 월~금 중식 데이터 수집 시작')
                    week_data = self.extract_weekday_lunch(self.driver)
                    
                    if not week_data:
                        print('[INFO] 더 이상 데이터 없음, 종료')
                        break
                    
                    # 새 데이터만 필터링
                    new_week_data = []
                    for meal in week_data:
                        if not latest_date or meal['date'] > latest_date:
                            new_week_data.append(meal)
                    
                    if new_week_data:
                        for meal in new_week_data:
                            if self.save_meal_to_db(meal):
                                new_meals += 1
                                print(f"새 식단 저장: {meal['date']} - {meal['menu'][:30]}...")
                    else:
                        print("이번 주는 모두 기존 데이터입니다.")
                    
                    # 다음 주로 이동
                    try:
                        date_els = self.driver.find_elements(By.CSS_SELECTOR, 'thead tr th')[1:]
                        prev_dates = [el.text.split('\n')[1] for el in date_els]
                        prev_btn = self.driver.find_element(By.CSS_SELECTOR, 'a:has(i.xi-angle-right)')
                        print('[INFO] 다음주 버튼 클릭')
                        prev_btn.click()
                        WebDriverWait(self.driver, 10).until(
                            lambda d: [el.text.split('\n')[1] for el in d.find_elements(By.CSS_SELECTOR, 'thead tr th')[1:]] != prev_dates
                        )
                        time.sleep(0.5)
                        week_count += 1
                    except NoSuchElementException:
                        print('[WARN] 더 이상 이전주 버튼 없음')
                        break
                        
                except StaleElementReferenceException:
                    print('[WARN] StaleElementReferenceException: 루프에서 발생, 다음 주로 진행')
                    continue
                    
        except Exception as e:
            print(f"[ERROR] 식단 크롤링 중 오류 발생: {str(e)}")
        
        print(f"식단 크롤링 완료. 새로 추가된 식단: {new_meals}개")
        return new_meals
    
    def run_crawler(self, crawl_notices=True, crawl_meals=True, max_notices=100, max_weeks=20):
        """통합 크롤러 실행"""
        print("=== 파주와석초등학교 통합 크롤러 시작 ===")
        print(f"실행 시간: {datetime.now()}")
        
        try:
            self.setup_driver()
            
            total_new_notices = 0
            total_new_meals = 0
            
            if crawl_notices:
                total_new_notices = self.crawl_notices(max_notices)
            
            if crawl_meals:
                total_new_meals = self.crawl_meals(max_weeks)
            
            print(f"\n=== 크롤링 완료 ===")
            print(f"새로 추가된 공지사항: {total_new_notices}개")
            print(f"새로 추가된 식단: {total_new_meals}개")
            print(f"총 추가된 데이터: {total_new_notices + total_new_meals}개")
            
        except Exception as e:
            print(f"크롤링 중 오류 발생: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                print("드라이버 종료 완료")

def main():
    """메인 실행 함수"""
    crawler = UnifiedCrawler()
    
    # 사용자 입력 받기
    print("크롤링 옵션을 선택하세요:")
    print("1. 공지사항만 크롤링")
    print("2. 식단만 크롤링")
    print("3. 모두 크롤링 (기본값)")
    
    choice = input("선택 (1-3, 기본값: 3): ").strip() or "3"
    
    if choice == "1":
        crawler.run_crawler(crawl_notices=True, crawl_meals=False)
    elif choice == "2":
        crawler.run_crawler(crawl_notices=False, crawl_meals=True)
    else:
        crawler.run_crawler(crawl_notices=True, crawl_meals=True)

if __name__ == "__main__":
    main() 