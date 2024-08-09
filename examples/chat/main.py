from ollama_aipm import chat

# 创建一个包含用户消息的消息列表
messages = [
  {
    'role': 'user',
    'content': '为什么天空是蓝色的?',
  },
]

# 使用mistral模型与Ollama API进行聊天交互
response = chat('mistral', messages=messages)

# 打印聊天响应中的消息内容
print(response['message']['content'])
