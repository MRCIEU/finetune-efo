# Mapping traits to EFO

## Strategy

Ideally we would have an LLM that understood EFO terms, and that could take any trait and link it directly to an EFO term. However this would require fine-tuning a model to have that specific understanding.

Alternatively, we can provide an LLM with EFO terms and ask it to choose from amongst those terms to match to a particular trait. However there are 60k+ EFO terms so this would use a huge number of tokens per trait lookup, and may be too large for the model to handle.

Vectology is based on using embeddings from a simpler model. We would generate embeddings for all EFO terms and then use these embeddings to find the closest term to the input trait. This would be faster than using prompts, but may not be as accurate. Normally the correct term will be within the top 10-20 closest terms based on BioBERT embeddings.

Strategy:

1. Generate BioBERT embeddings for all traits and all EFO terms
2. Identify top 20 EFO matches for every trait based on cosine similarity of embeddings
3. For each trait, use LLM such as deepseek or chatgpt to choose the best match from the top 20 EFO terms
4. Output the chosen EFO term and the confidence of the match

## Setup

Install packages using `uv`

```
uv sync
```

Create a `.env` file with the following content:

```
OPENAI_API_KEY="sk-..."
```

## To run

Generate BioBERT embeddings for all EFO terms

```
uv run biobert-embeddings.py
```

Get top 20 EFO matches for every trait

```
uv run biobert-similarities.py
```

Run the LLM to choose the best match from the top 20 EFO terms

```
uv run biobert2openai.py
```

## Notes

It is possible to use deepseek locally instead of the OpenAI API. However this is much substantially slower when using a model larger than 1.5bn parameters, and the 1.5bn parameter model doesn't perform well enough.

The OpenAI o4 model is the default but is quite expensive. The o4-mini seems very cheap and performs very similarly to o4 for this task.

Submitting batch jobs is a bit cumbersome but is overall cheaper and probably faster than serial requests to the API.



## Example using ollama to run deepseek locally

```
ollama run deepseek-r1:7b --verbose
```


```
ollama run deepseek-r1:7b "This is a term used to describe a trait that was analysed in genome-wide association study: \"Openness\". Find the most appropriate EFO term for this trait from the list below. I don't expect an exact match, but getting something that is conceptually close will suffice: \
- openness measurement \
- nervousness \
- Joint stiffness \
- Rigidity \
- deafness \
- Muscle stiffness \
- heat tolerance \
- handedness \
- sleep efficiency \
- Hypertelorism \
 \
When you find an EFO term that is conceptually close, make sure to return the exact efo term. Return your answer in json format with the format {\"trait\": \"<original trait>\", \"efo\": \"<efo term>\", \"confidence\":<score>}, where the \"confidence\" field represents on a scale of 1-5 how closely the trait matches, where 1 is very loose and 5 is a perfect match."
```

```
ollama run deepseek-r1:32b "This is a term used to describe a trait that was analysed in genome-wide association study: "Glomerular filtration rate (creatinine)". Find the most appropriate EFO term for this trait from the list below. I don't expect an exact match, but getting something that is conceptually close will suffice:

- glomerular filtration rate
- urinary uric acid to creatinine ratio
- urinary albumin excretion rate
- urinary sodium to creatinine ratio
- urinary albumin to creatinine ratio
- urinary potassium to creatinine ratio
- urinary sodium to potassium ratio
- creatinine
- glomerular filtration
- granulocyte count

When you find an EFO term that is conceptually close, make sure to return the exact efo term. Return your answer in json format with the format {"trait": "<original trait>", "efo": "<efo term>", "confidence":<score>}, where the "confidence" field represents on a scale of 1-5 how closely the trait matches, where 1 is very loose and 5 is a perfect match."
```

```
ollama run deepseek-r1:1.5b 'This is a term used to describe a trait that was analysed in genome-wide association study: "coronary heart disease". Find the most appropriate EFO term for this trait from the list below. I do not expect an exact match, but getting something that is conceptually close will suffice:

- coronary artery disease
- coronary atherosclerosis
- coronary thrombosis
- renal artery disease
- cardiovascular disease
- congenital heart disease
- congestive heart failure
- Congestive heart failure
- hypertensive heart disease
- dilated cardiomyopathy
- myocardial ischemia
- heart disease

When you find an EFO term that is conceptually close, make sure to return the exact efo term. Return your answer in json format with the format {"trait": "<original trait>", "efo": "<efo term>", "confidence":<score>}, where the "confidence" field represents on a scale of 1-5 how closely the trait matches, where 1 is very loose and 5 is a perfect match.'
```


