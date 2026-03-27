import os, glob, re, json

directory = r'd:\codeWorkspase\presenton\servers\nextjs\app\presentation-templates'
files = []
for root, _, _ in os.walk(directory):
    files.extend(glob.glob(os.path.join(root, '*.tsx')))
    files.extend(glob.glob(os.path.join(root, '*.json')))

with open('d:/codeWorkspase/presenton/all_translations.json', 'r', encoding='utf-8') as f:
    translations = json.load(f)

def escape_str(s):
    return re.escape(s)

count_replacements = 0

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        
    original_content = content
    
    if f.endswith('.tsx'):
        for eng, zh in translations.items():
            if eng in content:
                content = re.sub(r'(export const layoutName\s*=\s*[\'"])' + escape_str(eng) + r'([\'"])', r'\g<1>' + zh + r'\g<2>', content)
                content = re.sub(r'(export const layoutDescription\s*=\s*[\'"])' + escape_str(eng) + r'([\'"])', r'\g<1>' + zh + r'\g<2>', content)
                content = re.sub(r'(description:\s*[\'"])' + escape_str(eng) + r'([\'"])', r'\g<1>' + zh + r'\g<2>', content)
    elif f.endswith('settings.json'):
        for eng, zh in translations.items():
            if eng in content:
                content = content.replace(f'"description": "{eng}"', f'"description": "{zh}"')
                content = content.replace(f'"name": "{eng}"', f'"name": "{zh}"')

    if content != original_content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        count_replacements += 1

print(f"Updated {count_replacements} files.")
