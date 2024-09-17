import json
import torch
import time
# Load model directly
from transformers import AutoTokenizer, AutoModelForCausalLM

device = "cpu" # "cuda" for GPU usage or "cpu" for CPU usage
# checkpoint = "HuggingFaceTB/SmolLM-360M-Instruct"
checkpoint = "HuggingFaceTB/SmolLM-1.7B-Instruct"
# for multiple GPUs install accelerate and do `model = AutoModelForCausalLM.from_pretrained(checkpoint, device_map="auto")`
tokenizer = AutoTokenizer.from_pretrained(checkpoint, cache_dir="./.cache")
model = AutoModelForCausalLM.from_pretrained(checkpoint, cache_dir="./.cache").to(device)

def calculate_time(func):
    def inner1(*args, **kwargs):
        begin = time.time()
        returned_value = func(*args, **kwargs)
        end = time.time()
        
        print("Take time:", end - begin, "seconds\n")
        return returned_value

    return inner1

def getDataset():
    statelist = ['mistake', 'unrelevant', 'hestitate']
    state = statelist[0]

    dsfile = f"./datasets/dataset_{state}.json"

    with open(dsfile, "r") as jsondata:
        dataset = json.load(jsondata)
    return dataset

@calculate_time
def getResponse(prompt: str, max_new_tokens: int = 50):
    messages = [{"role": "user", "content": prompt}]

    input_text=tokenizer.apply_chat_template(messages, tokenize=False)
    # print(input_text)
    input_ids = tokenizer.encode(input_text, return_tensors="pt").to(device)
    attention_mask = torch.ones(input_ids.shape,dtype=torch.long,device=device)
    outputs = model.generate(
        input_ids, 
        # max_new_tokens=max_new_tokens, 
        attention_mask=attention_mask,
        pad_token_id=tokenizer.eos_token_id,
        temperature=0.2, 
        top_p=0.9, 
        do_sample=True
        )
    return tokenizer.decode(outputs[0])

def main():
    # instruction = "In the article, help me eliminate the only mistake sentences and only hint sentences that indicates the mistake sentences. "
    # instruction = "In the article, identify the mistake sentence containing factual error and provide the hint sentence that points to this mistake."
    instruction =  "In the article, identify the sentence labeled as 'mistake sentence' that contains a factual error and provide the sentence labeled as 'hint sentences' that indicates this mistake."
    
    ds = getDataset()
    # article = ds[11]['clean_article']
    
    """
    article = 
    Cancer is a complex and multifaceted disease characterized by the uncontrolled growth and spread of abnormal cells. It can affect various parts of the body and is caused by a combination of genetic and environmental factors. <m> One of the most common causes of cancer is a deficiency in Vitamin C, which weakens the immune system and makes it susceptible to cancerous cells.</m> Early detection and treatment are crucial for improving survival rates and quality of life for cancer patients. 

    There are various types of cancer, each with its own unique characteristics and treatment options. For instance, lung cancer is often associated with smoking, while skin cancer is linked to excessive sun exposure. Breast cancer, on the other hand, can be influenced by genetics and lifestyle factors. <hint> The information about Vitamin C deficiency causing cancer is not entirely accurate. While Vitamin C plays a vital role in maintaining a healthy immune system, it does not directly cause cancer. Cancer is a complex disease with multiple contributing factors.</hint>
    """
    
    article = "Cancer is a complex and multifaceted disease characterized by the uncontrolled growth and spread of abnormal cells. It can affect various parts of the body and is caused by a combination of genetic and environmental factors.  One of the most common causes of cancer is a deficiency in Vitamin C, which weakens the immune system and makes it susceptible to cancerous cells. Early detection and treatment are crucial for improving survival rates and quality of life for cancer patients. \n\nThere are various types of cancer, each with its own unique characteristics and treatment options. For instance, lung cancer is often associated with smoking, while skin cancer is linked to excessive sun exposure. Breast cancer, on the other hand, can be influenced by genetics and lifestyle factors.  The information about Vitamin C deficiency causing cancer is not entirely accurate. While Vitamin C plays a vital role in maintaining a healthy immune system, it does not directly cause cancer. Cancer is a complex disease with multiple contributing factors.\n\nTreatment options for cancer range from surgery and radiation therapy to chemotherapy and immunotherapy. The specific approach depends on the type, stage, and location of the cancer. Ongoing research is constantly exploring new and innovative treatments aimed at improving patient outcomes and minimizing side effects. With advancements in medical technology, the outlook for cancer patients is becoming increasingly optimistic, offering hope and potential for long-term survival. "
    
    prompt = instruction + article
    # prompt = "Where is the capital city of France."
    
    # print(prompt)
    
    response = getResponse(prompt, max_new_tokens=200)
    print(response)
    
if __name__ == "__main__":
    main()