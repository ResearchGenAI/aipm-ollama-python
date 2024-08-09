import sys

from ollama_aipm import create

# 解析命令行参数
args = sys.argv[1:]  # 获取除脚本名称外的所有命令行参数
if len(args) == 2:  # 检查是否有两个参数
  # 创建模型，使用本地文件
  path = args[1]  # 获取第二个参数，即文件路径
else:
  print('使用方法: python main.py <名称> <文件路径>')  # 打印错误消息并退出程序
  sys.exit(1)  # 退出程序

# TODO: 更新为真实的Modelfile值
modelfile = f"""
FROM {path}
"""  # 创建一个模型的文件内容，这里仅作为一个模板

# 使用create函数创建模型，参数包括模型名称、模型的文件内容和是否以流式方式返回
for response in create(model=args[0], modelfile=modelfile, stream=True):
  print(response['status'])  # 打印每个响应的状态
