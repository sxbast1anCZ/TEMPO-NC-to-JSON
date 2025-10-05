"""
Divide archivos JSON grandes en chunks más pequeños para facilitar carga a Google Cloud
Útil cuando los archivos son muy grandes (>50 MB)
"""

import json
from pathlib import Path
import math


def dividir_json(input_file, chunk_size=50000):
    """
    Divide un archivo JSON grande en chunks más pequeños
    
    Args:
        input_file: Archivo JSON a dividir
        chunk_size: Número de mediciones por chunk (default: 50000)
    """
    print(f"📂 Dividiendo: {input_file.name}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_measurements = len(data['measurements'])
    num_chunks = math.ceil(total_measurements / chunk_size)
    
    print(f"   Total de mediciones: {total_measurements:,}")
    print(f"   Tamaño de chunk: {chunk_size:,}")
    print(f"   Número de chunks: {num_chunks}\n")
    
    output_folder = input_file.parent / 'chunks'
    output_folder.mkdir(exist_ok=True)
    
    base_name = input_file.stem
    
    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, total_measurements)
        
        chunk_measurements = data['measurements'][start_idx:end_idx]
        
        chunk_data = {
            "metadata": {
                **data['metadata'],
                "chunk_info": {
                    "chunk_number": i + 1,
                    "total_chunks": num_chunks,
                    "measurements_in_chunk": len(chunk_measurements),
                    "start_index": start_idx,
                    "end_index": end_idx
                }
            },
            "measurements": chunk_measurements
        }
        
        chunk_file = output_folder / f"{base_name}_chunk_{i+1:03d}_of_{num_chunks:03d}.json"
        
        with open(chunk_file, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, indent=2, ensure_ascii=False)
        
        size_mb = chunk_file.stat().st_size / (1024 * 1024)
        print(f"   ✅ Chunk {i+1}/{num_chunks}: {chunk_file.name} ({size_mb:.2f} MB, {len(chunk_measurements):,} puntos)")
    
    print(f"\n📁 Chunks guardados en: {output_folder.absolute()}\n")


def main():
    """Función principal"""
    print("\n📦 DIVISOR DE ARCHIVOS JSON GRANDES\n")
    print("="*70 + "\n")
    
    output_folder = Path('output')
    surface_files = list(output_folder.glob('SURFACE_*.json'))
    
    if not surface_files:
        print("⚠️  No se encontraron archivos SURFACE_*.json")
        return
    
    print(f"Encontrados {len(surface_files)} archivo(s) para dividir:\n")
    
    for filepath in surface_files:
        dividir_json(filepath, chunk_size=50000)
    
    print("="*70)
    print("\n🎉 División completada!")
    print("\n💡 Ahora puedes subir los chunks a Google Cloud:")
    print("   gsutil -m cp output/chunks/*.json gs://tu-bucket/tempo-data/\n")


if __name__ == '__main__':
    main()
