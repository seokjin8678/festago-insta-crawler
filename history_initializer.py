import argparse
import datetime
import logging

from crawler import crawler
from db.entity import database, InstagramAccount, InstagramReadHistory

logging.basicConfig(
    filename=f"logs/{datetime.datetime.now().date()}.log",
    format='%(asctime)s %(levelname)s:%(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main(username: str, password: str):
  crawler.login(username, password)

  database.create_tables([InstagramAccount, InstagramReadHistory])

  accounts = InstagramAccount.select()
  logger.info(f'{len(accounts)}개의 계정에 대해 읽은 게시글 기록 초기화를 시작합니다.')
  for account in accounts:
    try:
      with database.atomic():
        limit_count = 30
        read_count = 0
        account_id = account.id
        logger.info(f'{account_id} 계정 읽은 게시글 기록 초기화 시작')
        if len(account.histories) >= limit_count:
          logger.info(f'{account_id} 계정에 이미 읽은 게시글이 존재합니다.')
          return
        (InstagramReadHistory
         .delete()
         .where(InstagramReadHistory.account_id == account_id)
         .execute())

        crawler.move_to_first_post(account_id)

        unread_posts = []
        while read_count < limit_count:
          unread_posts.append({
            'post_id': crawler.extract_post_id(),
            'account_id': account_id,
            'is_festival': crawler.is_festival_post(),
            'posted_at': crawler.extract_posted_at()
          })
          try:
            crawler.move_to_next_post()
            read_count += 1
          except Exception:
            break

        InstagramReadHistory.insert_many(unread_posts).execute()
        logger.info(f'{account_id} 계정에 {len(unread_posts)}개의 읽은 게시글 기록을 저장했습니다.')
    except Exception as e:
      logger.error(e)
  logger.info(f'{len(accounts)}개의 계정에 대해 읽은 게시글 기록 초기화를 완료했습니다.')


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-u', '--username', required=True, help='인스타 계정')
  parser.add_argument('-p', '--password', required=True, help='인스타 비밀번호')
  args = parser.parse_args()
  main(args.username, args.password)
