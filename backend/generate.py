import os
from cerebras.cloud.sdk import Cerebras

client = Cerebras(
  api_key="csk-w4mcxrcex2vkpv24jdtv23kyjyh9jyn5cxw2terkp9k2xtxn"
)

chat_completion = client.chat.completions.create(
  messages=[
  {"role": "user", "content": "Why is fast inferepoetry run nce important?",}
],
  model="llama-4-scout-17b-16e-instruct",
)
print(chat_completion.choices[0].message.content)