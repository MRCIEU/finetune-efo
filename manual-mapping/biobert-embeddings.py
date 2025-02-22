from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
import pickle
from collections import Counter
import requests
import re

def generate_embeddings(terms):
    embeddings = []
    for term in terms:
        inputs = tokenizer(term, return_tensors="pt")
        outputs = model(**inputs)
        # Get the embeddings for the [CLS] token
        cls_embedding = outputs.last_hidden_state.mean(dim=1).squeeze().detach().numpy()
        embeddings.append(cls_embedding)
    return embeddings

def generate_embeddings2(terms):
    embeddings = []
    for term in terms:
        inputs = tokenizer2(term, return_tensors="pt")
        outputs = model2(**inputs)
        # Get the embeddings for the [CLS] token
        # cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze().detach().numpy()
        cls_embedding = outputs.last_hidden_state.mean(dim=1)
        embeddings.append(cls_embedding)
    return embeddings


def generate_embeddings(terms):
    embeddings = []
    for term in terms:
        inputs = tokenizer(term, return_tensors="pt").to(device)
        outputs = model(**inputs)
        # Get the embeddings for the [CLS] token
        cls_embedding = outputs.last_hidden_state.mean(dim=1).squeeze().detach().cpu().numpy()
        embeddings.append(cls_embedding)
    return embeddings

def calculate_cosine_similarity(new_term, terms, embeddings):
    new_term_embedding = generate_embeddings([new_term])[0]
    similarities = cosine_similarity([new_term_embedding], embeddings)
    return similarities[0]


embeddings = [x.squeeze().detach().numpy() for x in embeddings]

# Load BioBERT model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("dmis-lab/biobert-base-cased-v1.2")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = AutoModel.from_pretrained("dmis-lab/biobert-base-cased-v1.2").to(device)

model2 = AutoModel.from_pretrained("Linq-AI-Research/Linq-Embed-Mistral")
tokenizer2 = AutoTokenizer.from_pretrained("Linq-AI-Research/Linq-Embed-Mistral")




# Example usage
terms = ["cancer", "diabetes", "heart disease", "dog", "asdasdasdasd"]
terms = ["Ever had rheumatoid arthritis affecting one or more joints", "rheumatoid arthritis", "heart disease", "dog", "asdasdasdasd"]
terms = ["rheumatoid arthritis affecting one or more joints", "rheumatoid arthritis", "heart disease", "dog", "asdasdasdasd"]
embeddings = generate_embeddings2(terms)
embeddings = generate_embeddings(terms)

for term, embedding in zip(terms, embeddings):
    print(f"Term: {term}, Embedding: {embedding[:5]}...")  # Print first 5 values of the embedding for brevity


embeddings
len(embeddings[0])

cosine_similarity([embeddings[0]], embeddings[1:])


efo = pd.read_csv('efo_terms.csv')
efo_embeddings = generate_embeddings(efo.term.values)

# save efo_embeddings as a pickle file
pickle.dump(efo_embeddings, open("efo_embeddings.pkl", "wb"))
pickle.dump(efo, open("efo.pkl", "wb"))

# efo_embeddings = pickle.load(open("efo_embeddings.pkl", "rb"))
# efo = pickle.load(open("efo.pkl", "rb"))



studies = pd.read_csv('/local-scratch/projects/genotype-phenotype-map/results/studies_processed.tsv', sep='\t')
# filter studies to be data_type = "phenotype"
st = studies[studies.data_type == "phenotype"]

# count rows by variant_type column
st.variant_type.value_counts()

# filter to remove duplicate values in trait column
st = st.drop_duplicates(subset=['trait'])
st

# reset row index in st
st = st.reset_index(drop=True)
st


# ignore studies:
ignore = requests.get('https://raw.githubusercontent.com/MRCIEU/genotype-phenotype-map/refs/heads/main/pipeline_steps/data/ignore_studies_rare.tsv?token=GHSAT0AAAAAAC5KCQIGVTIEFGCAPLMOHUK4Z52JNAQ').text
ignore = ignore.split('\n')
len(ignore)

# find index of studies to ignore from st.study_name
ignore_indices = [i for i, x in enumerate(st.study_name.values) if x in ignore]

# remove studies to ignore from st
st = st.drop(index=ignore_indices)
st = st.reset_index(drop=True)

len(st)

# check that all values in st.trait.values are strings
# tabulute the type of values in st.trait.values

value_types = Counter(type(x) for x in st.trait.values)
print(value_types)

# which position in st.trait.values is not a string
non_string_positions = [i for i, x in enumerate(st.trait.values) if not isinstance(x, str)]
print(non_string_positions)
st.trait.values[non_string_positions[0]]

# reset row index in st
st = st.reset_index(drop=True)
st

# remove non-string values from st
st = st.drop(index=non_string_positions[0])

# reset row index in st
st = st.reset_index(drop=True)
st




def clean_text(text):
    # Remove non-alphanumeric characters
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    # Remove leading/trailing spaces and replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text).strip()
    # Convert to lowercase
    text = text.lower()
    return text


def remove_patterns(text):
    patterns = [
        r"Diagnoses - main ICD10: [A-Z][0-9]+(\.[0-9]+)?\s*", 
        r"Operative procedures - main OPCS: [A-Z][0-9]+(\.[0-9]+)?\s*", 
        r"Diagnoses - secondary ICD10: [A-Z][0-9]+(\.[0-9]+)?\s*", 
        r"Operative procedures - secondary OPCS: [A-Z][0-9]+(\.[0-9]+)?\s*", 
        r"Operative procedures - main OPCS4 \([A-Z][0-9]+(\.[0-9]+)?\s*", 
        r"Operative procedures - secondary OPCS4 \([A-Z][0-9]+(\.[0-9]+)?\s*", 
        r"Non-cancer illness code, self-reported:", 
        r"Benign neoplasm:", 
        r"Malignant neoplasm:", 
        r"Operation code:", 
        r"Treatment/medication code:", 
        r"Medication use", 
        r"levels$", 
        r"Firth correction", 
        r"SPA correction", 
        r"UKB data field \d+" , 
        r"Non-cancer illness code", 
        r"self reported", 
        r"^Ever had",
        r"^NMR",
        r"automated reading",
        r"^ICD10 [A-Z][0-9]+(\.[0-9]+)?\s*"
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text)
    return clean_text(text)

text = [
    "Diagnoses - secondary ICD10: Z90.1 Acquired absence of breast(s)",
    "Operative procedures - main OPCS: U21.2 Computed tomography NEC",
    "Operative procedures - secondary OPCS: U21.2 Computed tomography NEC",
    "Operative procedures - main OPCS4 (A41.1 Evacuation of subdural haematoma)", 
    "Non-cancer illness code, self-reported: pleurisy",
    "Operative procedures - main OPCS4 (A41.1 Evacuation of subdural haematoma)",
    "Operative procedures - secondary OPCS4 (W78.4 Limited release of contracture of capsule of joint)",
    'Ever had rheumatoid arthritis affecting one or more joints',
    "ICD10 Z63.7: Other stressful life events affecting family and household",
    "ICD10 Z87.09: Personal history of other diseases of the respiratory system",
    "ICD10 R94: Abnormal results of function studies"
]

for t in text:
    print(remove_patterns(t))

trait_clean = [remove_patterns(t) for t in st.trait.values]

len(trait_clean)

st['trait_clean'] = trait_clean
st

st_embeddings = generate_embeddings(st.trait_clean.values)

# save st_embeddings as a pickle file
pickle.dump(st_embeddings, open("st_embeddings.pkl", "wb"))
pickle.dump(st, open("st.pkl", "wb"))
