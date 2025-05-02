import os
import re
import pickle
import sys
import networkx as nx
from difflib import get_close_matches
from concurrent.futures import ProcessPoolExecutor, as_completed

def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def strip_version(folder_name):
    return re.sub(r'v\d+$', '', folder_name)

def extract_year_from_arxiv_id(folder):
    folder = strip_version(folder)
    if len(folder) < 4 or not folder[:4].isdigit():
        return None, None
    year = int(folder[:2])
    month = int(folder[2:4])
    return year, month

def extract_year_from_bib_entry(text):
    match = re.search(r'year\s*=\s*\{(\d{4})\}', text)
    if match:
        return int(match.group(1))
    return None

def extract_year_from_bbl_entry(entry_text):
    match = re.search(r',\s*(\d{4})\.', entry_text)
    if match:
        return int(match.group(1))
    return None

def build_title_to_paper_map(root_dir, nodes_file_path="nodes.txt"):
    title_to_folder = {}
    folder_to_title = {}

    with open(nodes_file_path, 'w', encoding='utf-8') as node_file:
        for folder in os.listdir(root_dir):
            title_file = os.path.join(root_dir, folder, "title.txt")
            if not os.path.exists(title_file):
                continue
            try:
                with open(title_file, 'r', encoding='utf-8') as f:
                    raw_title = f.read()
                    normalized_title = normalize_text(raw_title)
                    base_folder = strip_version(folder)
                    title_to_folder[normalized_title] = base_folder
                    folder_to_title[base_folder] = normalized_title
                    node_file.write(f"{base_folder}\t{normalized_title}\n")
            except Exception as e:
                print(f"Error reading title for {folder}: {e}", file=sys.stderr)

    return title_to_folder, folder_to_title

def extract_titles_from_bbl(text, cited_titles_with_years):
    entries = re.split(r'\\bibitem', text)
    for entry in entries:
        lines = entry.splitlines()
        title_parts = []
        started_collecting = False

        for line in lines:
            if '\\newblock' in line:
                if not started_collecting:
                    started_collecting = True
                    title_line = line.replace('\\newblock', '').strip()
                    title_parts.append(title_line)
                else:
                    break
            elif started_collecting:
                title_parts.append(line.strip())

        if title_parts:
            full_title = ' '.join(title_parts)
            full_title = normalize_text(full_title)
            cited_year = extract_year_from_bbl_entry(entry)
            if full_title not in cited_titles_with_years and len(full_title) > 10:
                cited_titles_with_years[full_title] = cited_year

def extract_titles_from_bib(text, cited_titles_with_years):
    matches = re.findall(r'@\w+\s*\{[^,]+,([^@]*)\}', text, re.DOTALL)
    for entry in matches:
        title_match = re.search(r'title\s*=\s*\{([^}]*)\}', entry, re.IGNORECASE)
        if title_match:
            title = normalize_text(title_match.group(1))
            year = extract_year_from_bib_entry(entry)
            if title not in cited_titles_with_years and len(title) > 10:
                cited_titles_with_years[title] = year

def extract_cited_titles_from_all_bib_bbl(paper_path):
    cited_titles_with_years = {}
    for file in os.listdir(paper_path):
        if file.endswith('.bbl') or file.endswith('.bib'):
            file_path = os.path.join(paper_path, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        text = f.read()
                except Exception as e:
                    print(f"❌ Failed to parse {file_path}: {e}", file=sys.stderr)
                    continue
            try:
                if file.endswith('.bbl'):
                    extract_titles_from_bbl(text, cited_titles_with_years)
                elif file.endswith('.bib'):
                    extract_titles_from_bib(text, cited_titles_with_years)
            except Exception as e:
                print(f"❌ Error while extracting from {file_path}: {e}", file=sys.stderr)
    return cited_titles_with_years

def match_citation_to_dataset(cited_title, title_keys, title_to_folder):
    match = get_close_matches(cited_title, title_keys, n=1, cutoff=0.90)
    if match:
        return cited_title, match[0], title_to_folder[match[0]]
    return cited_title, None, None

def process_single_paper(folder, root_dir, title_to_folder, folder_to_title, title_keys):
    base_folder = strip_version(folder)
    paper_path = os.path.join(root_dir, folder)

    if base_folder not in folder_to_title:
        return base_folder, [], []

    citing_year, citing_month = extract_year_from_arxiv_id(base_folder)
    cited_titles_with_years = extract_cited_titles_from_all_bib_bbl(paper_path)
    edges = []
    logs = []

    for cited_title, cited_year in cited_titles_with_years.items():
        cited_title, matched_title, target = match_citation_to_dataset(cited_title, title_keys, title_to_folder)
        if target:
            target_year, target_month = extract_year_from_arxiv_id(target)
            if target_year is not None and citing_year is not None:
                if target_year > citing_year:
                    continue
                # if cited_year is not None:
                #     if cited_year >= 2000 and cited_year <= 2024:
                #         if target_year != cited_year % 100:
                #             print(f"❌ Year mismatch: {target_year} vs {cited_year} for paper {base_folder} citing {cited_title} to {matched_title}")
                #             continue
                if target_year == citing_year and target_month is not None and citing_month is not None:
                    if target_month > citing_month:
                        continue
            if target != base_folder:
                edges.append((base_folder, target, cited_title, matched_title))
    return base_folder, edges, logs

def build_citation_graph_parallel(root_dir, nodes_file_path="nodes_parallelized.txt", edges_file_path="edges_parallelized.txt", log_path="log.txt"):
    title_to_folder, folder_to_title = build_title_to_paper_map(root_dir, nodes_file_path)
    G = nx.DiGraph()

    for base_folder in folder_to_title:
        G.add_node(base_folder)

    title_keys = list(title_to_folder.keys())
    folders = os.listdir(root_dir)
    edge_counter = 0
    vertex_counter = 0

    with open(edges_file_path, 'w', encoding='utf-8') as edge_log, open(log_path, 'w', encoding='utf-8') as log_file:
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(process_single_paper, folder, root_dir, title_to_folder, folder_to_title, title_keys)
                       for folder in folders]

            for future in as_completed(futures):
                base_folder, edges, logs = future.result()
                vertex_counter += 1
                for base, target, cited_title, matched_title in edges:
                    G.add_edge(base, target)
                    edge_log.write(f"{base} -> {target}\n")
                    edge_log.write(f"{folder_to_title[base]} -> {folder_to_title[target]}\n")
                    log_file.write(f"[EDGE ADDED] {cited_title} -> {matched_title}\n")
                    edge_counter += 1
                if vertex_counter % 50 == 0:
                    log_file.write(f"✅ Processed {vertex_counter} vertices, {edge_counter} edges so far.\n")
                    log_file.flush()

    G.graph['title_to_folder'] = title_to_folder
    G.graph['folder_to_title'] = folder_to_title
    return G

if __name__ == "__main__":
    root = './dataset_papers/'  # adjust if needed
    citation_graph = build_citation_graph_parallel(root)

    with open('citation_graph.pkl', 'wb') as f:
        pickle.dump(citation_graph, f)

    print(f"🏁 Graph built with {citation_graph.number_of_nodes()} nodes and {citation_graph.number_of_edges()} edges.", file=sys.stderr)
