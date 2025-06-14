# === 1. 라이브러리 임포트 ===
# 필요한 외부 기능들을 가져오는 부분

import time  # 시간 관련 함수를 사용하기 위함 (예: time.sleep()으로 잠시 멈춤)
import pandas as pd  # 데이터 분석 라이브러리. 여기서는 CSV 저장을 위함
import json # JSON(JavaScript Object Notation) 형식의 데이터를 다루기 위함 (파일 저장/로드)
from selenium import webdriver  # 웹 브라우저 자동화를 위한 핵심 라이브러리
from selenium.webdriver.chrome.service import Service  # ChromeDriver 실행을 관리
from selenium.webdriver.common.by import By  # HTML 요소를 찾는 방법(ID, CSS 선택자 등)을 지정
from selenium.webdriver.support.ui import WebDriverWait  # 웹 드라이버가 특정 조건까지 기다리도록 설정
from selenium.webdriver.support import expected_conditions as EC  # WebDriverWait와 함께 사용되는 조건들
from webdriver_manager.chrome import ChromeDriverManager  # ChromeDriver를 자동으로 관리(설치/업데이트)
from bs4 import BeautifulSoup  # HTML/XML 문서에서 데이터를 추출(파싱)하기 쉽게 만듦
import re  # 정규 표현식(문자열 패턴 검색/치환)을 사용하기 위함
import traceback  # 예외(에러) 발생 시 상세한 호출 스택 정보를 얻기 위함

# === 2. 상세 페이지 내용 크롤링 함수: crawl_detail_page ===
# 이 함수는 하나의 상세 정보 페이지 URL을 받아 해당 페이지의 본문 내용을 추출함

def crawl_detail_page(detail_url, driver):
    # 어떤 상세 페이지를 크롤링 중인지 화면에 표시
    print(f"  Crawling detail page: {detail_url}")
    try:
        # 1. WebDriver로 상세 페이지 URL 접속
        driver.get(detail_url)
        # 2. WebDriverWait 객체 생성: 최대 20초까지 기다림
        wait = WebDriverWait(driver, 20)
        
        # 3. 상세 내용이 담긴 HTML 요소의 CSS 선택자 정의
        #    첫 번째 시도: 좀 더 구체적인 선택자 (예: <div id="content"> 안의 <div class="healthCont">)
        content_container_selector = "div#content div.healthCont" 
        try:
            #    선택한 요소가 나타날 때까지 기다림
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, content_container_selector)))
        except: # 만약 첫 번째 시도에서 요소를 못 찾으면 (TimeoutException 등 발생)
            #    두 번째 시도: 좀 더 일반적인 선택자 (예: <div id="content">)
            content_container_selector = "div#content" 
            print(f"    Fallback: Waiting for {content_container_selector}") # 대체 시도 알림
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, content_container_selector)))

        # 4. 현재 페이지의 HTML 소스 가져오기
        detail_page_source = driver.page_source
        # 5. BeautifulSoup으로 HTML 파싱
        detail_soup = BeautifulSoup(detail_page_source, 'html.parser')
        # 6. 파싱된 HTML에서 내용 컨테이너 요소 찾기
        content_div = detail_soup.select_one(content_container_selector)
        
        if content_div: # 내용 컨테이너를 찾았다면
            # 7. (선택적) 불필요한 내부 요소 제거: 예시로 LNB(좌측 내비게이션 바) 제거
            #    실제 상세 페이지 구조를 보고 RAG에 불필요한 부분을 제거하면 내용이 깔끔해짐
            lnb_div = content_div.select_one("div#lnb") 
            if lnb_div:
                lnb_div.decompose() # 해당 요소를 DOM 트리에서 제거

            # 8. 내용 텍스트 추출 및 정제
            #    get_text(): 모든 텍스트 추출, separator='\n'은 태그 사이에 줄바꿈 추가, strip=True는 앞뒤 공백 제거
            raw_text = content_div.get_text(separator='\n', strip=True)
            #    re.sub(): 정규 표현식으로 불필요한 연속 줄바꿈을 하나로 합치고, 전체 텍스트의 앞뒤 공백 제거
            cleaned_text = re.sub(r'\n\s*\n', '\n', raw_text).strip()
            return cleaned_text # 정제된 텍스트 반환
        else: # 내용 컨테이너를 못 찾았다면
            print(f"  Could not find content div ({content_container_selector}) on: {detail_url}")
            return "Content not found." # 내용 없음 메시지 반환
            
    except Exception as e: # 상세 페이지 크롤링 중 다른 에러 발생 시
        print(f"  Error crawling detail page {detail_url}: {e}")
        return "Error fetching content." # 에러 메시지 반환

# === 3. 메인 크롤링 함수: crawl_amc_health_info ===
# 특정 부위(partId)의 목록 페이지부터 시작하여 각 항목의 상세 정보까지 크롤링합니다.
# category_name은 JSON 메타데이터에 저장될 카테고리 이름입니다.

def crawl_amc_health_info(part_id="B000020", category_name="가슴"):
    # 1. 크롤링 대상 URL 설정
    base_url = "https://www.amc.seoul.kr/asan/healthinfo/management/managementList.do"
    target_url = f"{base_url}?partId={part_id}#" # #은 페이지 내 특정 위치로 이동하는 것을 의미하지만, 여기서는 큰 영향 없음

    # 2. Selenium WebDriver 옵션 설정
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # 브라우저 창 없이 백그라운드 실행 (테스트 완료 후 사용)
    options.add_argument("--no-sandbox") # 리눅스/Docker 환경에서 headless 사용 시 필요
    options.add_argument("--disable-dev-shm-usage") # 리눅스/Docker 환경에서 /dev/shm 파티션 관련 문제 방지
    options.add_argument("window-size=1920,1080") # 브라우저 창 크기 (headless에서도 영향 줄 수 있음)
    # User-Agent 설정: 웹 서버에 일반 사용자로 보이도록 함
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36")
    options.add_experimental_option('excludeSwitches', ['enable-logging']) # 불필요한 콘솔 로그 줄임

    # 3. WebDriver 인스턴스 생성
    #    ChromeDriverManager().install(): ChromeDriver 자동 다운로드 및 경로 설정
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    rag_documents = [] # RAG 형식으로 변환된 최종 데이터를 담을 리스트
    list_items_to_process = [] # 목록에서 수집한 임시 데이터(제목, 링크)를 담을 리스트
    current_page = 1 # 현재 처리 중인 목록 페이지 번호

    print(f"Target URL: {target_url}")
    print(f"Crawling Part ID: {part_id} (Category: {category_name})")

    try: # 전체 크롤링 과정을 try-except로 감싸 예외 처리
        # 4. 목록 페이지의 첫 페이지로 이동
        driver.get(target_url)
        # WebDriverWait 객체 생성: 목록 페이지 요소 로드를 위해 최대 30초 기다림
        list_wait = WebDriverWait(driver, 30) 

        # --- 1단계: 목록 페이지 순회하며 링크 수집 ---
        while True: # 다음 페이지가 없을 때까지 반복
            print(f"Scraping list page: {current_page}")
            page_loaded_successfully = False # 페이지 로드 성공 여부 플래그
            try:
                # 5. 목록의 각 항목(li)들이 나타날 때까지 기다림
                #    CSS 선택자: <div class="listTypeSec6"> 안의 <ul class="descBoxBody"> 바로 아래 <li>
                print("  Waiting for list items (div.listTypeSec6 ul.descBoxBody > li)...")
                list_wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.listTypeSec6 ul.descBoxBody > li")))
                print("  List items found.")
                page_loaded_successfully = True
            except Exception as e: # 기다리다 예외 발생 (주로 TimeoutException)
                print(f"  Timeout or error waiting for list page {current_page} content: {e}")
                # 디버깅 위해 현재 페이지 HTML 저장
                with open(f"debug_list_page_timeout_part_{part_id}_page_{current_page}.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print(f"  Saved debug page source to debug_list_page_timeout_part_{part_id}_page_{current_page}.html")
                if current_page == 1: # 첫 페이지 로드 실패 시
                    print("  Failed to load content on the first page. Aborting.")
                    driver.quit() # 드라이버 종료
                    return [] # 빈 리스트 반환하고 함수 종료
                break # 현재 페이지 처리 실패, 목록 수집 중단

            if not page_loaded_successfully: # (이중 안전장치)
                break

            # 6. 현재 페이지 HTML 가져와서 BeautifulSoup으로 파싱
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # 7. 목록을 담고 있는 <ul> 태그 찾기
            content_list_ul = soup.select_one("div.listTypeSec6 ul.descBoxBody")
            if not content_list_ul: # <ul> 못 찾으면
                # ... (디버깅용 HTML 저장 및 메시지 출력) ...
                break # 목록 수집 중단

            # 8. <ul> 안의 모든 <li> (항목)들 찾기
            items = content_list_ul.select("li") 
            if not items: # <li> 못 찾으면
                # ... (디버깅용 HTML 저장 및 메시지 출력) ...
                break # 목록 수집 중단 (마지막 페이지일 수도)
            
            # 9. 각 <li> 항목 정보 추출
            for item_li in items:
                #    제목과 링크가 있는 <a> 태그 찾기
                title_anchor = item_li.select_one("div.contBox > strong.contTitle > a")
                if title_anchor: 
                    title = title_anchor.get_text(strip=True) # 제목 텍스트
                    detail_page_link = title_anchor.get("href") # 상세 페이지 링크
                    # 상대 경로면 절대 경로로 변환
                    if detail_page_link and not detail_page_link.startswith("http"):
                        detail_page_link = "https://www.amc.seoul.kr" + detail_page_link
                    
                    date_text = "N/A" # 이 페이지 목록에는 날짜 정보가 없으므로 N/A

                    # 임시 리스트에 저장
                    list_items_to_process.append({
                        "list_title": title,
                        "list_date": date_text,
                        "detail_page_link": detail_page_link,
                    })
                else: # 제목 <a> 태그 못 찾으면 오류 메시지
                    print(f"    Could not find title_anchor ... in item on page {current_page}. Item HTML: {str(item_li)[:200]}")

            print(f"  Collected {len(items)} item links from list page {current_page}.") 

            # --- 10. 다음 페이지로 이동 (페이지네이션) ---
            try:
                # 페이지네이션 영역 찾기
                pagination_container = driver.find_element(By.CSS_SELECTOR, "div.pagingWrapSec")
                # 현재 페이지 번호 표시하는 링크 찾기 (class="nowPage")
                current_page_indicator = pagination_container.find_element(By.CSS_SELECTOR, "a.nowPage")
                current_page_number_text = current_page_indicator.text.strip()
                
                # 다음 페이지로 갈 수 있는 모든 링크 후보 찾기 (숫자 페이지, "이전", "다음" 버튼 등)
                possible_next_page_links = pagination_container.find_elements(By.CSS_SELECTOR, "span.numPagingSec a, span.btnPagingSec a") 
                
                found_and_clicked_next_page = False # 다음 페이지 이동 성공 여부 플래그
                for link in possible_next_page_links:
                    link_text = link.text.strip()
                    # "다음" 버튼/링크 우선 확인 (텍스트 또는 class 속성)
                    if "다음" in link_text or (link.get_attribute("class") and "next" in link.get_attribute("class")):
                        # 비활성화된(disabled) 버튼은 클릭하지 않음
                        if not (link.get_attribute("class") and "disabled" in link.get_attribute("class")):
                            print(f"  Clicking '다음' button/link.")
                            driver.execute_script("arguments[0].click();", link) # JavaScript로 클릭
                            current_page += 1 # 현재 처리 중인 페이지 번호 (단순 카운터)
                            time.sleep(2.5) # 페이지 로드 대기
                            found_and_clicked_next_page = True
                            break # 다음 페이지로 갔으므로 내부 for 루프 탈출
                    # "다음" 버튼 없으면, 현재 페이지 번호보다 큰 숫자 페이지 링크 찾기
                    elif link_text.isdigit(): # 링크 텍스트가 숫자인지 확인
                        if int(link_text) > int(current_page_number_text):
                            print(f"  Clicking next page number link: {link_text}")
                            driver.execute_script("arguments[0].click();", link)
                            current_page += 1
                            time.sleep(2.5)
                            found_and_clicked_next_page = True
                            break
                
                if not found_and_clicked_next_page: # 다음으로 이동할 페이지가 없으면
                    print(f"  No more next page links found after page {current_page_number_text}. Reached the end of list pages.")
                    break # while 루프 탈출 (목록 수집 종료)

            except Exception as e_page: # 페이지네이션 중 에러 발생 시
                print(f"  Reached the end of list pages or 'next' button/link issue on page {current_page}. Error: {e_page}")
                break # while 루프 탈출
        
        # --- 2단계: 수집된 링크들의 상세 페이지 방문 및 RAG 형식으로 저장 ---
        print(f"\nCollected {len(list_items_to_process)} item links in total. Now fetching details for RAG...")
        # 임시 저장된 각 항목에 대해 반복
        for i, info_item in enumerate(list_items_to_process):
            print(f"Processing detail for RAG item {i+1}/{len(list_items_to_process)}: {info_item['list_title'][:50]}")
            # 상세 페이지 링크 유효성 검사
            if info_item["detail_page_link"] and info_item["detail_page_link"].startswith("http"):
                # 상세 페이지 내용 크롤링 함수 호출
                detail_content = crawl_detail_page(info_item["detail_page_link"], driver)
                
                # RAG 형식의 JSON 객체 생성
                rag_document = {
                    "content": detail_content if detail_content else "Content not found or error fetching.", # 상세 내용
                    "metadata": { # 메타데이터
                        "title": info_item["list_title"], # 제목
                        "source_url": info_item["detail_page_link"], # 출처 URL
                        "category": category_name, # 카테고리 이름 (함수 파라미터로 받음)
                        "publish_date": info_item["list_date"] # 날짜 (현재는 "N/A")
                    }
                }
                rag_documents.append(rag_document) # 최종 리스트에 추가
                time.sleep(1.2) # 서버 부하 감소를 위해 잠시 대기
            else: # 링크가 유효하지 않으면
                print(f"  Skipping RAG item with invalid or missing detail_page_link: {info_item['list_title']}")
                # 빈 내용으로 RAG 문서 구조만 유지하며 추가
                rag_documents.append({
                    "content": "Detail link was invalid or missing.",
                    "metadata": {
                        "title": info_item["list_title"],
                        "source_url": info_item["detail_page_link"] if info_item["detail_page_link"] else "N/A",
                        "category": category_name,
                        "publish_date": info_item["list_date"]
                    }
                })
            
    except Exception as e_main: # 메인 크롤링 과정에서 예측 못한 에러 발생 시
        print(f"An critical error occurred during crawling process: {e_main}")
        traceback.print_exc() # 에러 상세 정보 출력
    finally: # try 블록이 끝나거나 에러로 빠져나갈 때 항상 실행
        print("Quitting WebDriver.")
        driver.quit() # WebDriver 종료 (브라우저 닫기)

    return rag_documents # 최종 수집된 RAG 문서 리스트 반환

# === 4. 스크립트 실행 부분 (if __name__ == "__main__":) ===
# 이 파이썬 파일이 직접 실행될 때만 이 블록 안의 코드가 동작합니다.
# (다른 파일에서 이 파일을 import해서 사용할 때는 실행되지 않음)

if __name__ == "__main__":
    # 1. 크롤링할 카테고리 목록 정의
    #    각 카테고리는 딕셔너리 형태로 'partId'와 'name'(메타데이터용)을 가짐
    #    실제 웹사이트에서 각 부위별 partId를 정확히 확인해야 합니다.
    #    (아래 partId는 예시이며, 실제와 다를 수 있습니다. 웹사이트에서 직접 확인하세요!)
    categories_to_crawl = [
        {"partId": "B000020", "name": "가슴"}, # 이미 작업하신 부분
        {"partId": "B000001", "name": "골반"},
        {"partId": "B000002", "name": "귀"},
        {"partId": "B000003", "name": "기타"}, # "기타" 부위가 있는지 확인 필요
        {"partId": "B000004", "name": "눈"},
        {"partId": "B000005", "name": "다리"},
        {"partId": "B000006", "name": "등/허리"},
        {"partId": "B000007", "name": "머리"},
        {"partId": "B000008", "name": "목"},
        {"partId": "B000009", "name": "발"},
        {"partId": "B000010", "name": "배"},
        {"partId": "B000011", "name": "생식기"},
        {"partId": "B000012", "name": "손"},
        # {"partId": "B000021", "name": "얼굴"}, # 예전에 "가슴" 페이지 HTML에서 보였던 ID
        {"partId": "B000013", "name": "엉덩이"},
        {"partId": "B000014", "name": "유방"}, # "가슴"과 별도인지 확인 필요
        # {"partId": "B000015", "name": "입"},
        {"partId": "B000016", "name": "전신"},
        # {"partId": "B000017", "name": "코"},
        {"partId": "B000018", "name": "팔"},
        # {"partId": "B000019", "name": "피부"}
    ]

    all_rag_data = [] # 모든 카테고리에서 크롤링한 데이터를 합칠 리스트

    # 2. 정의된 각 카테고리에 대해 크롤링 실행
    for category_info in categories_to_crawl:
        part_id_to_crawl = category_info["partId"] 
        category_name_for_metadata = category_info["name"] 
        
        print(f"\n--- Starting crawl for category: {category_name_for_metadata} (Part ID: {part_id_to_crawl}) ---")
        # 메인 크롤링 함수 호출 (partId와 카테고리 이름 전달)
        rag_data_for_category = crawl_amc_health_info(part_id=part_id_to_crawl, category_name=category_name_for_metadata)
        
        if rag_data_for_category: # 현재 카테고리에서 데이터가 수집되었다면
            all_rag_data.extend(rag_data_for_category) # 전체 데이터 리스트에 추가
            print(f"    Successfully crawled {len(rag_data_for_category)} items from '{category_name_for_metadata}'.")
        else:
            print(f"    No data crawled or an error occurred for '{category_name_for_metadata}'.")
            
        print(f"--- Finished crawl for category: {category_name_for_metadata}. Total RAG documents so far: {len(all_rag_data)} ---")
        
        # 여러 카테고리 크롤링 시, 마지막 카테고리가 아니면 잠시 대기 (서버 부하 방지)
        if len(categories_to_crawl) > 1 and category_info != categories_to_crawl[-1]:
            # 대기 시간을 조절할 수 있습니다. 너무 짧으면 서버에 부담을 줄 수 있습니다.
            wait_time = 10 # 예: 10초 대기
            print(f"Waiting for {wait_time} seconds before next category...")
            time.sleep(wait_time) 

    # 3. 수집된 전체 데이터를 JSON 파일로 저장
    if all_rag_data: 
        print(f"\nTotal RAG documents crawled from all categories: {len(all_rag_data)}")
        
        output_filename = "amc_health_info_all_categories_rag_data.json" # 파일 이름 변경
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(all_rag_data, f, ensure_ascii=False, indent=2)
            print(f"RAG data saved to {output_filename}")
        except IOError as e: 
            print(f"Error saving JSON file {output_filename}: {e}")
        except Exception as e: 
            print(f"An unexpected error occurred during JSON saving: {e}")

    else: 
        print("No RAG data crawled from any category.")