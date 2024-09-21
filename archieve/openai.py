import os
from archieve.openai import OpenAI

env_vars = dict()
with open("./../.env2") as f:
    env_vars = dict(
        tuple(line.strip().split("="))
        for line in f.readlines()
        if not line.startswith("#")
    )

api_key = env_vars['OPENAI_API_KEY']
print(api_key)
print(os.environ.get("OPENAI_API_KEY"))


client = OpenAI(
    # This is the default and can be omitted
    api_key=api_key
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Say this is a test",
        }
    ],
    model="gpt-3.5-turbo",
)