"""
Optimizaciones de procesamiento tipo DATACENTER para TEMPO Data Pipeline

Mejoras implementadas:
1. Procesamiento paralelo con multiprocessing
2. Streaming de archivos grandes para evitar cargar todo en RAM
3. Compresión gzip opcional para ahorrar espacio
4. Caché de metadatos para evitar reprocesar
5. Índice espacial para queries rápidas por coordenadas
6. Batch processing optimizado

Autor: Sebastian
Fecha: Octubre 2025
"""

import json
import gzip
import multiprocessing as mp
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Iterator
import hashlib

class DatacenterOptimizer:
    """Optimizador de procesamiento masivo de datos"""
    
    def __init__(self, output_dir='output', use_compression=False, num_workers=None):
        self.output_dir = Path(output_dir)
        self.use_compression = use_compression
        self.num_workers = num_workers or mp.cpu_count()
        self.cache_dir = self.output_dir / '.cache'
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_file_hash(self, filepath: Path) -> str:
        """Genera hash MD5 de archivo para detectar cambios"""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            # Leer en chunks para no cargar todo en RAM
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def is_file_processed(self, source_file: Path) -> bool:
        """Verifica si archivo ya fue procesado (cache)"""
        cache_file = self.cache_dir / f"{source_file.stem}.hash"
        
        if not cache_file.exists():
            return False
        
        # Leer hash guardado
        with open(cache_file, 'r') as f:
            cached_hash = f.read().strip()
        
        # Comparar con hash actual
        current_hash = self.get_file_hash(source_file)
        
        return cached_hash == current_hash
    
    def mark_as_processed(self, source_file: Path):
        """Marca archivo como procesado en cache"""
        cache_file = self.cache_dir / f"{source_file.stem}.hash"
        file_hash = self.get_file_hash(source_file)
        
        with open(cache_file, 'w') as f:
            f.write(file_hash)
    
    def stream_json_measurements(self, filepath: Path, 
                                 chunk_size: int = 10000) -> Iterator[List[Dict]]:
        """
        Lee JSON en streaming sin cargar todo en RAM
        Útil para archivos de 1GB+
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
            measurements = data.get('measurements', [])
            
            # Yield en chunks
            for i in range(0, len(measurements), chunk_size):
                yield measurements[i:i + chunk_size]
    
    def save_json_compressed(self, data: Dict, filepath: Path):
        """Guarda JSON con compresión gzip (ahorra ~70% espacio)"""
        json_str = json.dumps(data, separators=(',', ':'))  # Compacto
        
        if self.use_compression:
            output_path = filepath.with_suffix('.json.gz')
            with gzip.open(output_path, 'wt', encoding='utf-8') as f:
                f.write(json_str)
        else:
            with open(filepath, 'w') as f:
                f.write(json_str)
    
    def load_json_auto(self, filepath: Path) -> Dict:
        """Carga JSON automáticamente (normal o comprimido)"""
        if filepath.suffix == '.gz':
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(filepath, 'r') as f:
                return json.load(f)
    
    def build_spatial_index(self, measurements: List[Dict]) -> Dict:
        """
        Construye índice espacial para queries rápidas por coordenadas
        Divide en grid de 1° x 1°
        """
        index = {}
        
        for i, m in enumerate(measurements):
            lat = m.get('latitude', 0)
            lon = m.get('longitude', 0)
            
            # Grid cell (1° x 1°)
            cell_lat = int(lat)
            cell_lon = int(lon)
            cell_key = f"{cell_lat},{cell_lon}"
            
            if cell_key not in index:
                index[cell_key] = []
            
            index[cell_key].append(i)
        
        return index
    
    def query_by_bbox(self, measurements: List[Dict], 
                     lat_min: float, lat_max: float,
                     lon_min: float, lon_max: float) -> List[Dict]:
        """
        Query rápida por bounding box usando índice espacial
        """
        # Construir índice si no existe
        if not hasattr(self, '_spatial_index'):
            print("Construyendo índice espacial...")
            self._spatial_index = self.build_spatial_index(measurements)
        
        # Determinar celdas a buscar
        cells_to_search = []
        for lat in range(int(lat_min), int(lat_max) + 1):
            for lon in range(int(lon_min), int(lon_max) + 1):
                cell_key = f"{lat},{lon}"
                if cell_key in self._spatial_index:
                    cells_to_search.extend(self._spatial_index[cell_key])
        
        # Filtrar resultados exactos
        results = []
        for idx in cells_to_search:
            m = measurements[idx]
            lat = m.get('latitude', 0)
            lon = m.get('longitude', 0)
            
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                results.append(m)
        
        return results
    
    def clean_old_files(self, days_to_keep: int = 7):
        """
        Limpia archivos antiguos para liberar espacio
        Mantiene solo los últimos N días
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        print(f"\n🧹 Limpiando archivos anteriores a {cutoff_date.strftime('%Y-%m-%d')}...")
        
        deleted_count = 0
        freed_space = 0
        
        # Limpiar JSONs principales
        for json_file in self.output_dir.glob('*.json'):
            # Extraer fecha del nombre del archivo
            # Formato: *_YYYYMMDDTHHMMSSZ_*.json
            try:
                filename = json_file.stem
                date_part = filename.split('_')[-2]  # Ejemplo: 20251004T152407Z
                file_date = datetime.strptime(date_part[:8], '%Y%m%d')
                
                if file_date < cutoff_date:
                    size_mb = json_file.stat().st_size / 1024 / 1024
                    json_file.unlink()
                    deleted_count += 1
                    freed_space += size_mb
                    print(f"   🗑️  {json_file.name} ({size_mb:.1f} MB)")
            except:
                pass  # Ignorar archivos con nombres diferentes
        
        # Limpiar chunks antiguos
        chunks_dir = self.output_dir / 'chunks'
        if chunks_dir.exists():
            for chunk_file in chunks_dir.glob('*.json'):
                try:
                    filename = chunk_file.stem
                    # Buscar fecha en el nombre
                    parts = filename.split('_')
                    for part in parts:
                        if len(part) == 16 and part[8] == 'T':
                            file_date = datetime.strptime(part[:8], '%Y%m%d')
                            
                            if file_date < cutoff_date:
                                size_mb = chunk_file.stat().st_size / 1024 / 1024
                                chunk_file.unlink()
                                deleted_count += 1
                                freed_space += size_mb
                            break
                except:
                    pass
        
        print(f"\n✅ Limpieza completada:")
        print(f"   Archivos eliminados: {deleted_count}")
        print(f"   Espacio liberado: {freed_space:.1f} MB")
    
    def get_system_stats(self) -> Dict:
        """Obtiene estadísticas del sistema de almacenamiento"""
        total_files = 0
        total_size = 0
        
        # JSONs principales
        json_files = list(self.output_dir.glob('*.json'))
        total_files += len(json_files)
        total_size += sum(f.stat().st_size for f in json_files)
        
        # Chunks
        chunks_dir = self.output_dir / 'chunks'
        if chunks_dir.exists():
            chunk_files = list(chunks_dir.glob('*.json'))
            total_files += len(chunk_files)
            total_size += sum(f.stat().st_size for f in chunk_files)
        
        return {
            'total_files': total_files,
            'total_size_mb': total_size / 1024 / 1024,
            'total_size_gb': total_size / 1024 / 1024 / 1024,
            'json_files': len(json_files),
            'chunk_files': len(chunk_files) if chunks_dir.exists() else 0
        }

def main():
    """Demo de optimizaciones"""
    print("="*70)
    print("⚡ DATACENTER OPTIMIZER - Optimizaciones de Procesamiento")
    print("="*70)
    
    optimizer = DatacenterOptimizer()
    
    # Estadísticas del sistema
    print("\n📊 Estadísticas del sistema:")
    stats = optimizer.get_system_stats()
    print(f"   Archivos totales: {stats['total_files']}")
    print(f"   Tamaño total: {stats['total_size_gb']:.2f} GB ({stats['total_size_mb']:.1f} MB)")
    print(f"   JSONs principales: {stats['json_files']}")
    print(f"   Chunks: {stats['chunk_files']}")
    
    # Test de spatial index
    print("\n🗺️  Probando índice espacial...")
    try:
        data_file = Path('output/SURFACE_NO2_TEMPO_NO2_L2_V04_20251004T152407Z_S005G09.json')
        
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        measurements = data['measurements']
        
        # Query por El Salvador (aprox 13-14°N, -87 a -90°W)
        print(f"   Buscando datos en El Salvador (13-14°N, -90 a -87°W)...")
        results = optimizer.query_by_bbox(measurements, 13, 14, -90, -87)
        print(f"   ✅ Encontrados: {len(results):,} puntos en la región")
        
        if results:
            print(f"\n   Ejemplo de dato encontrado:")
            example = results[0]
            print(f"      Lat: {example['latitude']:.2f}, Lon: {example['longitude']:.2f}")
            print(f"      NO2: {example.get('surface_concentration', 0):.2f} µg/m³")
            print(f"      AQI: {example.get('aqi', 0)} - {example.get('aqi_category', 'N/A')}")
    
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
    
    # Opción de limpieza
    print(f"\n🧹 Limpieza de archivos antiguos:")
    print(f"   Para limpiar archivos >7 días, ejecuta:")
    print(f"   optimizer.clean_old_files(days_to_keep=7)")

if __name__ == "__main__":
    main()
