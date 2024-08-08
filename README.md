# Ollama Python库
Ollama Python库提供了最简单的方式来将Python 3.8+项目与[Ollama](https://github.com/ollama/ollama)集成。
## 安装
```sh
pip install ollama
```
## 使用
```python
import ollama
# 使用Ollama的chat函数与模型交互，发送用户消息并获取响应
response = ollama.chat(model='llama3.1', messages=[
  {
    'role': 'user',  # 指定消息的角色为用户
    'content': 'Why is the sky blue?',  # 消息内容
  },
])
# 打印出响应中的消息内容
print(response['message']['content'])
```
## 流式响应
通过设置`stream=True`，可以启用响应流，将函数调用修改为返回一个Python生成器，每个部分都是流中的一个对象。
```python
import ollama
# 启用流式响应
stream = ollama.chat(
    model='llama3.1',
    messages=[{'role': 'user', 'content': 'Why is the sky blue?'}],
    stream=True,  # 设置为流式响应
)
# 遍历流中的每个块并打印内容
for chunk in stream:
  print(chunk['message']['content'], end='', flush=True)
```
## API
Ollama Python库的API是围绕[Ollama REST API](https://github.com/ollama/ollama/blob/main/docs/api.md)设计的
### 聊天
```python
ollama.chat(model='llama3.1', messages=[{'role': 'user', 'content': 'Why is the sky blue?'}])
```
### 生成
```python
ollama.generate(model='llama3.1', prompt='Why is the sky blue?')
```
### 列表
```python
ollama.list()
```
### 显示
```python
ollama.show('llama3.1')
```
### 创建
```python
modelfile='''
FROM llama3.1
SYSTEM You are mario from super mario bros.
'''
ollama.create(model='example', modelfile=modelfile)
```
### 复制
```python
ollama.copy('llama3.1', 'user/llama3.1')
```
### 删除
```python
ollama.delete('llama3.1')
```
### 拉
```python
ollama.pull('llama3.1')
```
### 推
```python
ollama.push('user/llama3.1')
```
### 嵌入
```python
ollama.embeddings(model='llama3.1', prompt='The sky is blue because of rayleigh scattering')
```
### 进程
```python
ollama.ps()
```
## 自定义客户端
可以使用以下字段创建自定义客户端：
- `host`: 要连接的Ollama主机
- `timeout`: 请求的超时时间
```python
from ollama import Client
client = Client(host='http://localhost:11434')
response = client.chat(model='llama3.1', messages=[
  {
    'role': 'user',
    'content': 'Why is the sky blue?',
  },
])
```
## 异步客户端
```python
import asyncio
from ollama import AsyncClient
async def chat():
  message = {'role': 'user', 'content': 'Why is the sky blue?'}
  response = await AsyncClient().chat(model='llama3.1', messages=[message])
asyncio.run(chat())
```
设置`stream=True`可以将函数修改为返回Python异步生成器：
```python
import asyncio
from ollama import AsyncClient
async def chat():
  message = {'role': 'user', 'content': 'Why is the sky blue?'}
  async for part in await AsyncClient().chat(model='llama3.1', messages=[message], stream=True):
    print(part['message']['content'], end='', flush=True)
asyncio.run(chat())
```
## 错误
如果请求返回错误状态或者在流式传输时检测到错误，将引发错误。
```python
model = 'does-not-yet-exist'
try:
  ollama.chat(model)
except ollama.ResponseError as e:
  print('Error:', e.error)
  if e.status_code == 404:
    ollama.pull(model)
```
