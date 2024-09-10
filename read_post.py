import argparse
import datetime
import logging

from api import discord_client
from crawler import crawler
from db.entity import database, InstagramAccount, InstagramReadHistory

logging.basicConfig(
    filename=f"logs/{datetime.datetime.now().date()}.log",
    format='%(asctime)s %(levelname)s:%(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main(username: str, password: str, webhook_url: str):
  account_id = input('게시글을 읽을 계정 입력: ')
  database.create_tables([InstagramAccount, InstagramReadHistory])
  discord_client.initial_webhook(webhook_url)

  crawler.login(username, password)

  account = InstagramAccount.get_by_id(account_id)
  read_post(account)


def read_post(account):
  account_id = account.id
  try:
    with database.atomic():
      logger.info(f'{account_id} 계정 크롤링 시작')

      crawler.move_to_first_post(account_id)

      unread_posts = []
      for _ in range(crawler.get_pinned_post_count()):
        post_id = crawler.extract_post_id()
        logger.info(f'게시글 조회 완료 post_id = {post_id}')
        post = (InstagramReadHistory.select()
                .where(InstagramReadHistory.post_id == post_id)
                .get_or_none())
        if post is None:
          unread_posts.append({
            'post_id': post_id,
            'account_id': account_id,
            'is_festival': crawler.is_festival_post(),
            'posted_at': crawler.extract_posted_at()
          })
        crawler.move_to_next_post()

      read_post_ids = set(
          map(
              lambda history: history.post_id,
              account.histories
              .select()
              .order_by(InstagramReadHistory.posted_at.desc())
              .limit(30)
          )
      )

      while True:
        post_id = crawler.extract_post_id()
        logger.info(f'게시글 조회 완료 post_id = {post_id}')
        if post_id in read_post_ids:
          break

        unread_posts.append({
          'post_id': post_id,
          'account_id': account_id,
          'is_festival': crawler.is_festival_post(),
          'posted_at': crawler.extract_posted_at()
        })
        crawler.move_to_next_post()

      if unread_posts:
        InstagramReadHistory.insert_many(unread_posts).execute()
        festival_posts = list(filter(lambda it: it['is_festival'], unread_posts))
        if festival_posts:
          festival_post_urls = "\n".join(
              map(lambda it: f'https://www.instagram.com/p/{it['post_id']}', festival_posts))
          message = (
            f"[{account.name}](https://www.instagram.com/{account_id}) 계정에 {len(festival_posts)}개의 축제 게시글이 조회되었습니다.\n"
            f"{festival_post_urls}"
          )
          discord_client.send(message)
      else:
        if (datetime.datetime.now() - crawler.extract_posted_at()) >= datetime.timedelta(days=30):
          message = f'[{account.name}](https://www.instagram.com/{account_id}) 계정에 30일 이상 새로운 게시글이 업로드 되지 않았습니다.'
          discord_client.send(message)

      logger.info(f'{account_id} 계정 크롤링 완료')
  except Exception as e:
    logger.error(e)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-u', '--username', required=True, help='인스타 계정')
  parser.add_argument('-p', '--password', required=True, help='인스타 비밀번호')
  parser.add_argument('-w', '--webhook', required=True, help='웹훅 URL')
  args = parser.parse_args()
  main(args.username, args.password, args.webhook)
