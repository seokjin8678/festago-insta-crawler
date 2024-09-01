import time
from datetime import datetime
from time import sleep

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

from const.filtering_words import filtering_words

driver = webdriver.Chrome()


def login(username, password):
  driver.get('https://www.instagram.com')
  driver.implicitly_wait(2)

  username_input = driver.find_element(
      by=By.CSS_SELECTOR,
      value='input[name="username"]'
  )
  username_input.send_keys(username)

  password_input = driver.find_element(
      by=By.CSS_SELECTOR,
      value='input[name="password"]'
  )
  password_input.send_keys(password)

  login_button = driver.find_element(by=By.CSS_SELECTOR, value='._acap')
  login_button.send_keys(Keys.ENTER)
  time.sleep(8)


def move_to_first_post(account_id: str):
  driver.get(f'https://www.instagram.com/{account_id}')
  driver.implicitly_wait(5)
  try:
    first_post = driver.find_element(by=By.CSS_SELECTOR, value='._aagw')
  except NoSuchElementException:
    raise Exception(f'{account_id} 계정에 게시글이 존재하지 않습니다.')
  first_post.click()
  driver.implicitly_wait(1)


def get_pinned_post_count():
  svgs = driver.find_elements(by=By.TAG_NAME, value='svg')
  return len(list(filter(lambda svg: svg.get_attribute('aria-label') == '고정 게시물', svgs)))


def extract_post_id() -> str:
  post_url = driver.current_url
  start_index = post_url.find('/p/') + 3
  end_index = post_url.find('/', start_index)
  return post_url[start_index:end_index]


def move_to_next_post():
  driver.find_element(
      by=By.CSS_SELECTOR,
      value='._aaqg'
  ).find_element(
      by=By.CSS_SELECTOR,
      value='._abl-'
  ).click()
  sleep(0.2)


def is_festival_post() -> bool:
  try:
    post_text = driver.find_element(by=By.TAG_NAME, value='h1').text
  except NoSuchElementException:
    return False
  for filtering_word in filtering_words:
    if filtering_word in post_text:
      return True
  return False


def extract_posted_at() -> datetime:
  datetime_element = driver.find_element(by=By.CSS_SELECTOR, value='.x1p4m5qa')
  date_str = datetime_element.get_attribute("datetime")
  return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')


def get_image_url(post_url):
  driver.get(post_url)
  driver.implicitly_wait(5)
  return (driver.find_element(by=By.CSS_SELECTOR, value='._aagu')
          .find_element(by=By.TAG_NAME, value='img')
          .get_attribute('src'))
