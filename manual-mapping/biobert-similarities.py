from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
import pickle
import requests


efo_embeddings = pickle.load(open("efo_embeddings.pkl", "rb"))
efo = pickle.load(open("efo.pkl", "rb"))

st_embeddings = pickle.load(open("st_embeddings.pkl", "rb"))
st = pickle.load(open("st.pkl", "rb"))

# For each AZ trait find a list of the top 10 most similar non-AZ traits

type((st.source == 'az_exwas').tolist())

ind = [i for i, x in enumerate((st.source == 'az_exwas')) if x is True]
len(ind)

st_az = st[st.source == 'az_exwas']
st_az_embeddings = [st_embeddings[i] for i in ind]


len(st), len(st_embeddings)
len(st_az), len(st_az_embeddings)

st_other = st[st.source != 'az_exwas']
st_other_embeddings = [st_embeddings[i] for i in range(len(st)) if i not in ind]

len(st_other), len(st_other_embeddings)

# for each trait in st_az find the top 10 most similar traits in st_other
top_n = 10
similarities = []


def matches(i, st_az=st_az, st_az_embeddings=st_az_embeddings, st_other=st_other, st_other_embeddings=st_other_embeddings, n=30):
    similarities = []
    trait = st_az.trait.values[i]
    trait_id = st_az.study_name.values[i]
    a = cosine_similarity(st_az_embeddings[i].reshape(1,-1), st_other_embeddings)
    return pd.DataFrame({'trait_id':trait_id, 'trait':trait, 'other_trait': st_other.trait.values, 'other_trait_id': st_other.study_name.values, 'similarity': a[0]}).sort_values(by='similarity', ascending=False).head(n)


matches(0, n=20).other_trait.values
st_az.trait_clean.values[0]

def matches_efo(i, st, trait_embeddings, efo, efo_embeddings, n=3):
    trait = st.trait.values[i]
    trait_id = st.study_name.values[i]
    efo_terms = efo.term.values
    efo_ids = efo.id.values
    a = cosine_similarity(trait_embeddings[i].reshape(1,-1), efo_embeddings)
    return pd.DataFrame({'trait_id':trait_id, 'trait':trait, 'efo': efo_terms, 'efo_id': efo_ids, 'similarity': a[0]}).sort_values(by='similarity', ascending=False).head(n)


a = matches_efo(0, st_az, st_az_embeddings, efo, efo_embeddings, n=20)[['efo', 'similarity']]
a[a.efo.str.contains('arthritis')]
a[a.efo.str.contains('rheumatoid')]

efo[efo.term.str.contains('rheumatoid')]



# for each trait get the top 10 most similar efo terms
top_n = 20
similarities = []

for i in range(44, len(st_embeddings)):
    print(i)
    similarities.append(matches_efo(i, st, st_embeddings, efo, efo_embeddings, top_n))

sim = pd.concat(similarities)
sim

# remove duplicates of trait_id and efo_id
sim2 = sim.drop_duplicates(subset=['trait_id', 'efo_id'])

sim2.to_csv("similarity.csv", index=False)

# write to csv in batches of 500 rows named by batch number
batch_size = 500
n_batches = len(sim2) // batch_size + 1
for i in range(n_batches):
    sim2.iloc[i * batch_size:(i + 1) * batch_size].to_csv(f"bio-bert/similarity_batch_{i}.csv", index=False)

