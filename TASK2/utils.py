from sklearn.metrics.pairwise import cosine_similarity
import re
import numpy as np
def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
def compute_in_neighbor_similarity(u_emb, v, G):
    sims = []
    for z in G.predecessors(v):
        emb_z = G.nodes[z].get('embedding')
        if emb_z is not None:
            sim = cosine_similarity(u_emb.reshape(1, -1), emb_z.reshape(1, -1))[0][0]
            if sim > 0.98:  # Avoid self-similarity
                continue
            sims.append(sim)
    if sims:
        sims.sort(reverse=True)
        if len(sims)>4:
            bruh = sims[:5]
        else:
            bruh = sims
        if len(sims) > 9:
            bruh2 = np.mean(sims[:10])
        else:
            bruh2 = np.mean(sims)*0.9 
            
        return [np.mean(bruh), np.mean(bruh2),np.max(sims),len(sims)]
    else:
        return [0.0, 0.0, 0.0, 0.0]
    
    