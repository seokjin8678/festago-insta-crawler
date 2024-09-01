import datetime
import logging
from io import BytesIO

import requests
from PIL import Image

from crawler import crawler
from db.entity import InstagramReadHistory

logging.basicConfig(
    filename=f"logs/{datetime.datetime.now().date()}.log",
    format='%(asctime)s %(levelname)s:%(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
  post_id = input('이미지를 가져올 게시글 ID 입력: ')
  count = int(input('연속된 이미지 게시글 개수 입력: '))
  post = InstagramReadHistory.select().where(InstagramReadHistory.post_id == post_id).get_or_none()
  if post is None:
    logger.error(f'{post_id}에 해당하는 게시글 기록이 존재하지 않습니다.')
    return
  image_posts = (InstagramReadHistory.select()
                 .where(InstagramReadHistory.account_id == post.account_id, InstagramReadHistory.id >= post.id)
                 .order_by(InstagramReadHistory.id)
                 .limit(count))
  image_post_urls = list(map(lambda image_post: f'https://www.instagram.com/p/{image_post.post_id}', image_posts))
  try:
    image_urls = [crawler.get_image_url(image_post_url) for image_post_url in image_post_urls]
    images = [Image.open(BytesIO(requests.get(image_url).content)) for image_url in image_urls]
    image = combine_images(images)

    ratio = 1 if len(images) < 3 else 3 / len(images)
    image = resize_image(image, ratio)
    image.save(
        f'./images/{post.account_id}_{post.post_id}.jpg',
        format="jpeg",
        optimize=True,
        quality=85
    )
  except Exception as e:
    logger.error(e)


def combine_images(images):
  if len(images) == 1:
    return images[0]
  width, height = images[0].size
  total_width = width * 3
  total_height = height * (len(images) // 3)
  new_image = Image.new('RGB', (total_width, total_height), (0, 0, 0))
  i, j = 0, 0
  for image in images:
    new_image.paste(image, box=(i * width, j * height))
    i += 1
    if i >= 3:
      i = 0
      j += 1
  return new_image


def resize_image(image, ratio):
  original_width, original_height = image.size
  new_width = int(original_width * ratio)
  new_height = int(original_height * ratio)
  return image.resize((new_width, new_height))


if __name__ == '__main__':
  main()
