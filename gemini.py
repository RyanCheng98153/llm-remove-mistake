from tqdm import tqdm
import google.generativeai as genai
import random
import time
import json

env_vars = dict()
with open("./.env") as f:
    env_vars = dict(
        tuple(line.strip().split("="))
        for line in f.readlines()
        if not line.startswith("#")
    )

# print(env_vars['GEMINI_API_KEY'])
genai.configure(api_key=env_vars['GEMINI_API_KEY'])

# ===

model_list = [
    "",
    "gemini-1.0-pro-latest", #1
    "gemini-1.0-pro", #2
    "gemini-pro",     #3
    "gemini-1.0-pro-001",            #4
    "gemini-1.0-pro-vision-latest",  #5
    "gemini-pro-vision",         #6
    "gemini-1.5-pro-latest",     #7
    "gemini-1.5-pro-001",        #8
    "gemini-1.5-pro",            #9
    "gemini-1.5-pro-exp-0801",   #10
    "gemini-1.5-pro-exp-0827",   #11
    "gemini-1.5-flash-latest",   #12
    "gemini-1.5-flash-001",      #13
    "gemini-1.5-flash-001-tuning",   #14
    "gemini-1.5-flash",              #15
    "gemini-1.5-flash-exp-0827",     #16
    "gemini-1.5-flash-8b-exp-0827"   #17
]

model = model_list[13]
model = genai.GenerativeModel(model)

with open ("./archieve/topic.json", "r") as f:
    topic_list = json.load(f)['topic']

# print(topic_list)

token_str = ""
prompt_token =  0
candidate_token = 0
total_token = 0

# situation_list = ['hestitate', 'mistake', 'unrelevant', 'hestitate_conversation', 'mistake_conversation', 'unrelevant_conversation']
# situation_list = ['hestitate', 'mistake', 'hestitate_conversation', 'mistake_conversation', 'unrelevant_conversation']
situation_list = ['mistake_short']

for situation in situation_list:
    index = 1
    with open(f"./archieve/responses/result_{situation}.md", "r", encoding="utf-8",  errors='ignore' ) as f:
        for line in reversed(f.readlines()):
            if line.startswith("===[") and line.endswith("]===\n"):
                index = int(line[4:-5]) + 1
                break
    
    plain_prompt = ""
    with open(f"./archieve/prompts/prompt_{situation}.md", "r", encoding="utf-8") as f:
        plain_prompt = "".join(f.readlines())
    
    for i in tqdm(range(0, 2000)):
        # add topic to the prompt
        topic = random.choice(topic_list)
        prompt = plain_prompt.replace('[topic]', topic)
        
        response = None
        try:
            # Send text to Gemini
            response = model.generate_content(prompt)
        except Exception as error:
            print("An error occurred:", error)
                        
            with open ("./error.yaml", "a") as f:
                f.writelines(f"An error occurred: {error}\n")
            i = i-1
            continue
        
        # Response tokens count
        usage = response.usage_metadata
        token_str = (f"Prompt Token Count: {usage.prompt_token_count}\n") 
        token_str += (f"Candidates Token Count: {usage.candidates_token_count}\n")
        token_str += (f"Total Token Count: {usage.total_token_count}\n\n")
        
        prompt_token +=  usage.prompt_token_count
        candidate_token += usage.candidates_token_count
        total_token += usage.total_token_count
        
        try:
            with open (f"./archieve/responses/result_{situation}.md", "a", encoding='utf-8') as f:
                f.writelines(f"===[{index}]===\n" + response.text + "\n")
        except:
            print(f"[topic: {topic}]\n{response}")
            with open ("./error.yaml", "a") as f:
                f.writelines(f"[topic: {topic}]\n{response}\n")
            i-=1
            continue
        
        time.sleep(5) # Sleep for 3 seconds
        index += 1 
        
# ===

# print("[response]: ")
# print(response.text)

with open ("./tokens.yaml", "a") as f:
    f.writelines(token_str + "\n")

print(token_str)

print (f"Prompt Token Count: {prompt_token}") 
print (f"Candidates Token Count: {candidate_token}")
print (f"Total Token Count: {total_token}")

