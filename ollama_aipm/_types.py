import json
from typing import Any, TypedDict, Sequence, Literal, Mapping

import sys

if sys.version_info < (3, 11):
  from typing_extensions import NotRequired
else:
  from typing import NotRequired


class BaseGenerateResponse(TypedDict):
  model: str
  '用于生成响应的模型。'
  
  created_at: str
  '请求创建的时间。'
  
  done: bool
  '如果响应已完成则为True，否则为False。对于流式响应，可用于检测最终响应。'
  
  done_reason: str
  '完成响应的原因。当done为True时才存在。'
  
  total_duration: int
  '总持续时间（纳秒）。'
  
  load_duration: int
  '加载持续时间（纳秒）。'
  
  prompt_eval_count: int
  '提示中评估的令牌数量。'
  
  prompt_eval_duration: int
  '提示评估的持续时间（纳秒）。'
  
  eval_count: int
  '推理中评估的令牌数量。'
  
  eval_duration: int
  '推理评估的持续时间（纳秒）。'


class GenerateResponse(BaseGenerateResponse):
  """
  由生成请求返回的响应。
  """
  
  response: str  # 响应内容
  '响应内容。当流式响应时，这包含响应的一部分。'
  
  context: Sequence[int]  # 分词后的历史记录
  '响应前的令牌化历史记录。'


class ToolCallFunction(TypedDict):
  """
  工具调用函数。
  """
  
  name: str
  '函数的名称。'
  
  arguments: NotRequired[Mapping[str, Any]]
  '函数的参数。'


class ToolCall(TypedDict):
  """
  模型工具调用。
  """
  
  function: ToolCallFunction  # 要调用的函数
  '要调用的函数。'


class Message(TypedDict):
  """
  聊天消息。
  """
  
  role: Literal['user', 'assistant', 'system', 'tool']  # 消息的角色
  "消息假设的角色。响应消息总是具有角色 'assistant' 或 'tool'。"
  
  content: NotRequired[str]  # 消息的内容
  '消息的内容。流式响应时，响应消息包含消息片段。'
  
  images: NotRequired[Sequence[Any]]  # 可选的图像数据列表
  """
  多模态模型的可选图像数据列表。
  
  有效的输入类型包括：
  - `str` 或路径对象：图像文件的路径
  - `bytes` 或字节对象：原始图像数据
  
  有效的图像格式取决于模型。更多信息请参见模型卡。
  """
  
  tool_calls: NotRequired[Sequence[ToolCall]]  # 模型要调用的工具调用
  """
  模型要调用的工具调用。
  """


class Property(TypedDict):
  type: str  # 属性的类型
  description: str  # 属性的描述
  enum: NotRequired[Sequence[str]]  # `enum` 是可选的，可以是一个字符串序列


class Parameters(TypedDict):
  type: str  # 参数的类型
  required: Sequence[str]  # 必填参数的名称列表
  properties: Mapping[str, Property]  # 参数的属性，键为参数名，值为属性字典


class ToolFunction(TypedDict):
  name: str  # 工具函数的名称
  description: str  # 工具函数的描述
  parameters: Parameters  # 工具函数的参数


class Tool(TypedDict):
  type: str  # 工具的类型
  function: ToolFunction  # 工具的函数定义


class ChatResponse(BaseGenerateResponse):
  """
  由聊天请求返回的响应。
  """

  message: Message  # 响应消息
  '响应消息。'


class ProgressResponse(TypedDict):
  status: str  # 状态
  completed: int  # 完成数
  total: int  # 总数
  digest: str  # 摘要


class Options(TypedDict, total=False):
  # 加载时间选项
  numa: bool  # 是否使用NUMA
  num_ctx: int  # 上下文数量
  num_batch: int  # 批处理数量
  num_gpu: int  # GPU数量
  main_gpu: int  # 主GPU编号
  low_vram: bool  # 是否使用低VRAM
  f16_kv: bool  # 是否使用16位KV
  logits_all: bool  # 是否使用所有logits
  vocab_only: bool  # 是否仅使用词汇表
  use_mmap: bool  # 是否使用mmap
  use_mlock: bool  # 是否使用mlock
  embedding_only: bool  # 是否仅使用嵌入
  num_thread: int  # 线程数量
  
  # 运行时间选项
  num_keep: int  # 保留数量
  seed: int  # 种子
  num_predict: int  # 预测数量
  top_k: int  # top-k
  top_p: float  # top-p
  tfs_z: float  # TFS-z
  typical_p: float  # 典型p
  repeat_last_n: int  # 重复最后n
  temperature: float  # 温度
  repeat_penalty: float  # 重复惩罚
  presence_penalty: float  # 存在惩罚
  frequency_penalty: float  # 频率惩罚
  mirostat: int  # Mirostat
  mirostat_tau: float  # Mirostat-tau
  mirostat_eta: float  # Mirostat-eta
  penalize_newline: bool  # 是否惩罚换行符
  stop: Sequence[str]  # 停止序列


class RequestError(Exception):
  """
  请求错误的通用类。
  """

  def __init__(self, error: str):
    super().__init__(error)
    self.error = error  # 错误原因
    '错误原因。'


class ResponseError(Exception):
  """
  响应错误的通用类。
  """

  def __init__(self, error: str, status_code: int = -1):
    try:
      # 尝试将内容解析为JSON并提取'error'
      # 如果JSON解析失败，则使用原始内容
      error = json.loads(error).get('error', error)
    except json.JSONDecodeError:
      ...

    super().__init__(error)
    self.error = error  # 错误原因
    '错误原因。'
    
    self.status_code = status_code  # HTTP响应状态码
    'HTTP响应状态码。'
