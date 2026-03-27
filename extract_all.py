import os, glob, re, json

directory = r'd:\codeWorkspase\presenton\servers\nextjs\app\presentation-templates'
files = []
for root, _, _ in os.walk(directory):
    files.extend(glob.glob(os.path.join(root, '*.tsx')))

strings_to_translate = set()

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        m = re.search(r'export const layoutName\s*=\s*[\'"]([^\'"]+)[\'"]', content)
        if m: strings_to_translate.add(m.group(1))
        
        m = re.search(r'export const layoutDescription\s*=\s*[\'"]([^\'"]+)[\'"]', content)
        if m: strings_to_translate.add(m.group(1))
        
        matches = re.findall(r'description:\s*[\'"]([^\'"]+)[\'"]', content)
        for match in matches:
            strings_to_translate.add(match)

with open('translate_all.json', 'w', encoding='utf-8') as out:
    json.dump(list(strings_to_translate), out, indent=2, ensure_ascii=False)

print(f'Extracted {len(strings_to_translate)} strings.')
