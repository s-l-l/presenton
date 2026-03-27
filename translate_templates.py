import os, glob, re, json

directory = r'd:\codeWorkspase\presenton\servers\nextjs\app\presentation-templates\neo-general'
files = glob.glob(os.path.join(directory, '*.tsx'))

strings_to_translate = set()

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        # Find layoutName
        m = re.search(r'export const layoutName\s*=\s*[\'"]([^\'"]+)[\'"]', content)
        if m: strings_to_translate.add(m.group(1))
        
        # Find layoutDescription
        m = re.search(r'export const layoutDescription\s*=\s*[\'"]([^\'"]+)[\'"]', content)
        if m: strings_to_translate.add(m.group(1))
        
        # Find description: \"...\"
        matches = re.findall(r'description:\s*[\'"]([^\'"]+)[\'"]', content)
        for match in matches:
            strings_to_translate.add(match)

with open('translate_me.json', 'w', encoding='utf-8') as out:
    json.dump(list(strings_to_translate), out, indent=2, ensure_ascii=False)

print(f'Extracted {len(strings_to_translate)} strings.')
