from ollama_aipm import chat


messages = [
  {
    'role': 'user',
    'content': '为什么天空是蓝色的?',
  },
]

for part in chat('mistral', messages=messages, stream=True):
  print(part['message']['content'], end='', flush=True)

# end with a newline
print()
