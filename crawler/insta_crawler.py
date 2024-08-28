import time
import logging
from datetime import datetime
from time import sleep
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from api import discord_client
from crawler.filtering_words import filtering_words
from db.entity import InstagramReadHistory

driver = webdriver.Chrome()
logger = logging.getLogger(__name__)


def login(username: str, password: str):
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
  time.sleep(3)


def crawling(insta_account):
  pinned_post_offset_count = 3  # 고정된 게시글 때문에 3번 까지는 읽은 게시글이라도 계속 읽는다.
  account_id = insta_account.id
  logger.info(f'{account_id} 계정 크롤링 시작')

  move_to_first_post(account_id)

  unread_posts = []
  for i in range(pinned_post_offset_count):
    post_id = extract_post_id()
    logger.info(f'게시글 조회 완료 post_id = {post_id}')
    post = (InstagramReadHistory.select()
            .where(InstagramReadHistory.post_id == post_id)
            .get_or_none())
    if post is None:
      unread_posts.append({
        'post_id': post_id,
        'account_id': account_id,
        'is_festival': is_post_festival_post(),
        'posted_at': extract_posted_at()
      })
    move_to_next_post()

  read_post_ids = set(
      map(
          lambda history: history.post_id,
          insta_account.histories
          .select()
          .order_by(InstagramReadHistory.posted_at.desc())
          .limit(30)
      )
  )

  while True:
    post_id = extract_post_id()
    logger.info(f'게시글 조회 완료 post_id = {post_id}')
    if post_id in read_post_ids:
      break

    unread_posts.append({
      'post_id': post_id,
      'account_id': account_id,
      'is_festival': is_post_festival_post(),
      'posted_at': extract_posted_at()
    })
    move_to_next_post()

  if unread_posts:
    InstagramReadHistory.insert_many(unread_posts).execute()
    festival_posts = list(filter(lambda it: it['is_festival'], unread_posts))
    if festival_posts:
      festival_post_urls = "\n".join(map(lambda it: f'https://www.instagram.com/p/{it['post_id']}', festival_posts))
      message = (
        f"https://www.instagram.com/{account_id}\n"
        f"{insta_account.name} 계정에 {len(festival_posts)}개의 축제 게시글이 조회되었습니다.\n"
        f"{festival_post_urls}"
      )
      discord_client.send(message)
  logger.info(f'{account_id} 계정 크롤링 완료')


def move_to_first_post(account_id: str):
  driver.get(f'https://www.instagram.com/{account_id}')
  driver.implicitly_wait(5)
  try:
    first_post = driver.find_element(by=By.CSS_SELECTOR, value='._aagw')
  except NoSuchElementException:
    raise Exception(f'{account_id} 계정에 게시글이 존재하지 않습니다.')
  first_post.click()
  driver.implicitly_wait(1)


def extract_post_id() -> str:
  post_url = driver.current_url
  start_index = post_url.find('/p/') + 3
  end_index = post_url.find('/', start_index)
  return post_url[start_index:end_index]


def is_post_festival_post() -> bool:
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


def move_to_next_post():
  driver.find_element(
      by=By.CSS_SELECTOR,
      value='._aaqg'
  ).find_element(
      by=By.CSS_SELECTOR,
      value='._abl-'
  ).click()
  sleep(0.2)


def initial_history(insta_account):
  limit_count = 30
  read_count = 0
  account_id = insta_account.id
  logger.info(f'{account_id} 계정 읽은 게시글 기록 초기화 시작')
  if len(insta_account.histories) >= limit_count:
    logger.info(f'{account_id} 계정에 이미 읽은 게시글이 존재합니다.')
    return
  (InstagramReadHistory
   .delete()
   .where(InstagramReadHistory.account_id == account_id)
   .execute())

  move_to_first_post(account_id)

  unread_posts = []
  while read_count < limit_count:
    unread_posts.append({
      'post_id': extract_post_id(),
      'account_id': account_id,
      'is_festival': is_post_festival_post(),
      'posted_at': extract_posted_at()
    })
    try:
      move_to_next_post()
      read_count += 1
    except NoSuchElementException:
      break

  InstagramReadHistory.insert_many(unread_posts).execute()
  logger.info(f'{account_id} 계정에 {len(unread_posts)}개의 읽은 게시글 기록을 저장했습니다.')
