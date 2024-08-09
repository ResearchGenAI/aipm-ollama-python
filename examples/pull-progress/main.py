from tqdm import tqdm
from ollama_aipm import pull

# 初始化当前摘要和进度条字典
current_digest, bars = '', {}

# 拉取模型信息，并设置为流式响应
for progress in pull('mistral', stream=True):
  # 获取当前进度中的摘要
  digest = progress.get('digest', '')
  
  # 如果摘要与当前摘要不同，并且当前摘要已经在进度条字典中，则关闭进度条
  if digest != current_digest and current_digest in bars:
    bars[current_digest].close()

  # 如果摘要为空，则打印进度状态并继续
  if not digest:
    print(progress.get('status'))
    continue

  # 如果摘要不在进度条字典中，并且存在总进度（total），则创建进度条
  if digest not in bars and (total := progress.get('total')):
    bars[digest] = tqdm(total=total, desc=f'pulling {digest[7:19]}', unit='B', unit_scale=True)

  # 如果存在已完成进度（completed），则更新进度条
  if completed := progress.get('completed'):
    bars[digest].update(completed - bars[digest].n)

  # 更新当前摘要为最新的摘要
  current_digest = digest
