from ollama_aipm import generate


for part in generate('mistral', '为什么天空是蓝色的?', stream=True):
  print(part['response'], end='', flush=True)
