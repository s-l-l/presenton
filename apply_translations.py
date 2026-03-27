import os, glob, re, json

directory = r'd:\codeWorkspase\presenton\servers\nextjs\app\presentation-templates\neo-general'
files = glob.glob(os.path.join(directory, '*.tsx'))

with open('translations.json', 'r', encoding='utf-8') as f:
    translations = json.load(f)

def escape_str(s):
    # escape single and double quotes for regex
    return re.escape(s)

count_replacements = 0

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        
    original_content = content
    
    # replace layoutName
    for eng, zh in translations.items():
        if eng in content:
            # specifically for layoutName and layoutDescription and meta descriptions
            content = re.sub(r'(export const layoutName\s*=\s*[\'"])' + escape_str(eng) + r'([\'"])', r'\g<1>' + zh + r'\g<2>', content)
            content = re.sub(r'(export const layoutDescription\s*=\s*[\'"])' + escape_str(eng) + r'([\'"])', r'\g<1>' + zh + r'\g<2>', content)
            content = re.sub(r'(description:\s*[\'"])' + escape_str(eng) + r'([\'"])', r'\g<1>' + zh + r'\g<2>', content)

    if content != original_content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        count_replacements += 1

print(f"Updated {count_replacements} files.")
