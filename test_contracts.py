import re

# Read enums.py
with open('backend/revflow/contracts/enums.py', 'r') as f:
    enums_content = f.read()

# Extract enum values from enums.py
enum_pattern = r'class (\w+)\(StrEnum\):(.*?)(?=\nclass |\n\n|\Z)'
enums = re.findall(enum_pattern, enums_content, re.DOTALL)

py_enums = {}
for name, content in enums:
    values = re.findall(r'(\w+)\s*=\s*["\']([^"\']+)["\']', content)
    py_enums[name] = {k: v for k, v in values}

# Read contracts.ts
with open('frontend/lib/contracts.ts', 'r') as f:
    contracts_content = f.read()

# Extract type definitions
ts_enums = {}
type_pattern = r'export type (\w+)\s*=\s*([^;]+);'
for match in re.finditer(type_pattern, contracts_content):
    name = match.group(1)
    content = match.group(2)
    values = re.findall(r'[\'"]([^\'"]+)[\'"]', content)
    ts_enums[name] = values

# Compare
all_match = True
for name in py_enums:
    if name not in ts_enums:
        print(f'MISSING in TS: {name}')
        all_match = False
    else:
        py_values = set(py_enums[name].values())
        ts_values = set(ts_enums[name])
        if py_values != ts_values:
            print(f'MISMATCH in {name}:')
            print(f'  Python: {sorted(py_values)}')
            print(f'  TypeScript: {sorted(ts_values)}')
            all_match = False

if all_match:
    print('TEST-12 PASSED: contracts.ts matches enums.py')
else:
    print('TEST-12 FAILED')