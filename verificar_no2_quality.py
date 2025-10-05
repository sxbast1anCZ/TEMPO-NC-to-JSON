import json

# Verificar distribución de quality_flag en archivo NO2 original
with open('output/NO2_TEMPO_NO2_L2_V03_20250916T214329Z_S012G07.json', 'r') as f:
    data = json.load(f)

qf_counts = {}
for m in data['measurements']:
    qf = str(m['quality_flag'])
    qf_counts[qf] = qf_counts.get(qf, 0) + 1

print('Quality flags en archivo NO2 original:')
for qf, count in sorted(qf_counts.items()):
    print(f"  quality_flag {qf}: {count:,} puntos")

print(f"\nTotal: {len(data['measurements']):,} puntos")
