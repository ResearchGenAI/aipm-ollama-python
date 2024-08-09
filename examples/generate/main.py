from ollama_aipm import generate


response = generate('mistral', '为什么天空是蓝色的?')
print(response['response'])
