import json

# Verificar NO2
print("="*70)
print("VERIFICANDO NO2")
print("="*70)
with open('output/SURFACE_NO2_TEMPO_NO2_L2_V03_20250916T214329Z_S012G07.json', 'r') as f:
    no2_data = json.load(f)

# Contar quality flags
quality_counts = {}
for m in no2_data['measurements']:
    qf = m['quality_flag']
    quality_counts[qf] = quality_counts.get(qf, 0) + 1

print("\nDistribución de quality_flag en NO2:")
for qf in sorted(quality_counts.keys()):
    print(f"  quality_flag {qf}: {quality_counts[qf]:,} puntos")

# Mostrar ejemplos con quality_flag = 0
print("\n5 ejemplos con quality_flag = 0.0:")
count = 0
for m in no2_data['measurements']:
    if m['quality_flag'] == 0.0 and count < 5:
        print(f"  Lat: {m['latitude']}, Lon: {m['longitude']}")
        print(f"    quality_flag: {m['quality_flag']}")
        print(f"    concentration: {m['surface_concentration_ugm3']} µg/m³")
        print(f"    AQI: {m['aqi']} - {m['aqi_category']}")
        print()
        count += 1

print("\n" + "="*70)
print("VERIFICANDO O3")
print("="*70)
with open('output/SURFACE_O3_TEMPO_O3TOT_L3_V04_20251004T133103Z_S004.json', 'r') as f:
    o3_data = json.load(f)

# Todos deberían tener quality_flag = 1.0 (L3 no tiene flags individuales)
print("\nPrimeros 5 puntos de O3:")
for i, m in enumerate(o3_data['measurements'][:5]):
    print(f"{i+1}. quality_flag: {m['quality_flag']} - Conc: {m['tropospheric_concentration_ppb']} ppb - AQI: {m['aqi']} - {m['aqi_category']}")

print("\n" + "="*70)
print("CONCLUSIÓN:")
print("="*70)
print("En los archivos TEMPO originales:")
print("  • quality_flag = 0 generalmente indica DATOS MALOS/FALTANTES")
print("  • quality_flag > 0 (especialmente > 0.5) indica DATOS BUENOS")
print("\nPero estamos procesando TODOS los datos, incluyendo los malos.")
print("Necesitamos FILTRAR por quality_flag en el procesamiento.")
