import os  # 导入操作系统接口模块
import io  # 导入IO流模块
import json  # 导入JSON处理模块
import httpx  # 导入HTTP客户端模块
import binascii  # 导入二进制和ASCII转换模块
import platform  # 导入平台信息模块
import urllib.parse  # 导入URL解析模块
from os import PathLike  # 导入路径类
from pathlib import Path  # 导入路径操作模块
from copy import deepcopy  # 导入深拷贝函数
from hashlib import sha256  # 导入SHA256哈希函数
from base64 import b64encode, b64decode  # 导入Base64编码和解码函数

from typing import Any, AnyStr, Union, Optional, Sequence, Mapping, Literal, overload  # 导入类型注解相关类型

import sys  # 导入系统接口模块
# 如果Python版本小于3.9，则从typing导入Iterator和AsyncIterator
if sys.version_info < (3, 9):
  from typing import Iterator, AsyncIterator
else:
  from collections.abc import Iterator, AsyncIterator  # 从collections.abc导入迭代器相关类型
  
from importlib import metadata  # 导入元数据模块，用于获取包版本信息
# 尝试获取ollama包的版本信息
try:
  __version__ = metadata.version('ollama')
except metadata.PackageNotFoundError:
  __version__ = '0.0.0'  # 如果找不到版本信息，则默认为'0.0.0'
# 从ollama_aipm._types导入类型定义
from ollama_aipm._types import Message, Options, RequestError, ResponseError, Tool


class BaseClient:
  def __init__(
    self,
    client,
    host: Optional[str] = None,  # 可选的字符串，表示主机地址
    follow_redirects: bool = True,  # 布尔值，表示是否跟随重定向
    timeout: Any = None,  # 任何类型，表示超时时间
    **kwargs,  # 关键字参数，传递给httpx客户端
  ) -> None:
    """
    创建一个httpx客户端。默认参数与httpx中定义的相同，除了以下几项：
    - `follow_redirects`: True
    - `timeout`: None
    `kwargs`将被传递给httpx客户端。
    """
    # 从kwargs中弹出'headers'键，如果不存在则默认为空字典
    headers = kwargs.pop('headers', {})
    # 设置请求头内容类型为JSON
    headers['Content-Type'] = 'application/json'
    # 设置接受的内容类型为JSON
    headers['Accept'] = 'application/json'
    # 设置用户代理，包含ollama版本、平台信息、Python版本
    headers['User-Agent'] = f'ollama-python/{__version__} ({platform.machine()} {platform.system().lower()}) Python/{platform.python_version()}'
    # 初始化客户端实例，使用提供的参数
    self._client = client(
      base_url=_parse_host(host or os.getenv('OLLAMA_HOST')),  # 解析主机地址，优先使用host参数，否则使用环境变量
      follow_redirects=follow_redirects,  # 是否跟随重定向
      timeout=timeout,  # 超时时间
      headers=headers,  # 请求头
      **kwargs,  # 其他参数
    )



class Client(BaseClient):
  def __init__(self, host: Optional[str] = None, **kwargs) -> None:
    super().__init__(httpx.Client, host, **kwargs)

  def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
    response = self._client.request(method, url, **kwargs)

    try:
      response.raise_for_status()
    except httpx.HTTPStatusError as e:
      raise ResponseError(e.response.text, e.response.status_code) from None

    return response

  def _stream(self, method: str, url: str, **kwargs) -> Iterator[Mapping[str, Any]]:
    with self._client.stream(method, url, **kwargs) as r:
      try:
        r.raise_for_status()
      except httpx.HTTPStatusError as e:
        e.response.read()
        raise ResponseError(e.response.text, e.response.status_code) from None

      for line in r.iter_lines():
        partial = json.loads(line)
        if e := partial.get('error'):
          raise ResponseError(e)
        yield partial

  def _request_stream(
    self,
    *args,
    stream: bool = False,
    **kwargs,
  ) -> Union[Mapping[str, Any], Iterator[Mapping[str, Any]]]:
    return self._stream(*args, **kwargs) if stream else self._request(*args, **kwargs).json()

  @overload
  def generate(
    self,
    model: str = '',
    prompt: str = '',
    suffix: str = '',
    system: str = '',
    template: str = '',
    context: Optional[Sequence[int]] = None,
    stream: Literal[False] = False,
    raw: bool = False,
    format: Literal['', 'json'] = '',
    images: Optional[Sequence[AnyStr]] = None,
    options: Optional[Options] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> Mapping[str, Any]: ...

  @overload
  def generate(
    self,
    model: str = '',
    prompt: str = '',
    suffix: str = '',
    system: str = '',
    template: str = '',
    context: Optional[Sequence[int]] = None,
    stream: Literal[True] = True,
    raw: bool = False,
    format: Literal['', 'json'] = '',
    images: Optional[Sequence[AnyStr]] = None,
    options: Optional[Options] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> Iterator[Mapping[str, Any]]: ...

  def generate(
    self,
    model: str = '',  # 模型名称，默认为空字符串
    prompt: str = '',  # 提示文本，默认为空字符串
    suffix: str = '',  # 后缀文本，默认为空字符串
    system: str = '',  # 系统文本，默认为空字符串
    template: str = '',  # 模板文本，默认为空字符串
    context: Optional[Sequence[int]] = None,  # 上下文，默认为None
    stream: bool = False,  # 是否以流式方式返回，默认为False
    raw: bool = False,  # 是否返回原始数据，默认为False
    format: Literal['', 'json'] = '',  # 响应格式，默认为空字符串或'json'
    images: Optional[Sequence[AnyStr]] = None,  # 图片数据，默认为None
    options: Optional[Options] = None,  # 生成选项，默认为None
    keep_alive: Optional[Union[float, str]] = None,  # 保持连接，默认为None
  ) -> Union[Mapping[str, Any], Iterator[Mapping[str, Any]]]:
    """
    使用请求的模型创建一个响应。
    
    如果未提供模型，则引发`RequestError`。
    
    如果请求无法完成，则引发`ResponseError`。
    
    如果`stream`为`False`，则返回`GenerateResponse`，否则返回一个`GenerateResponse`生成器。
    """
    # 如果模型为空，则抛出RequestError
    if not model:
      raise RequestError('必须提供一个模型')
    # 调用_request_stream方法，发送POST请求，获取响应
    return self._request_stream(
      'POST',
      '/api/generate',
      json={
        'model': model,
        'prompt': prompt,
        'suffix': suffix,
        'system': system,
        'template': template,
        'context': context or [],  # 如果context为None，则返回空列表
        'stream': stream,
        'raw': raw,
        'images': [_encode_image(image) for image in images or []],  # 如果images为None，则返回空列表
        'format': format,
        'options': options or {},  # 如果options为None，则返回空字典
        'keep_alive': keep_alive,
      },
      stream=stream,  # 请求是否以流式方式返回
    )

  @overload
  def chat(
    self,
    model: str = '',
    messages: Optional[Sequence[Message]] = None,
    tools: Optional[Sequence[Tool]] = None,
    stream: Literal[False] = False,
    format: Literal['', 'json'] = '',
    options: Optional[Options] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> Mapping[str, Any]: ...

  @overload
  def chat(
    self,
    model: str = '',
    messages: Optional[Sequence[Message]] = None,
    tools: Optional[Sequence[Tool]] = None,
    stream: Literal[True] = True,
    format: Literal['', 'json'] = '',
    options: Optional[Options] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> Iterator[Mapping[str, Any]]: ...

  def chat(
    self,
    model: str = '',  # 模型名称，默认为空字符串
    messages: Optional[Sequence[Message]] = None,  # 消息序列，默认为None
    tools: Optional[Sequence[Tool]] = None,  # 工具序列，默认为None
    stream: bool = False,  # 是否以流式方式返回，默认为False
    format: Literal['', 'json'] = '',  # 响应格式，默认为空字符串或'json'
    options: Optional[Options] = None,  # 聊天选项，默认为None
    keep_alive: Optional[Union[float, str]] = None,  # 保持连接，默认为None
  ) -> Union[Mapping[str, Any], Iterator[Mapping[str, Any]]]:
    """
    使用请求的模型创建一个聊天响应。
    
    如果未提供模型，则引发`RequestError`。
    
    如果请求无法完成，则引发`ResponseError`。
    
    如果`stream`为`False`，则返回`ChatResponse`，否则返回一个`ChatResponse`生成器。
    """
    # 如果模型为空，则抛出RequestError
    if not model:
      raise RequestError('必须提供一个模型')
    # 对messages进行深拷贝，以避免后续操作影响原始数据
    messages = deepcopy(messages)
    # 遍历消息序列，如果有图片，则进行编码处理
    for message in messages or []:
      if images := message.get('images'):
        message['images'] = [_encode_image(image) for image in images]
    # 调用_request_stream方法，发送POST请求，获取响应
    return self._request_stream(
      'POST',
      '/api/chat',
      json={
        'model': model,
        'messages': messages,
        'tools': tools or [],  # 如果tools为None，则返回空列表
        'stream': stream,
        'format': format,
        'options': options or {},  # 如果options为None，则返回空字典
        'keep_alive': keep_alive,
      },
      stream=stream,  # 请求是否以流式方式返回
    )
    
  def embed(
    self,
    model: str = '',  # 模型名称，默认为空字符串
    input: Union[str, Sequence[AnyStr]] = '',  # 输入文本，可以是字符串或字符串序列，默认为空字符串
    truncate: bool = True,  # 是否截断输入文本，默认为True
    options: Optional[Options] = None,  # 嵌入选项，默认为None
    keep_alive: Optional[Union[float, str]] = None,  # 保持连接，默认为None
  ) -> Mapping[str, Any]:
    """
    使用请求的模型对输入文本进行嵌入。
    
    如果未提供模型，则引发`RequestError`。
    
    返回`Mapping[str, Any]`类型的结果，包含嵌入结果。
    """
    # 如果模型为空，则抛出RequestError
    if not model:
      raise RequestError('必须提供一个模型')
    # 调用_request方法，发送POST请求，获取响应
    return self._request(
      'POST',
      '/api/embed',
      json={
        'model': model,
        'input': input,
        'truncate': truncate,
        'options': options or {},  # 如果options为None，则返回空字典
        'keep_alive': keep_alive,
      },
    ).json()

  def embeddings(
    self,
    model: str = '',
    prompt: str = '',
    options: Optional[Options] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> Mapping[str, Sequence[float]]:
    return self._request(
      'POST',
      '/api/embeddings',
      json={
        'model': model,
        'prompt': prompt,
        'options': options or {},
        'keep_alive': keep_alive,
      },
    ).json()

  @overload
  def pull(
    self,
    model: str,
    insecure: bool = False,
    stream: Literal[False] = False,
  ) -> Mapping[str, Any]: ...

  @overload
  def pull(
    self,
    model: str,
    insecure: bool = False,
    stream: Literal[True] = True,
  ) -> Iterator[Mapping[str, Any]]: ...

  def pull(
    self,
    model: str,  # 模型名称
    insecure: bool = False,  # 是否使用不安全的连接，默认为False
    stream: bool = False,  # 是否以流式方式返回，默认为False
  ) -> Union[Mapping[str, Any], Iterator[Mapping[str, Any]]]:
    """
    如果请求无法完成，则引发`ResponseError`。

    如果`stream`为`False`，则返回`ProgressResponse`，否则返回一个`ProgressResponse`生成器。
    """
    # 调用_request_stream方法，发送POST请求，获取响应
    return self._request_stream(
      'POST',
      '/api/pull',
      json={
        'name': model,  # 模型名称
        'insecure': insecure,  # 是否使用不安全的连接
        'stream': stream,  # 是否以流式方式返回
      },
      stream=stream,  # 请求是否以流式方式返回
    )


  @overload
  def push(
    self,
    model: str,
    insecure: bool = False,
    stream: Literal[False] = False,
  ) -> Mapping[str, Any]: ...

  @overload
  def push(
    self,
    model: str,
    insecure: bool = False,
    stream: Literal[True] = True,
  ) -> Iterator[Mapping[str, Any]]: ...

  def push(
    self,
    model: str,  # 模型名称
    insecure: bool = False,  # 是否使用不安全的连接，默认为False
    stream: bool = False,  # 是否以流式方式返回，默认为False
  ) -> Union[Mapping[str, Any], Iterator[Mapping[str, Any]]]:
    """
    如果请求无法完成，则引发`ResponseError`。

    如果`stream`为`False`，则返回`ProgressResponse`，否则返回一个`ProgressResponse`生成器。
    """
    # 调用_request_stream方法，发送POST请求，获取响应
    return self._request_stream(
      'POST',
      '/api/push',
      json={
        'name': model,  # 模型名称
        'insecure': insecure,  # 是否使用不安全的连接
        'stream': stream,  # 是否以流式方式返回
      },
      stream=stream,  # 请求是否以流式方式返回
    )

  @overload
  def create(
    self,
    model: str,
    path: Optional[Union[str, PathLike]] = None,
    modelfile: Optional[str] = None,
    quantize: Optional[str] = None,
    stream: Literal[False] = False,
  ) -> Mapping[str, Any]: ...

  @overload
  def create(
    self,
    model: str,
    path: Optional[Union[str, PathLike]] = None,
    modelfile: Optional[str] = None,
    quantize: Optional[str] = None,
    stream: Literal[True] = True,
  ) -> Iterator[Mapping[str, Any]]: ...

  def create(
    self,
    model: str,  # 模型名称
    path: Optional[Union[str, PathLike]] = None,  # 模型文件的路径，可以是字符串或路径对象，默认为None
    modelfile: Optional[str] = None,  # 模型文件的名称，默认为None
    quantize: Optional[str] = None,  # 量化配置，默认为None
    stream: bool = False,  # 是否以流式方式返回，默认为False
  ) -> Union[Mapping[str, Any], Iterator[Mapping[str, Any]]]:
    """
    如果请求无法完成，则引发`ResponseError`。

    如果`stream`为`False`，则返回`ProgressResponse`，否则返回一个`ProgressResponse`生成器。
    """
    # 如果指定了路径，并且路径存在，则使用路径读取模型文件
    if (realpath := _as_path(path)) and realpath.exists():
      modelfile = self._parse_modelfile(realpath.read_text(), base=realpath.parent)
    # 如果指定了modelfile，则直接使用modelfile
    elif modelfile:
      modelfile = self._parse_modelfile(modelfile)
    # 如果以上条件都不满足，则抛出RequestError
    else:
      raise RequestError('必须提供路径或modelfile')

    # 调用_request_stream方法，发送POST请求，获取响应
    return self._request_stream(
      'POST',
      '/api/create',
      json={
        'name': model,  # 模型名称
        'modelfile': modelfile,  # 模型文件内容
        'stream': stream,  # 是否以流式方式返回
        'quantize': quantize,  # 量化配置
      },
      stream=stream,  # 请求是否以流式方式返回
    )

  def _parse_modelfile(self, modelfile: str, base: Optional[Path] = None) -> str:
    base = Path.cwd() if base is None else base

    out = io.StringIO()
    for line in io.StringIO(modelfile):
      command, _, args = line.partition(' ')
      if command.upper() not in ['FROM', 'ADAPTER']:
        print(line, end='', file=out)
        continue

      path = Path(args.strip()).expanduser()
      path = path if path.is_absolute() else base / path
      if path.exists():
        args = f'@{self._create_blob(path)}\n'
      print(command, args, end='', file=out)

    return out.getvalue()

  def _create_blob(self, path: Union[str, Path]) -> str:
    sha256sum = sha256()
    with open(path, 'rb') as r:
      while True:
        chunk = r.read(32 * 1024)
        if not chunk:
          break
        sha256sum.update(chunk)

    digest = f'sha256:{sha256sum.hexdigest()}'

    try:
      self._request('HEAD', f'/api/blobs/{digest}')
    except ResponseError as e:
      if e.status_code != 404:
        raise

      with open(path, 'rb') as r:
        self._request('POST', f'/api/blobs/{digest}', content=r)

    return digest

  def delete(self, model: str) -> Mapping[str, Any]:
    response = self._request('DELETE', '/api/delete', json={'name': model})
    return {'status': 'success' if response.status_code == 200 else 'error'}

  def list(self) -> Mapping[str, Any]:
    return self._request('GET', '/api/tags').json()

  def copy(self, source: str, destination: str) -> Mapping[str, Any]:
    response = self._request('POST', '/api/copy', json={'source': source, 'destination': destination})
    return {'status': 'success' if response.status_code == 200 else 'error'}

  def show(self, model: str) -> Mapping[str, Any]:
    return self._request('POST', '/api/show', json={'name': model}).json()

  def ps(self) -> Mapping[str, Any]:
    return self._request('GET', '/api/ps').json()


class AsyncClient(BaseClient):
  def __init__(self, host: Optional[str] = None, **kwargs) -> None:
    super().__init__(httpx.AsyncClient, host, **kwargs)

  async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
    response = await self._client.request(method, url, **kwargs)

    try:
      response.raise_for_status()
    except httpx.HTTPStatusError as e:
      raise ResponseError(e.response.text, e.response.status_code) from None

    return response

  async def _stream(self, method: str, url: str, **kwargs) -> AsyncIterator[Mapping[str, Any]]:
    async def inner():
      async with self._client.stream(method, url, **kwargs) as r:
        try:
          r.raise_for_status()
        except httpx.HTTPStatusError as e:
          e.response.read()
          raise ResponseError(e.response.text, e.response.status_code) from None

        async for line in r.aiter_lines():
          partial = json.loads(line)
          if e := partial.get('error'):
            raise ResponseError(e)
          yield partial

    return inner()

  async def _request_stream(
    self,
    *args,
    stream: bool = False,
    **kwargs,
  ) -> Union[Mapping[str, Any], AsyncIterator[Mapping[str, Any]]]:
    if stream:
      return await self._stream(*args, **kwargs)

    response = await self._request(*args, **kwargs)
    return response.json()

  @overload
  async def generate(
    self,
    model: str = '',
    prompt: str = '',
    suffix: str = '',
    system: str = '',
    template: str = '',
    context: Optional[Sequence[int]] = None,
    stream: Literal[False] = False,
    raw: bool = False,
    format: Literal['', 'json'] = '',
    images: Optional[Sequence[AnyStr]] = None,
    options: Optional[Options] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> Mapping[str, Any]: ...

  @overload
  async def generate(
    self,
    model: str = '',
    prompt: str = '',
    suffix: str = '',
    system: str = '',
    template: str = '',
    context: Optional[Sequence[int]] = None,
    stream: Literal[True] = True,
    raw: bool = False,
    format: Literal['', 'json'] = '',
    images: Optional[Sequence[AnyStr]] = None,
    options: Optional[Options] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> AsyncIterator[Mapping[str, Any]]: ...

  async def generate(
    self,
    model: str = '',  # 模型名称，默认为空字符串
    prompt: str = '',  # 提示文本，默认为空字符串
    suffix: str = '',  # 后缀文本，默认为空字符串
    system: str = '',  # 系统文本，默认为空字符串
    template: str = '',  # 模板文本，默认为空字符串
    context: Optional[Sequence[int]] = None,  # 上下文，默认为None
    stream: bool = False,  # 是否以流式方式返回，默认为False
    raw: bool = False,  # 是否返回原始数据，默认为False
    format: Literal['', 'json'] = '',  # 响应格式，默认为空字符串或'json'
    images: Optional[Sequence[AnyStr]] = None,  # 图片数据，默认为None
    options: Optional[Options] = None,  # 生成选项，默认为None
    keep_alive: Optional[Union[float, str]] = None,  # 保持连接，默认为None
  ) -> Union[Mapping[str, Any], AsyncIterator[Mapping[str, Any]]]:
    """
    使用请求的模型创建一个响应。

    如果未提供模型，则引发`RequestError`。

    如果请求无法完成，则引发`ResponseError`。

    如果`stream`为`False`，则返回`GenerateResponse`，否则返回一个异步的`GenerateResponse`生成器。
    """
    # 如果模型为空，则抛出RequestError
    if not model:
      raise RequestError('必须提供一个模型')

    # 调用_request_stream方法，发送POST请求，获取响应
    return await self._request_stream(
      'POST',
      '/api/generate',
      json={
        'model': model,
        'prompt': prompt,
        'suffix': suffix,
        'system': system,
        'template': template,
        'context': context or [],  # 如果context为None，则返回空列表
        'stream': stream,
        'raw': raw,
        'images': [_encode_image(image) for image in images or []],  # 如果images为None，则返回空列表
        'format': format,
        'options': options or {},  # 如果options为None，则返回空字典
        'keep_alive': keep_alive,
      },
      stream=stream,  # 请求是否以流式方式返回
    )

  @overload
  async def chat(
    self,
    model: str = '',
    messages: Optional[Sequence[Message]] = None,
    tools: Optional[Sequence[Tool]] = None,
    stream: Literal[False] = False,
    format: Literal['', 'json'] = '',
    options: Optional[Options] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> Mapping[str, Any]: ...

  @overload
  async def chat(
    self,
    model: str = '',
    messages: Optional[Sequence[Message]] = None,
    tools: Optional[Sequence[Tool]] = None,
    stream: Literal[True] = True,
    format: Literal['', 'json'] = '',
    options: Optional[Options] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> AsyncIterator[Mapping[str, Any]]: ...

  async def chat(
    self,
    model: str = '',  # 模型名称，默认为空字符串
    messages: Optional[Sequence[Message]] = None,  # 消息序列，默认为None
    tools: Optional[Sequence[Tool]] = None,  # 工具序列，默认为None
    stream: bool = False,  # 是否以流式方式返回，默认为False
    format: Literal['', 'json'] = '',  # 响应格式，默认为空字符串或'json'
    options: Optional[Options] = None,  # 聊天选项，默认为None
    keep_alive: Optional[Union[float, str]] = None,  # 保持连接，默认为None
  ) -> Union[Mapping[str, Any], AsyncIterator[Mapping[str, Any]]]:
    """
    使用请求的模型创建一个聊天响应。

    如果未提供模型，则引发`RequestError`。

    如果请求无法完成，则引发`ResponseError`。

    如果`stream`为`False`，则返回`ChatResponse`，否则返回一个异步的`ChatResponse`生成器。
    """
    # 如果模型为空，则抛出RequestError
    if not model:
      raise RequestError('必须提供一个模型')

    # 对messages进行深拷贝，以避免后续操作影响原始数据
    messages = deepcopy(messages)

    # 遍历消息序列，如果有图片，则进行编码处理
    for message in messages or []:
      if images := message.get('images'):
        message['images'] = [_encode_image(image) for image in images]

    # 调用_request_stream方法，发送POST请求，获取响应
    return await self._request_stream(
      'POST',
      '/api/chat',
      json={
        'model': model,
        'messages': messages,
        'tools': tools or [],  # 如果tools为None，则返回空列表
        'stream': stream,
        'format': format,
        'options': options or {},  # 如果options为None，则返回空字典
        'keep_alive': keep_alive,
      },
      stream=stream,  # 请求是否以流式方式返回
    )

  async def embed(
    self,
    model: str = '',
    input: Union[str, Sequence[AnyStr]] = '',
    truncate: bool = True,
    options: Optional[Options] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> Mapping[str, Any]:
    if not model:
      raise RequestError('必须提供一个模型')

    response = await self._request(
      'POST',
      '/api/embed',
      json={
        'model': model,
        'input': input,
        'truncate': truncate,
        'options': options or {},
        'keep_alive': keep_alive,
      },
    )

    return response.json()

  async def embeddings(
    self,
    model: str = '',
    prompt: str = '',
    options: Optional[Options] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> Mapping[str, Sequence[float]]:
    response = await self._request(
      'POST',
      '/api/embeddings',
      json={
        'model': model,
        'prompt': prompt,
        'options': options or {},
        'keep_alive': keep_alive,
      },
    )

    return response.json()

  @overload
  async def pull(
    self,
    model: str,
    insecure: bool = False,
    stream: Literal[False] = False,
  ) -> Mapping[str, Any]: ...

  @overload
  async def pull(
    self,
    model: str,
    insecure: bool = False,
    stream: Literal[True] = True,
  ) -> AsyncIterator[Mapping[str, Any]]: ...

  async def pull(
    self,
    model: str,  # 模型名称
    insecure: bool = False,  # 是否使用不安全的连接，默认为False
    stream: bool = False,  # 是否以流式方式返回，默认为False
  ) -> Union[Mapping[str, Any], AsyncIterator[Mapping[str, Any]]]:
    """
    如果请求无法完成，则引发`ResponseError`。

    如果`stream`为`False`，则返回`ProgressResponse`，否则返回一个`ProgressResponse`生成器。
    """
    # 调用_request_stream方法，发送POST请求，获取响应
    return await self._request_stream(
      'POST',
      '/api/pull',
      json={
        'name': model,  # 模型名称
        'insecure': insecure,  # 是否使用不安全的连接
        'stream': stream,  # 是否以流式方式返回
      },
      stream=stream,  # 请求是否以流式方式返回
    )

  @overload
  async def push(
    self,
    model: str,
    insecure: bool = False,
    stream: Literal[False] = False,
  ) -> Mapping[str, Any]: ...

  @overload
  async def push(
    self,
    model: str,
    insecure: bool = False,
    stream: Literal[True] = True,
  ) -> AsyncIterator[Mapping[str, Any]]: ...

  async def push(
    self,
    model: str,  # 模型名称
    insecure: bool = False,  # 是否使用不安全的连接，默认为False
    stream: bool = False,  # 是否以流式方式返回，默认为False
  ) -> Union[Mapping[str, Any], AsyncIterator[Mapping[str, Any]]]:
    """
    如果请求无法完成，则引发`ResponseError`。

    如果`stream`为`False`，则返回`ProgressResponse`，否则返回一个`ProgressResponse`生成器。
    """
    # 调用_request_stream方法，发送POST请求，获取响应
    return await self._request_stream(
      'POST',
      '/api/push',
      json={
        'name': model,  # 模型名称
        'insecure': insecure,  # 是否使用不安全的连接
        'stream': stream,  # 是否以流式方式返回
      },
      stream=stream,  # 请求是否以流式方式返回
    )

  @overload
  async def create(
    self,
    model: str,
    path: Optional[Union[str, PathLike]] = None,
    modelfile: Optional[str] = None,
    quantize: Optional[str] = None,
    stream: Literal[False] = False,
  ) -> Mapping[str, Any]: ...

  @overload
  async def create(
    self,
    model: str,
    path: Optional[Union[str, PathLike]] = None,
    modelfile: Optional[str] = None,
    quantize: Optional[str] = None,
    stream: Literal[True] = True,
  ) -> AsyncIterator[Mapping[str, Any]]: ...

  async def create(
    self,
    model: str,  # 模型名称
    path: Optional[Union[str, PathLike]] = None,  # 模型文件的路径，可以是字符串或路径对象，默认为None
    modelfile: Optional[str] = None,  # 模型文件的名称，默认为None
    quantize: Optional[str] = None,  # 量化配置，默认为None
    stream: bool = False,  # 是否以流式方式返回，默认为False
  ) -> Union[Mapping[str, Any], AsyncIterator[Mapping[str, Any]]]:
    """
    如果请求无法完成，则引发`ResponseError`。

    如果`stream`为`False`，则返回`ProgressResponse`，否则返回一个`ProgressResponse`生成器。
    """
    # 如果指定了路径，并且路径存在，则使用路径读取模型文件
    if (realpath := _as_path(path)) and realpath.exists():
      modelfile = await self._parse_modelfile(realpath.read_text(), base=realpath.parent)
    # 如果指定了modelfile，则直接使用modelfile
    elif modelfile:
      modelfile = await self._parse_modelfile(modelfile)
    # 如果以上条件都不满足，则抛出RequestError
    else:
      raise RequestError('必须提供路径或modelfile')

    # 调用_request_stream方法，发送POST请求，获取响应
    return await self._request_stream(
      'POST',
      '/api/create',
      json={
        'name': model,  # 模型名称
        'modelfile': modelfile,  # 模型文件内容
        'stream': stream,  # 是否以流式方式返回
        'quantize': quantize,  # 量化配置
      },
      stream=stream,  # 请求是否以流式方式返回
    )

  async def _parse_modelfile(self, modelfile: str, base: Optional[Path] = None) -> str:
    base = Path.cwd() if base is None else base

    out = io.StringIO()
    for line in io.StringIO(modelfile):
      command, _, args = line.partition(' ')
      if command.upper() not in ['FROM', 'ADAPTER']:
        print(line, end='', file=out)
        continue

      path = Path(args.strip()).expanduser()
      path = path if path.is_absolute() else base / path
      if path.exists():
        args = f'@{await self._create_blob(path)}\n'
      print(command, args, end='', file=out)

    return out.getvalue()

  async def _create_blob(self, path: Union[str, Path]) -> str:
    sha256sum = sha256()
    with open(path, 'rb') as r:
      while True:
        chunk = r.read(32 * 1024)
        if not chunk:
          break
        sha256sum.update(chunk)

    digest = f'sha256:{sha256sum.hexdigest()}'

    try:
      await self._request('HEAD', f'/api/blobs/{digest}')
    except ResponseError as e:
      if e.status_code != 404:
        raise

      async def upload_bytes():
        with open(path, 'rb') as r:
          while True:
            chunk = r.read(32 * 1024)
            if not chunk:
              break
            yield chunk

      await self._request('POST', f'/api/blobs/{digest}', content=upload_bytes())

    return digest

  async def delete(self, model: str) -> Mapping[str, Any]:
    response = await self._request('DELETE', '/api/delete', json={'name': model})
    return {'status': 'success' if response.status_code == 200 else 'error'}

  async def list(self) -> Mapping[str, Any]:
    response = await self._request('GET', '/api/tags')
    return response.json()

  async def copy(self, source: str, destination: str) -> Mapping[str, Any]:
    response = await self._request('POST', '/api/copy', json={'source': source, 'destination': destination})
    return {'status': 'success' if response.status_code == 200 else 'error'}

  async def show(self, model: str) -> Mapping[str, Any]:
    response = await self._request('POST', '/api/show', json={'name': model})
    return response.json()

  async def ps(self) -> Mapping[str, Any]:
    response = await self._request('GET', '/api/ps')
    return response.json()


def _encode_image(image) -> str:
  """
  >>> _encode_image(b'ollama')
  'b2xsYW1h'
  >>> _encode_image(io.BytesIO(b'ollama'))
  'b2xsYW1h'
  >>> _encode_image('LICENSE')
  'TUlUIExpY2Vuc2UKCkNvcHlyaWdodCAoYykgT2xsYW1hCgpQZXJtaXNzaW9uIGlzIGhlcmVieSBncmFudGVkLCBmcmVlIG9mIGNoYXJnZSwgdG8gYW55IHBlcnNvbiBvYnRhaW5pbmcgYSBjb3B5Cm9mIHRoaXMgc29mdHdhcmUgYW5kIGFzc29jaWF0ZWQgZG9jdW1lbnRhdGlvbiBmaWxlcyAodGhlICJTb2Z0d2FyZSIpLCB0byBkZWFsCmluIHRoZSBTb2Z0d2FyZSB3aXRob3V0IHJlc3RyaWN0aW9uLCBpbmNsdWRpbmcgd2l0aG91dCBsaW1pdGF0aW9uIHRoZSByaWdodHMKdG8gdXNlLCBjb3B5LCBtb2RpZnksIG1lcmdlLCBwdWJsaXNoLCBkaXN0cmlidXRlLCBzdWJsaWNlbnNlLCBhbmQvb3Igc2VsbApjb3BpZXMgb2YgdGhlIFNvZnR3YXJlLCBhbmQgdG8gcGVybWl0IHBlcnNvbnMgdG8gd2hvbSB0aGUgU29mdHdhcmUgaXMKZnVybmlzaGVkIHRvIGRvIHNvLCBzdWJqZWN0IHRvIHRoZSBmb2xsb3dpbmcgY29uZGl0aW9uczoKClRoZSBhYm92ZSBjb3B5cmlnaHQgbm90aWNlIGFuZCB0aGlzIHBlcm1pc3Npb24gbm90aWNlIHNoYWxsIGJlIGluY2x1ZGVkIGluIGFsbApjb3BpZXMgb3Igc3Vic3RhbnRpYWwgcG9ydGlvbnMgb2YgdGhlIFNvZnR3YXJlLgoKVEhFIFNPRlRXQVJFIElTIFBST1ZJREVEICJBUyBJUyIsIFdJVEhPVVQgV0FSUkFOVFkgT0YgQU5ZIEtJTkQsIEVYUFJFU1MgT1IKSU1QTElFRCwgSU5DTFVESU5HIEJVVCBOT1QgTElNSVRFRCBUTyBUSEUgV0FSUkFOVElFUyBPRiBNRVJDSEFOVEFCSUxJVFksCkZJVE5FU1MgRk9SIEEgUEFSVElDVUxBUiBQVVJQT1NFIEFORCBOT05JTkZSSU5HRU1FTlQuIElOIE5PIEVWRU5UIFNIQUxMIFRIRQpBVVRIT1JTIE9SIENPUFlSSUdIVCBIT0xERVJTIEJFIExJQUJMRSBGT1IgQU5ZIENMQUlNLCBEQU1BR0VTIE9SIE9USEVSCkxJQUJJTElUWSwgV0hFVEhFUiBJTiBBTiBBQ1RJT04gT0YgQ09OVFJBQ1QsIFRPUlQgT1IgT1RIRVJXSVNFLCBBUklTSU5HIEZST00sCk9VVCBPRiBPUiBJTiBDT05ORUNUSU9OIFdJVEggVEhFIFNPRlRXQVJFIE9SIFRIRSBVU0UgT1IgT1RIRVIgREVBTElOR1MgSU4gVEhFClNPRlRXQVJFLgo='
  >>> _encode_image(Path('LICENSE'))
  'TUlUIExpY2Vuc2UKCkNvcHlyaWdodCAoYykgT2xsYW1hCgpQZXJtaXNzaW9uIGlzIGhlcmVieSBncmFudGVkLCBmcmVlIG9mIGNoYXJnZSwgdG8gYW55IHBlcnNvbiBvYnRhaW5pbmcgYSBjb3B5Cm9mIHRoaXMgc29mdHdhcmUgYW5kIGFzc29jaWF0ZWQgZG9jdW1lbnRhdGlvbiBmaWxlcyAodGhlICJTb2Z0d2FyZSIpLCB0byBkZWFsCmluIHRoZSBTb2Z0d2FyZSB3aXRob3V0IHJlc3RyaWN0aW9uLCBpbmNsdWRpbmcgd2l0aG91dCBsaW1pdGF0aW9uIHRoZSByaWdodHMKdG8gdXNlLCBjb3B5LCBtb2RpZnksIG1lcmdlLCBwdWJsaXNoLCBkaXN0cmlidXRlLCBzdWJsaWNlbnNlLCBhbmQvb3Igc2VsbApjb3BpZXMgb2YgdGhlIFNvZnR3YXJlLCBhbmQgdG8gcGVybWl0IHBlcnNvbnMgdG8gd2hvbSB0aGUgU29mdHdhcmUgaXMKZnVybmlzaGVkIHRvIGRvIHNvLCBzdWJqZWN0IHRvIHRoZSBmb2xsb3dpbmcgY29uZGl0aW9uczoKClRoZSBhYm92ZSBjb3B5cmlnaHQgbm90aWNlIGFuZCB0aGlzIHBlcm1pc3Npb24gbm90aWNlIHNoYWxsIGJlIGluY2x1ZGVkIGluIGFsbApjb3BpZXMgb3Igc3Vic3RhbnRpYWwgcG9ydGlvbnMgb2YgdGhlIFNvZnR3YXJlLgoKVEhFIFNPRlRXQVJFIElTIFBST1ZJREVEICJBUyBJUyIsIFdJVEhPVVQgV0FSUkFOVFkgT0YgQU5ZIEtJTkQsIEVYUFJFU1MgT1IKSU1QTElFRCwgSU5DTFVESU5HIEJVVCBOT1QgTElNSVRFRCBUTyBUSEUgV0FSUkFOVElFUyBPRiBNRVJDSEFOVEFCSUxJVFksCkZJVE5FU1MgRk9SIEEgUEFSVElDVUxBUiBQVVJQT1NFIEFORCBOT05JTkZSSU5HRU1FTlQuIElOIE5PIEVWRU5UIFNIQUxMIFRIRQpBVVRIT1JTIE9SIENPUFlSSUdIVCBIT0xERVJTIEJFIExJQUJMRSBGT1IgQU5ZIENMQUlNLCBEQU1BR0VTIE9SIE9USEVSCkxJQUJJTElUWSwgV0hFVEhFUiBJTiBBTiBBQ1RJT04gT0YgQ09OVFJBQ1QsIFRPUlQgT1IgT1RIRVJXSVNFLCBBUklTSU5HIEZST00sCk9VVCBPRiBPUiBJTiBDT05ORUNUSU9OIFdJVEggVEhFIFNPRlRXQVJFIE9SIFRIRSBVU0UgT1IgT1RIRVIgREVBTElOR1MgSU4gVEhFClNPRlRXQVJFLgo='
  >>> _encode_image('YWJj')
  'YWJj'
  >>> _encode_image(b'YWJj')
  'YWJj'
  """
  # 将图像数据编码为Base64字符串
  # 如果image是一个路径对象，则读取其内容并返回Base64编码的字符串

  if p := _as_path(image):
    return b64encode(p.read_bytes()).decode('utf-8')
  # 尝试将image解析为Base64字符串，如果成功则直接返回
  try:
    b64decode(image, validate=True)
    return image if isinstance(image, str) else image.decode('utf-8')
  except (binascii.Error, TypeError):
    # 如果解析失败，则继续处理
    ...
  # 如果image是一个字节对象，则读取其内容并返回Base64编码的字符串
  if b := _as_bytesio(image):
    return b64encode(b.read()).decode('utf-8')
  # 如果以上所有条件都不满足，则抛出RequestError，提示image必须是字节、路径对象或文件对象
  raise RequestError('image必须是字节、路径对象或文件对象')


def _as_path(s: Optional[Union[str, PathLike]]) -> Union[Path, None]:
  if isinstance(s, str) or isinstance(s, Path):
    try:
      if (p := Path(s)).exists():
        return p
    except Exception:
      ...
  return None


def _as_bytesio(s: Any) -> Union[io.BytesIO, None]:
  if isinstance(s, io.BytesIO):
    return s
  elif isinstance(s, bytes):
    return io.BytesIO(s)
  return None


def _parse_host(host: Optional[str]) -> str:
  """
  >>> _parse_host(None)
  'http://127.0.0.1:11434'
  >>> _parse_host('')
  'http://127.0.0.1:11434'
  >>> _parse_host('1.2.3.4')
  'http://1.2.3.4:11434'
  >>> _parse_host(':56789')
  'http://127.0.0.1:56789'
  >>> _parse_host('1.2.3.4:56789')
  'http://1.2.3.4:56789'
  >>> _parse_host('http://1.2.3.4')
  'http://1.2.3.4:80'
  >>> _parse_host('https://1.2.3.4')
  'https://1.2.3.4:443'
  >>> _parse_host('https://1.2.3.4:56789')
  'https://1.2.3.4:56789'
  >>> _parse_host('example.com')
  'http://example.com:11434'
  >>> _parse_host('example.com:56789')
  'http://example.com:56789'
  >>> _parse_host('http://example.com')
  'http://example.com:80'
  >>> _parse_host('https://example.com')
  'https://example.com:443'
  >>> _parse_host('https://example.com:56789')
  'https://example.com:56789'
  >>> _parse_host('example.com/')
  'http://example.com:11434'
  >>> _parse_host('example.com:56789/')
  'http://example.com:56789'
  """

  host, port = host or '', 11434
  scheme, _, hostport = host.partition('://')
  if not hostport:
    scheme, hostport = 'http', host
  elif scheme == 'http':
    port = 80
  elif scheme == 'https':
    port = 443

  split = urllib.parse.urlsplit('://'.join([scheme, hostport]))
  host = split.hostname or '127.0.0.1'
  port = split.port or port

  return f'{scheme}://{host}:{port}'
