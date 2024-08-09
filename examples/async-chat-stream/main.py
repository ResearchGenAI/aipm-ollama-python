import shutil
import asyncio
import argparse

import ollama_aipm


# 异步函数，用于通过外部命令将文本转换为语音
async def speak(speaker, content):
  if speaker:
    # 创建一个子进程来执行语音命令
    p = await asyncio.create_subprocess_exec(speaker, content)
    # 等待子进程执行完毕
    await p.communicate()


# 异步主函数
async def main():
  # 创建一个ArgumentParser实例来解析命令行参数
  parser = argparse.ArgumentParser()
  # 添加一个可选参数'speak'，默认为False，如果提供则设置为True
  parser.add_argument('--speak', default=False, action='store_true')
  # 解析命令行参数
  args = parser.parse_args()
  # 初始化语音合成工具变量
  speaker = None
  # 如果用户没有提供'speak'参数
  if not args.speak:
    ...
  # 如果系统中有'say'命令，则使用它
  elif say := shutil.which('say'):
    speaker = say
  # 如果系统中有'espeak'或'espeak-ng'命令，则使用它
  elif (espeak := shutil.which('espeak')) or (espeak := shutil.which('espeak-ng')):
    speaker = espeak
  # 创建一个异步客户端实例
  client = ollama_aipm.AsyncClient()
  # 初始化消息列表
  messages = []
  # 无限循环，直到用户中断
  while True:
    # 获取用户输入
    if content_in := input('>>> '):
      # 将用户输入添加到消息列表
      messages.append({'role': 'user', 'content': content_in})
      # 初始化输出内容
      content_out = ''
      # 初始化助手消息
      message = {'role': 'assistant', 'content': ''}
      # 异步迭代聊天响应
      async for response in await client.chat(model='mistral', messages=messages, stream=True):
        # 如果响应完成
        if response['done']:
          # 将助手消息添加到消息列表
          messages.append(message)
        # 获取响应中的消息内容
        content = response['message']['content']
        # 打印消息内容，不换行
        print(content, end='', flush=True)
        # 累加输出内容
        content_out += content
        # 如果内容以标点符号或换行符结束，则使用语音合成工具读出
        if content in ['.', '!', '?', '\n']:
          await speak(speaker, content_out)
          # 重置输出内容
          content_out = ''
        # 累加助手消息内容
        message['content'] += content
      # 如果还有未读出的内容，则使用语音合成工具读出
      if content_out:
        await speak(speaker, content_out)
      # 打印换行符
      print()


# 尝试运行主函数
try:
  asyncio.run(main())
# 捕获键盘中断或文件结束错误
except (KeyboardInterrupt, EOFError):
  ...
