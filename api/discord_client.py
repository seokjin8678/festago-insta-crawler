import requests

global discord_webhook_url


def send(message: str):
  requests.request(method='POST', url=discord_webhook_url, json={
    "content": message
  })


def initial_webhook(url: str):
  global discord_webhook_url
  discord_webhook_url = url
