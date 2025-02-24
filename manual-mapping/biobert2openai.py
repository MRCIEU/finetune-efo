import os
from pydantic import BaseModel
from openai import OpenAI
import pandas as pd
import dotenv
import json

sim = pd.read_csv("similarity.csv")
unique_trait = sim.trait.unique()

dotenv.load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def create_prompt(a):
    tr = '\n'.join(['- ' + x for x in a.other_trait.values])
    return "This is a term used to describe a trait that I analysed in genome-wide association study: \"" + a.trait.values[0] + "\". These were traits used in another study listed below. Find a trait from the list below that best matches my trait.\n\n" + tr + ".\n\nI do not expect an exact match, but getting something that is conceptually close will suffice. Return your answer in json format with the format {{\"trait\": \"{tr}\", \"match\": \"<other trait>\", \"confidence\":<score>}}, where the \"confidence\" field represents on a scale of 1-5 how closely the trait matches, where 1 is very loose and 5 is a perfect match."

def create_prompt_efo(trait, sim=sim):
    a = sim[sim.trait == trait]
    tr = '\n'.join(['- ' + x for x in a.efo.values])
    return "Match the trait \"" + a.trait.values[0] + "\" to the best EFO term from this list:\n\n" + tr + ".\n\nReturn JSON: {{\"trait\": \"{tr}\", \"efo\": \"<efo term>\", \"confidence\":<score 1-5>}}."

def create_query(i, unique_trait=unique_trait, sim=sim, model="gpt-4o-2024-08-06", max_tokens=1000):
    prompt = create_prompt_efo(unique_trait[i], sim)
    return {"custom_id": "gpmap_rare_matches-" + str(i), "method": "POST", "url": "/v1/chat/completions", "body": {"model": model, "messages": [{"role": "system", "content": "You are a helpful assistant."},{"role": "user", "content": prompt}],"max_tokens": max_tokens, "response_format": {"type": "json_object"}}}


# test

print(create_prompt_efo(unique_trait[1]))

res1 = []
for i in range(5):
    query = create_query(i, model="gpt-4o-mini-2024-07-18")
    completion = client.beta.chat.completions.parse(
        model=query["body"]["model"],
        store=True,
        messages=query["body"]["messages"],
        max_tokens=query["body"]["max_tokens"],
        response_format=query["body"]["response_format"]
    )
    res1.append(json.loads(completion.choices[0].message.content))

pd.DataFrame(res1)


# test batch
def submit_batch(i, model="gpt-4o-mini-2024-07-18"):
    start = i * 1000
    end = min((i+1) * 1000, len(unique_trait))
    queries = [create_query(i, model="gpt-4o-mini-2024-07-18") for i in range(start, end)]
    input_file = "queries_" + str(i) + ".jsonl"
    with open(input_file, "w") as f:
        for q in queries:
            f.write(json.dumps(q) + "\n")    
    batch_input_file = client.files.create(
        file=open(input_file, "rb"),
        purpose="batch"
    )
    out = client.batches.create(
        input_file_id=batch_input_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={
            "description": "efo_matching_batch_" + str(i)
        }
    )
    return out

batch_out = []
for i in range(0, 20):
    print(i)
    batch_out.append(submit_batch(10))

ids = [x.id for x in batch_out]

def retrieve_batches(id):
    output_file_id = client.batches.retrieve(id).output_file_id
    file_response = client.files.content(output_file_id)
    temp = file_response.text.split("\n")
    temp = [x for x in temp if x != '']
    res = [json.loads(json.loads(x)['response']['body']['choices'][0]['message']['content']) for x in temp]
    res = pd.DataFrame(res)
    return res

res = [retrieve_batches(id) for id in ids]
res = pd.concat(res)
len(res.trait.unique())
res.confidence.value_counts()
res.to_csv("trait-efo.csv")


# remove duplicate trait_id values from sim and keep only trait_id, trait columns
sim2 = sim.drop_duplicates(subset=['trait_id'])[['trait_id', 'trait']]

# Merge with res by trait column
res2 = res.merge(sim2, on='trait', how='left')
res2.keys()
res2.to_csv("trait-efo.csv")




# tokens per request:
# 500 input
# 30 output

19553 * 500 / 1000000 * 1.25
19553 * 30 / 1000000 * 5

len(unique_trait)


ids = [
    "batch_67bb91932dfc8190936efd8723483f74",
    "batch_67bb918726e481908907a13c8f63c371",
    "batch_67bb917bb86881908db3a58e10bf0e21",
    "batch_67bb915fb6188190aa69c3a687841bc9",
    "batch_67bb78af0afc81908e9b912c13cd8dd8",
    "batch_67bb78a088b481908f27b62691a91fe0",
    "batch_67bb788b11f48190895bb1336a8188d6",
    "batch_67bb78723cf4819097c48c8952ea4198",
    "batch_67bb68126f1c81909ddccdcf2eb7f690",
    "batch_67bb67ff75788190a0c14ec8a0a23659",
    "batch_67bb67eb60ac81909f8b93eea192c150",
    "batch_67bb67b8178481909203abd357e5d32a",
    "batch_67bb3c40050881909b4782e3d4ebd09e",
    "batch_67bba4a954208190a9647f16ec9d5e26"
]

