from crawler import insta_crawler
from db.entity import database, InstagramAccount, InstagramReadHistory
import argparse
import logging

logging.basicConfig(
    filename="log.log",
    format='%(asctime)s %(levelname)s:%(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main(username: str, password: str):
  insta_crawler.login(username, password)
  database.create_tables([InstagramAccount, InstagramReadHistory])

  accounts = InstagramAccount.select()
  logger.info(f'{len(accounts)}개의 계정에 대해 읽은 게시글 기록 초기화를 시작합니다.')
  for account in accounts:
    try:
      with database.atomic():
        insta_crawler.initial_history(account)
    except Exception as e:
      logger.error(e)
  logger.info(f'{len(accounts)}개의 계정에 대해 읽은 게시글 기록 초기화를 완료했습니다.')


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-u', '--username', required=True, help='인스타 계정')
  parser.add_argument('-p', '--password', required=True, help='인스타 비밀번호')
  args = parser.parse_args()
  main(args.username, args.password)
