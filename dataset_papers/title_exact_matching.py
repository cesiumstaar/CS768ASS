import re

def normalize_text(text):
    """Lowercase, remove punctuation, and extra spaces."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def check_matches(lines):
    """Check if text before and after arrow are the same."""
    c=0
    for idx, line in enumerate(lines):
        c+=1
        if(c%2 ==0): continue
        if '->' not in line:
            continue
        left, right = map(str.strip, line.split('->', 1))
        left_norm = normalize_text(left)
        right_norm = normalize_text(right)

        
        if left_norm == right_norm:
            pass
            # print(f"[✓] Line {idx+1}: MATCH ✅")
        else:
            print(f" Line {idx+1}: NO MATCH ")
            print(f"    Left : {left_norm}")
            print(f"    Right: {right_norm}")

# Example Usage:
filename = 'log.txt' 

with open(filename, 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f if line.strip()]

check_matches(lines)
