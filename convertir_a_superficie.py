"""
Script para convertir columnas verticales TEMPO a concentraciones superficiales estimadas
y calcular AQI para uso en aplicaciones de calidad del aire
"""

import json
from pathlib import Path
import glob


def column_to_surface_no2(vertical_column_1e15):
    """
    Convierte columna vertical de NO2 a concentración superficial estimada
    
    Parámetros:
        vertical_column_1e15: Columna vertical en 10^15 moléculas/cm²
    
    Retorna:
        Concentración superficial estimada en µg/m³
    
    Nota: Esta es una aproximación simplificada. La conversión exacta requiere
    información sobre el perfil vertical, altura de capa de mezcla, etc.
    """
    # Factor de conversión empírico basado en estudios de validación TEMPO
    # Asume altura de capa de mezcla típica de ~1.5 km
    # vertical_column (10^15 molec/cm²) × 0.75 ≈ surface_concentration (µg/m³)
    FACTOR = 0.75
    
    return vertical_column_1e15 * FACTOR


def column_to_surface_o3(vertical_column_du):
    """
    Convierte columna total de O3 a concentración troposférica estimada
    
    Parámetros:
        vertical_column_du: Columna vertical en Dobson Units (DU)
    
    Retorna:
        Concentración troposférica estimada en ppb
    """
    # La mayor parte del O3 está en la estratosfera (~90%)
    # Asumimos ~10% troposférico y convertimos
    # 1 DU ≈ 0.4 ppb O3 troposférico (aproximación)
    FACTOR = 0.04  # 10% × 0.4
    
    return vertical_column_du * FACTOR


def column_to_surface_aod(aod_value):
    """
    Convierte AOD a PM2.5 estimado
    
    Parámetros:
        aod_value: Aerosol Optical Depth (adimensional)
    
    Retorna:
        PM2.5 estimado en µg/m³
    """
    # Relación empírica: PM2.5 ≈ AOD × factor de escala
    # Factor típico varía entre 20-100 dependiendo de condiciones
    # Usamos un valor medio de 50
    FACTOR = 50
    
    return aod_value * FACTOR


def calculate_aqi_no2(concentration_ugm3):
    """Calcula AQI para NO2 en µg/m³"""
    breakpoints = [
        (0, 53, 0, 50),
        (54, 100, 51, 100),
        (101, 360, 101, 150),
        (361, 649, 151, 200),
        (650, 1249, 201, 300),
        (1250, 2049, 301, 500)
    ]
    
    for bp_lo, bp_hi, aqi_lo, aqi_hi in breakpoints:
        if bp_lo <= concentration_ugm3 <= bp_hi:
            aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (concentration_ugm3 - bp_lo) + aqi_lo
            return round(aqi)
    
    return 500  # Fuera de rango


def calculate_aqi_o3(concentration_ppb):
    """Calcula AQI para O3 en ppb"""
    breakpoints = [
        (0, 54, 0, 50),
        (55, 70, 51, 100),
        (71, 85, 101, 150),
        (86, 105, 151, 200),
        (106, 200, 201, 300),
        (201, 404, 301, 500)
    ]
    
    for bp_lo, bp_hi, aqi_lo, aqi_hi in breakpoints:
        if bp_lo <= concentration_ppb <= bp_hi:
            aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (concentration_ppb - bp_lo) + aqi_lo
            return round(aqi)
    
    return 500


def calculate_aqi_pm25(concentration_ugm3):
    """Calcula AQI para PM2.5 en µg/m³"""
    breakpoints = [
        (0, 12, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 500.4, 301, 500)
    ]
    
    for bp_lo, bp_hi, aqi_lo, aqi_hi in breakpoints:
        if bp_lo <= concentration_ugm3 <= bp_hi:
            aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (concentration_ugm3 - bp_lo) + aqi_lo
            return round(aqi)
    
    return 500


def get_aqi_category(aqi):
    """Retorna la categoría AQI"""
    if aqi <= 50:
        return "Bueno"
    elif aqi <= 100:
        return "Moderado"
    elif aqi <= 150:
        return "Insalubre para grupos sensibles"
    elif aqi <= 200:
        return "Insalubre"
    elif aqi <= 300:
        return "Muy insalubre"
    else:
        return "Peligroso"


def convert_no2_file(input_file, output_folder):
    """Convierte archivo NO2 de columnas verticales a concentraciones superficiales"""
    print(f"📂 Convirtiendo NO2: {input_file.name}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    new_measurements = []
    
    for m in data['measurements']:
        vertical_col = m['vertical_column']
        surface_conc = column_to_surface_no2(vertical_col)
        aqi = calculate_aqi_no2(surface_conc)
        
        new_measurements.append({
            "latitude": m['latitude'],
            "longitude": m['longitude'],
            "timestamp": m['timestamp'],
            "pollutant": "NO2",
            "surface_concentration_ugm3": round(surface_conc, 2),
            "vertical_column_1e15": vertical_col,
            "aqi": aqi,
            "aqi_category": get_aqi_category(aqi),
            "quality_flag": m['quality_flag']
        })
    
    output_data = {
        "metadata": {
            **data['metadata'],
            "conversion_note": "Concentraciones superficiales estimadas desde columnas verticales TEMPO",
            "conversion_method": "Factor empírico basado en altura de mezcla ~1.5km"
        },
        "measurements": new_measurements
    }
    
    output_file = output_folder / f"SURFACE_{input_file.name}"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Guardado: {output_file.name}\n")
    return len(new_measurements)


def convert_o3_file(input_file, output_folder):
    """Convierte archivo O3 de columnas verticales a concentraciones troposféricas"""
    print(f"📂 Convirtiendo O3: {input_file.name}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    new_measurements = []
    
    for m in data['measurements']:
        vertical_col = m['vertical_column_du']
        surface_conc = column_to_surface_o3(vertical_col)
        aqi = calculate_aqi_o3(surface_conc)
        
        new_measurements.append({
            "latitude": m['latitude'],
            "longitude": m['longitude'],
            "timestamp": m['timestamp'],
            "pollutant": "O3",
            "tropospheric_concentration_ppb": round(surface_conc, 2),
            "vertical_column_du": vertical_col,
            "aqi": aqi,
            "aqi_category": get_aqi_category(aqi),
            "quality_flag": m['quality_flag']
        })
    
    output_data = {
        "metadata": {
            **data['metadata'],
            "conversion_note": "Concentraciones troposféricas estimadas desde columnas verticales TEMPO",
            "conversion_method": "Factor empírico: ~10% de columna total es troposférico"
        },
        "measurements": new_measurements
    }
    
    output_file = output_folder / f"SURFACE_{input_file.name}"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Guardado: {output_file.name}\n")
    return len(new_measurements)


def main():
    """Función principal"""
    print("\n🔄 CONVERSOR DE COLUMNAS VERTICALES A CONCENTRACIONES SUPERFICIALES\n")
    print("="*70 + "\n")
    
    output_folder = Path('output')
    
    # Buscar archivos de columnas verticales
    no2_files = list(output_folder.glob('NO2_*.json'))
    o3_files = list(output_folder.glob('O3_*.json'))
    
    # Excluir archivos ya convertidos
    no2_files = [f for f in no2_files if not f.name.startswith('SURFACE_')]
    o3_files = [f for f in o3_files if not f.name.startswith('SURFACE_')]
    
    total_files = len(no2_files) + len(o3_files)
    
    if total_files == 0:
        print("⚠️  No se encontraron archivos de columnas verticales en output/")
        print("   Primero ejecuta: python extraer_datos.py\n")
        return
    
    print(f"✅ Encontrados {total_files} archivo(s) para convertir:")
    print(f"   • NO2: {len(no2_files)}")
    print(f"   • O3: {len(o3_files)}\n")
    
    total_points = 0
    
    # Procesar NO2
    for filepath in no2_files:
        points = convert_no2_file(filepath, output_folder)
        total_points += points
    
    # Procesar O3
    for filepath in o3_files:
        points = convert_o3_file(filepath, output_folder)
        total_points += points
    
    print("="*70)
    print(f"\n🎉 Conversión completada!")
    print(f"📊 Total de puntos convertidos: {total_points:,}")
    print(f"📁 Archivos guardados en: {output_folder.absolute()}")
    print("\n💡 Los archivos SURFACE_* contienen concentraciones superficiales")
    print("   estimadas y cálculos de AQI listos para tu aplicación.\n")


if __name__ == '__main__':
    main()
