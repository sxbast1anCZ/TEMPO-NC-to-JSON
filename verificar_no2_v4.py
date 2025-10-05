import json

# Verificar el archivo NO2 MÁS RECIENTE (V04)
print("Verificando archivo NO2 V04 recién descargado...\n")

try:
    with open('output/NO2_TEMPO_NO2_L2_V04_20251004T152407Z_S005G09.json', 'r') as f:
        data = json.load(f)
    
    print(f"Total de puntos: {len(data['measurements']):,}")
    
    qf_counts = {}
    for m in data['measurements']:
        qf = str(m['quality_flag'])
        qf_counts[qf] = qf_counts.get(qf, 0) + 1
    
    print("\nDistribución de quality_flag:")
    for qf, count in sorted(qf_counts.items()):
        pct = (count / len(data['measurements'])) * 100
        print(f"  quality_flag {qf}: {count:,} puntos ({pct:.1f}%)")
    
    # Mostrar algunos ejemplos de cada quality_flag
    print("\nEjemplos:")
    for qf_val in sorted(set(float(qf) for qf in qf_counts.keys())):
        examples = [m for m in data['measurements'] if m['quality_flag'] == qf_val][:3]
        print(f"\n  Quality flag = {qf_val}: ({len([m for m in data['measurements'] if m['quality_flag'] == qf_val])} puntos)")
        for ex in examples:
            print(f"    Lat: {ex['latitude']:.2f}, Lon: {ex['longitude']:.2f}, NO2: {ex['vertical_column']:.2e}")
            
except FileNotFoundError:
    print("❌ Archivo NO2 V04 no encontrado")
