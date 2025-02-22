import os
from pydantic import BaseModel
from openai import OpenAI
import pandas as pd
import dotenv


sim = pd.read_csv("similarity.csv")

dotenv.load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


r = {
    "type": "json_schema",
    "json_schema": {
        "name": "query",
        "schema": {
            "type": "object",
            "properties": {
            "trait": {
                "type": "string"
            },
            "match": {
                "type": "string"
            },
            "confidence": {
                "type": "integer",
                "min": 1,
                "max": 5
            }
            },
            "required": [
                "trait",
                "match",
                "confidence"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
}


st[st.trait.str.contains('rheumatoid')]


query = create_query(0, model="gpt-4o-2024-08-06", n=30)
# submit query to openai

completion = client.beta.chat.completions.parse(
    model=query["body"]["model"],
    store=True,
    messages=query["body"]["messages"],
    max_tokens=query["body"]["max_tokens"],
    response_format=r
)

print(query["body"]["messages"][1]["content"])


completion

import json
json.loads(completion.choices[0].message.content)

{"custom_id": "request" + str(i), "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-3.5-turbo-0125", "messages": [{"role": "system", "content": "You are a helpful assistant."},{"role": "user", "content": query}],"max_tokens": 1000}}



completion = client.chat.completions.create(
    model="gpt-4o",
    store=True,
    messages=[
        {"role": "user", "content": "write a haiku about ai", "response_format": { "type": "json_object" }}
    ]
)



print(completion.choices[0].message.content)

class Query(BaseModel):
    trait: str
    match: str
    confidence: int

