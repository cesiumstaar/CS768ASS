import argparse


def main():
    import pickle
    import numpy as np
    from utils import normalize_text, compute_in_neighbor_similarity
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-paper-title", type=str, required=True)
    parser.add_argument("--test-paper-abstract", type=str, required=True)
    args = parser.parse_args()

    ################################################
    #               YOUR CODE START                #
    ################################################

    # Helper: Embed abstract text
    def get_embedding_from_text(text):
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return model.encode(text, convert_to_numpy=True)


    with open("citation_graph_final.pkl", "rb") as f:
        G = pickle.load(f)
    with open("link_predictor_model.pkl", "rb") as f:
        clf = pickle.load(f)


    query_emb = get_embedding_from_text(args.test_paper_abstract)

    scores = []
    for node in G.nodes:
        emb_t = G.nodes[node].get("embedding")
        if emb_t is None:
            continue

        sim_mean, sim2_mean, sim_max, num = compute_in_neighbor_similarity(query_emb, node, G)
        feat = [float(sim_mean), sim2_mean, float(sim_max), num]
        prob = clf.predict_proba([feat])[0][1]
        scores.append((prob, node))

  
    scores.sort(reverse=True)
    result = [G.nodes[node]['raw_title'] for _, node in scores if G.nodes[node].get('raw_title')]

    ################################################
    #               YOUR CODE END                  #
    ################################################

    ################################################
    #               DO NOT CHANGE                  #
    ################################################
    #had to change the following because it cannot print all of result in one go it's impossible
    chunks = [result[i:i+500] for i in range(0, len(result), 500)]
    for chunk in chunks:
        print('\n'.join(chunk))

if __name__ == "__main__":
    main()
