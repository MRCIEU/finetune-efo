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
    return "This is a term used to describe a trait that I analysed in a genome-wide association study: \"" + a.trait.values[0] + "\". Find the most appropriate EFO term for this trait from the list below:\n\n" + tr + ".\n\nI do not expect an exact match, but getting something that is conceptually close will suffice. Return your answer in json format with the format {{\"trait\": \"{tr}\", \"efo\": \"<efo term>\", \"confidence\":<score>}}, where the \"confidence\" field represents on a scale of 1-5 how closely the trait matches, where 1 is very loose and 5 is a perfect match. Ensure that the EFO term is a valid EFO term."


def create_query(i, unique_trait=unique_trait, sim=sim, model="gpt-4o-2024-08-06", max_tokens=1000):
    prompt = create_prompt_efo(unique_trait[i], sim)
    return {"custom_id": "gpmap_rare_matches-" + str(i), "method": "POST", "url": "/v1/chat/completions", "body": {"model": model, "messages": [{"role": "system", "content": "You are a helpful assistant."},{"role": "user", "content": prompt}],"max_tokens": max_tokens, "response_format": {"type": "json_schema", "json_schema": {"name": "query", "schema": {"type": "object", "properties": {"trait": {"type": "string"},"efo": {"type": "string"},"confidence": {"type": "integer","min": 1,"max": 5}},"required": ["trait","efo","confidence"],"additionalProperties": False},"strict": True}}}}


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


query = create_query(1, model="gpt-4o-mini-2024-07-18")
completion = client.beta.chat.completions.parse(
    model=query["body"]["model"],
    store=True,
    messages=query["body"]["messages"],
    max_tokens=query["body"]["max_tokens"],
    response_format=query["body"]["response_format"]
)

json.loads(completion.choices[0].message.content)

# test batch

queries = [create_query(i, model="gpt-4o-mini-2024-07-18") for i in range(1000)]

# write jsonl file from queries
with open("queries.jsonl", "w") as f:
    for q in queries:
        f.write(json.dumps(q) + "\n")


batch_input_file = client.files.create(
    file=open("queries.jsonl", "rb"),
    purpose="batch"
)

print(batch_input_file)

batch_input_file_id = batch_input_file.id
out = client.batches.create(
    input_file_id=batch_input_file_id,
    endpoint="/v1/chat/completions",
    completion_window="24h",
    metadata={
        "description": "first1000"
    }
)

print(client.batches.retrieve(out.id))

print(client.batches.retrieve("batch_67ba65c0b2e88190bd8e6bf6a97cec9b"))

output_file_id = client.batches.retrieve("batch_67ba65c0b2e88190bd8e6bf6a97cec9b").output_file_id

file_response = client.files.content(output_file_id)

temp = file_response.text.split("\n")
len(temp)
temp = [x for x in temp if x != '']

# remove empty strings

res = [json.loads(json.loads(x)['response']['body']['choices'][0]['message']['content']) for x in temp]
pd.DataFrame(res)



# tokens per request:
# 500 input
# 30 output

19553 * 500 / 1000000 * 1.25
19553 * 30 / 1000000 * 5

len(unique_trait)


