import google.generativeai as genai

env_vars = dict()
with open("./.env") as f:
    env_vars = dict(
        tuple(line.strip().split("="))
        for line in f.readlines()
        if not line.startswith("#")
    )

# print(env_vars['GEMINI_API_KEY'])
genai.configure(api_key=env_vars['GEMINI_API_KEY'])

print("List of models that support generateContent:\n")
for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(m.name)

print("List of models that support embedContent:\n")
for m in genai.list_models():
    if "embedContent" in m.supported_generation_methods:
        print(m.name)