
import json
for i in range(141, 151):
    with open(f'scripts/batches/batch_{i}.json') as f:
        d = json.load(f)
    names = [e['name'] for e in d]
    print(f'batch_{i}: {len(d)} entries')
    for n in names:
        print(f'  - {n}')
