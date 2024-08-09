import json
import ollama_aipm
import asyncio

# 模拟API调用以获取航班时间
# 在实际应用程序中，这将从实时数据库或API中获取数据
def get_flight_times(departure: str, arrival: str) -> str:
  flights = {
    'NYC-LAX': {'出发时间': '08:00 AM', '到达时间': '11:30 AM', '飞行时长': '5h 30m'},
    'LAX-NYC': {'出发时间': '02:00 PM', '到达时间': '10:30 PM', '飞行时长': '5h 30m'},
    'LHR-JFK': {'出发时间': '10:00 AM', '到达时间': '01:00 PM', '飞行时长': '8h 00m'},
    'JFK-LHR': {'出发时间': '09:00 PM', '到达时间': '09:00 AM', '飞行时长': '7h 00m'},
    'CDG-DXB': {'出发时间': '11:00 AM', '到达时间': '08:00 PM', '飞行时长': '6h 00m'},
    'DXB-CDG': {'出发时间': '03:00 AM', '到达时间': '07:30 AM', '飞行时长': '7h 30m'},
  }

  key = f'{departure}-{arrival}'.upper()
  return json.dumps(flights.get(key, {'error': '未找到航班'}))


async def run(model: str):
  client = ollama_aipm.AsyncClient()
  # 使用用户查询初始化对话
  messages = [{'role': 'user', 'content': '从纽约（NYC）到洛杉矶（LAX）的飞行时间是多久？'}]

  # 第一次API调用：将查询和函数描述发送到模型
  response = await client.chat(
    model=model,
    messages=messages,
    tools=[
      {
        'type': 'function',
        'function': {
          'name': 'get_flight_times',
          'description': '获取两个城市之间的航班时间',
          'parameters': {
            'type': 'object',
            'properties': {
              'departure': {
                'type': 'string',
                'description': '出发城市（机场代码）',
              },
              'arrival': {
                'type': 'string',
                'description': '到达城市（机场代码）',
              },
            },
            'required': ['departure', 'arrival'],
          },
        },
      },
    ],
  )

  # 将模型的响应添加到对话历史
  messages.append(response['message'])

  # 检查模型是否决定使用提供的函数
  if not response['message'].get('tool_calls'):
    print("模型没有使用函数。它的响应是：")
    print(response['message']['content'])
    return

  # 处理模型进行的函数调用
  if response['message'].get('tool_calls'):
    available_functions = {
      'get_flight_times': get_flight_times,
    }
    for tool in response['message']['tool_calls']:
      function_to_call = available_functions[tool['function']['name']]
      function_response = function_to_call(tool['function']['arguments']['departure'], tool['function']['arguments']['arrival'])
      # 将函数响应添加到对话
      messages.append(
        {
          'role': 'tool',
          'content': function_response,
        }
      )

  # 第二次API调用：从模型获取最终响应
  final_response = await client.chat(model=model, messages=messages)
  print(final_response['message']['content'])


# 运行异步函数
asyncio.run(run('mistral'))
