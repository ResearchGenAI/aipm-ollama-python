from ollama_aipm import ps, pull, chat

# 拉取模型信息，并设置为流式响应
response = pull('mistral', stream=True)
# 创建一个集合来存储已出现的进度状态
progress_states = set()
# 遍历流式响应中的每个进度信息
for progress in response:
  # 如果进度状态已经在集合中，则跳过
  if progress.get('status') in progress_states:
    continue
  # 添加进度状态到集合中
  progress_states.add(progress.get('status'))
  # 打印进度状态
  print(progress.get('status'))

# 打印换行符，以分隔不同的操作
print('\n')

# 与模型进行聊天交互，发送用户消息
response = chat('mistral', messages=[{'role': 'user', 'content': '你好！'}])
# 打印聊天响应中的消息内容
print(response['message']['content'])

# 打印换行符，以分隔不同的操作
print('\n')

# 列出运行中的进程
response = ps()

# 获取第一个模型的名称、大小和VRAM大小
name = response['models'][0]['name']
size = response['models'][0]['size']
size_vram = response['models'][0]['size_vram']

# 根据模型的大小和VRAM大小判断模型的使用情况
if size == size_vram:
  # 如果大小等于VRAM大小，则表示模型完全使用GPU
  print(f'{name}: 100% GPU')
elif not size_vram:
  # 如果没有VRAM大小，则表示模型完全使用CPU
  print(f'{name}: 100% CPU')
else:
  # 如果模型大小不等于VRAM大小，则计算模型使用CPU的比例
  size_cpu = size - size_vram
  cpu_percent = round(size_cpu / size * 100)
  # 打印模型使用CPU和GPU的比例
  print(f'{name}: {cpu_percent}% CPU/{100 - cpu_percent}% GPU')
