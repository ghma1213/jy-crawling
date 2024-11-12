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




def make_excel(crawls):
    # 새 워크북 생성
    wb = Workbook()
    ws = wb.active
    ws.title = "Crawls Data"

    # 헤더 작성
    ws.append(["Index", "Keyword", "Title", "URL"])  # 적절한 필드 추가
    # 각 Crawls 객체의 데이터를 워크시트에 추가
    for index, crawl in enumerate(crawls, 1):
        ws.append([index, crawl['keyword'], crawl['title'], crawl['url']])  # 적절한 필드 사용

    # 엑셀 파일 저장
    wb.save("crawls_data.xlsx")


def make_result(search_results, search_keyword):
    results = []
    for result in search_results:
        # 'tit_wrap' 안의 모든 span 요소 찾기
        span_elements = result.find_elements(By.TAG_NAME, 'span')

        # 각 span 요소의 텍스트를 가져와 리스트에 추가
        span_texts = " ".join(span.text.strip() for span in span_elements)

        # URL 추출
        href = result.get_attribute("href")
        results.append({
            "html": result.get_attribute('outerHTML'),
            "title": span_texts,
            "url": href,
            "keyword": search_keyword
        })

    return results



def main():
    search_keyword = input("검색어를 입력하세요: ")

    # ChromeDriver 자동 설치
    chromedriver_autoinstaller.install()

    # Chrome 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 헤드리스 모드
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # 웹드라이버 설정
    driver = webdriver.Chrome(options=chrome_options)

    driver.get(f"https://ad.search.naver.com/search.naver?where=ad&query={search_keyword}")

    # 검색 결과 대기 (최대 10초)
    wait = WebDriverWait(driver, 10)

    # 결과 수집
    results = []
    search_results = []


    while True:
        print("크롤링 중...")
        try:
            # 'paginate' 요소를 찾습니다.
            paginate = driver.find_element(By.CLASS_NAME, 'paginate')

            if paginate:
                next_button = paginate.find_element(By.CLASS_NAME, 'next')

                # href 속성 가져오기
                href_value = next_button.get_attribute('href')

                # next 버튼이 있는 경우 처리
                if href_value:
                    search_results = wait.until(
                        EC.presence_of_all_elements_located((By.CLASS_NAME, "tit_wrap"))
                    )
                    results.extend(make_result(search_results, search_keyword))

                    next_button.click()  # 버튼 클릭
                    time.sleep(2)  # 페이지 로드 대기 (필요에 따라 조정)

                else:
                    print("Next button does not have an href attribute.")
                    search_results = wait.until(
                        EC.presence_of_all_elements_located((By.CLASS_NAME, "tit_wrap"))
                    )
                    results.extend(make_result(search_results, search_keyword))
                    break
            else:
                print("Pagination element not found.")
                break
        except TimeoutException:
            print("Timed out waiting for the search results.")
            break
        except NoSuchElementException:
            print("No next button found.")
            break  # 'next' 버튼이 없으면 루프 종료
        except StaleElementReferenceException:
            print("StaleElementReferenceException encountered. Retrying...")
            time.sleep(1)  # 요소를 다시 로드하기 위해 잠시 대기
            continue  # 루프 반복하여 재시도
        except Exception as e:
            print(f"An error occurred: {e}")
            break

    make_excel(results)



if __name__ == "__main__":
    main()