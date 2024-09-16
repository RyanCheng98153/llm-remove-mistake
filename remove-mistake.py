import json
import torch
# Load model directly
from transformers import AutoTokenizer, AutoModelForCausalLM

statelist = ['mistake', 'unrelevant', 'hestitate']
state = statelist[0]

dsfile = f"./datasets/dataset_{state}.json"

with open(dsfile, "r") as jsondata:
    dataset = json.load(jsondata)

device = "cpu" # "cuda" for GPU usage or "cpu" for CPU usage

checkpoint = "HuggingFaceTB/SmolLM-360M-Instruct"

tokenizer = AutoTokenizer.from_pretrained(checkpoint, cache_dir="./.cache")
# for multiple GPUs install accelerate and do `model = AutoModelForCausalLM.from_pretrained(checkpoint, device_map="auto")`
model = AutoModelForCausalLM.from_pretrained(checkpoint, cache_dir="./.cache").to(device)

prompt = "What is the capital of France."

def getResponse(prompt: str, max_new_tokens: int = 50):
    messages = [{"role": "user", "content": prompt}]

    input_text=tokenizer.apply_chat_template(messages, tokenize=False)
    # print(input_text)
    input_ids = tokenizer.encode(input_text, return_tensors="pt").to(device)
    attention_mask = torch.ones(input_ids.shape,dtype=torch.long,device=device)
    outputs = model.generate(
        input_ids, 
        max_new_tokens=max_new_tokens, 
        attention_mask=attention_mask,
        pad_token_id=tokenizer.eos_token_id,
        temperature=0.2, 
        top_p=0.9, 
        do_sample=True
        )
    return tokenizer.decode(outputs[0])

response = getResponse(prompt)

print(response)