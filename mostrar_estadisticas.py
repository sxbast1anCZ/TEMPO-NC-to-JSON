"""
Muestra estadísticas del procesamiento TEMPO
"""

import json
from pathlib import Path


def mostrar_estadisticas():
    """Muestra estadísticas de los archivos procesados"""
    
    output_folder = Path('output')
    surface_files = list(output_folder.glob('SURFACE_*.json'))
    
    if not surface_files:
        print("⚠️  No se encontraron archivos SURFACE_*.json")
        return
    
    for filepath in surface_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("\n" + "="*70)
        print("🎉 PROCESAMIENTO COMPLETADO EXITOSAMENTE")
        print("="*70 + "\n")
        
        print(f"Archivo: {data['metadata']['source_file']}")
        print(f"Producto: {data['metadata']['product']}")
        print(f"Scan time: {data['metadata']['scan_time']}")
        
        # Detectar tipo de contaminante
        pollutant = data['metadata']['product']
        
        # Estadísticas de concentración
        if pollutant == 'NO2':
            concs = [m['surface_concentration_ugm3'] for m in data['measurements']]
            unit = 'µg/m³'
        elif pollutant == 'O3':
            concs = [m['tropospheric_concentration_ppb'] for m in data['measurements']]
            unit = 'ppb'
        else:
            concs = [m.get('surface_concentration_ugm3', m.get('tropospheric_concentration_ppb', 0)) for m in data['measurements']]
            unit = 'units'
        
        print(f"\n📊 ESTADÍSTICAS:")
        print("-"*70)
        print(f"Puntos totales: {len(data['measurements']):,}")
        print(f"Concentración mínima: {min(concs):.2f} {unit}")
        print(f"Concentración máxima: {max(concs):.2f} {unit}")
        print(f"Concentración promedio: {sum(concs)/len(concs):.2f} {unit}")
        print(f"Concentración mediana: {sorted(concs)[len(concs)//2]:.2f} {unit}")
        
        # Distribución por categoría AQI
        categories = {}
        for m in data['measurements']:
            cat = m['aqi_category']
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\n🌈 DISTRIBUCIÓN DE CALIDAD DEL AIRE:")
        print("-"*70)
        
        for cat in ["Bueno", "Moderado", "Insalubre para grupos sensibles", 
                    "Insalubre", "Muy insalubre", "Peligroso"]:
            if cat in categories:
                count = categories[cat]
                percent = (count / len(data['measurements'])) * 100
                print(f"{cat:35} {count:8,} puntos ({percent:5.1f}%)")
        
        # Cobertura geográfica
        lats = [m['latitude'] for m in data['measurements']]
        lons = [m['longitude'] for m in data['measurements']]
        
        print(f"\n🌍 COBERTURA GEOGRÁFICA:")
        print("-"*70)
        print(f"Latitud:  {min(lats):7.2f}° N  →  {max(lats):7.2f}° N")
        print(f"Longitud: {min(lons):7.2f}° W  →  {max(lons):7.2f}° W")
        
        print(f"\n{'='*70}")
        print(f"✅ Archivo listo para Google Cloud:")
        print(f"   {filepath.name}")
        print(f"   Tamaño: {filepath.stat().st_size / (1024*1024):.2f} MB")
        print("="*70 + "\n")


if __name__ == '__main__':
    mostrar_estadisticas()
