import sys
import random
import httpx

from ollama_aipm import generate

# 获取xkcd最新漫画的元数据
latest = httpx.get('https://xkcd.com/info.0.json')
latest.raise_for_status()

# 如果提供了命令行参数，则使用第一个参数作为漫画编号，否则随机选择一个编号
if len(sys.argv) > 1:
  num = int(sys.argv[1])
else:
  num = random.randint(1, latest.json().get('num'))

# 获取指定编号的漫画元数据
comic = httpx.get(f'https://xkcd.com/{num}/info.0.json')
comic.raise_for_status()

# 打印漫画编号和标题
print(f'xkcd #{comic.json().get("num")}: {comic.json().get("alt")}')
print(f'链接: https://xkcd.com/{num}')
print('---')

# 获取漫画的原始图片内容
raw = httpx.get(comic.json().get('img'))
raw.raise_for_status()

# 使用generate函数生成关于该漫画的文本解释，并设置流式响应
for response in generate('llava', '解释这个漫画：', images=[raw.content], stream=True):
  print(response['response'], end='', flush=True)  # 打印响应内容，不换行

print()  # 打印换行符，以结束解释文本
