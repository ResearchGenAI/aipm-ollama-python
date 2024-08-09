from ollama_aipm._client import Client, AsyncClient  # 导入客户端类和异步客户端类
from ollama_aipm._types import (  # 导入Ollama库的类型定义
  GenerateResponse,  # 生成响应类型
  ChatResponse,  # 聊天响应类型
  ProgressResponse,  # 进度响应类型
  Message,  # 消息类型
  Options,  # 选项类型
  RequestError,  # 请求错误类型
  ResponseError,  # 响应错误类型
)
# 将以下符号添加到模块的全局命名空间中
__all__ = [
  'Client',  # 客户端类
  'AsyncClient',  # 异步客户端类
  'GenerateResponse',  # 生成响应类型
  'ChatResponse',  # 聊天响应类型
  'ProgressResponse',  # 进度响应类型
  'Message',  # 消息类型
  'Options',  # 选项类型
  'RequestError',  # 请求错误类型
  'ResponseError',  # 响应错误类型
  'generate',  # 生成文本的方法
  'chat',  # 聊天交互的方法
  'embed',  # 嵌入文本的方法
  'embeddings',  # 获取嵌入的方法
  'pull',  # 拉取模型的方法
  'push',  # 推送模型的方法
  'create',  # 创建模型的方法
  'delete',  # 删除模型的方法
  'list',  # 列出模型的方法
  'copy',  # 复制模型的方法
  'show',  # 显示模型详情的方法
  'ps',  # 列出运行中的进程的方法
]
# 创建一个客户端实例
_client = Client()
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
