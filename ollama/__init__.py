from ollama._client import Client, AsyncClient
from ollama._types import (
  GenerateResponse,  # 生成响应
  ChatResponse,  # 聊天响应
  ProgressResponse,  # 进度响应
  Message,  # 消息
  Options,  # 选项
  RequestError,  # 请求错误
  ResponseError,  # 响应错误
)

__all__ = [
  'Client',  # 客户端
  'AsyncClient',  # 异步客户端
  'GenerateResponse',  # 生成响应
  'ChatResponse',  # 聊天响应
  'ProgressResponse',  # 进度响应
  'Message',  # 消息
  'Options',  # 选项
  'RequestError',  # 请求错误
  'ResponseError',  # 响应错误
  'generate',  # 生成
  'chat',  # 聊天
  'embed',  # 嵌入
  'embeddings',  # 嵌入
  'pull',  # 拉
  'push',  # 推
  'create',  # 创建
  'delete',  # 删除
  'list',  # 列表
  'copy',  # 复制
  'show',  # 显示
  'ps',  # 进程
]

_client = Client()  # 创建一个客户端实例
# 将客户端实例的方法绑定到当前模块的命名空间
generate = _client.generate  # 生成文本的方法
chat = _client.chat  # 聊天交互的方法
embed = _client.embed  # 嵌入文本的方法
embeddings = _client.embeddings  # 获取嵌入的方法
pull = _client.pull  # 拉取模型的方法
push = _client.push  # 推送模型的方法
create = _client.create  # 创建模型的方法
delete = _client.delete  # 删除模型的方法
list = _client.list  # 列出模型的方法
copy = _client.copy  # 复制模型的方法
show = _client.show  # 显示模型详情的方法
ps = _client.ps  # 列出运行中的进程的方法
