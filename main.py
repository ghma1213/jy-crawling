from typing import List

import chromedriver_autoinstaller
import time

from openpyxl.workbook import Workbook
from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC


def read_text_file():
    # 현재 작업 디렉토리 기준으로 파일 경로 생성
    file_path = f"./search_keyword.txt"

    # 파일 읽기
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        # 각 줄에서 공백 제거 후 반환
        return [line.strip() for line in lines if line.strip()]
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다.")
        return []
    except Exception as e:
        print(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        return []


def crawling(driver, search_keyword, url, count):
    results = []
    driver.get(f"{url}{search_keyword}")

    # 검색 결과 대기 (최대 10초)
    wait = WebDriverWait(driver, 10)

    # for i in range(count):  # 최대 15번 반복
    print(f"크롤링 중... ({search_keyword} 검색어로 순위 {count}개 가져오는 중)")
    try:
        search_results = wait.until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "tit_wrap"))
        )
        # url_area 요소 찾기
        url_area_elements = wait.until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "url_area"))
        )

        results.extend(make_result(search_results, search_keyword, count, url_area_elements))
    except TimeoutException:
        print("Timed out waiting for the search results.")
    except NoSuchElementException:
        print("No next button found.")
    except StaleElementReferenceException:
        print("StaleElementReferenceException encountered. Retrying...")
        time.sleep(1)  # 요소를 다시 로드하기 위해 잠시 대기
    except Exception as e:
        print(f"An error occurred: {e}")

    return results


def make_excel(crawls, type, search_keyword):
    # 새 워크북 생성
    wb = Workbook()
    ws = wb.active
    ws.title = "Crawls Data"

    # 헤더 작성
    ws.append(["Index", "Type", "Keyword", "Title", "Name", "URL"])  # 적절한 필드 추가
    # 각 Crawls 객체의 데이터를 워크시트에 추가
    for index, crawl in enumerate(crawls, 1):
        ws.append([index, type, crawl['keyword'], crawl['title'], crawl['name'], crawl['url']])  # 적절한 필드 사용

    # 엑셀 파일 저장
    wb.save(f"crawls_data_{type}_{search_keyword}.xlsx")


def make_result(search_results, search_keyword, count, url_area_elements):
    results = []

    for result, url_area_elem in zip(search_results, url_area_elements):
        # 'tit_wrap' 안의 모든 span 요소 찾기
        span_elements = result.find_elements(By.TAG_NAME, 'span')

        # 각 span 요소의 텍스트를 가져와 리스트에 추가
        span_texts = " ".join(span.text.strip() for span in span_elements)

        # URL 추출
        href = result.get_attribute("href")
        results.append({
            "html": result.get_attribute('outerHTML'),
            "title": span_texts,
            "name": url_area_elem.text,
            "url": href,
            "keyword": search_keyword
        })


    return results



def main(type, keyword):
    search_keyword = keyword

    # ChromeDriver 자동 설치
    chromedriver_autoinstaller.install()

    # Chrome 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 헤드리스 모드
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # 결과 수집
    results = []
    count = 10
    url = "https://ad.search.naver.com/search.naver?where=ad&query="

    # 웹드라이버 설정
    driver = webdriver.Chrome(options=chrome_options)
    if type == "PC":
        results = crawling(driver, search_keyword, url, count)

    elif type == "M":
        count = 15
        url = "https://m.ad.search.naver.com/search.naver?where=m_expd&query="
        results = crawling(driver, search_keyword, url, count)

    make_excel(results, type, search_keyword)


if __name__ == "__main__":
    text = read_text_file()
    if text:
        for line in text:
            # 각 줄을 콤마로 분리
            parts = line.split(',')
            if len(parts) == 2:  # 형식이 올바른 경우만 처리
                type = parts[0].strip()
                keyword = parts[1].strip()
                main(type, keyword)
            else:
                print(f"잘못된 형식: {line}")
    else:
        print("파일이 비어있거나 읽을 수 없습니다.")

