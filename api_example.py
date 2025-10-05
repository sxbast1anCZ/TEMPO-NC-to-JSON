"""
API REST Endpoint Example para datos TEMPO

Este es un ejemplo de cómo estructurar tu API REST usando
los datos procesados con calidad validada.

Framework sugerido: FastAPI
Instalar: pip install fastapi uvicorn

Autor: Sebastian
Fecha: Octubre 2025
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, List
import json

# Simulación de endpoint (usar FastAPI en producción)
class TempoAPI:
    """Simulador de API REST para datos TEMPO"""
    
    def __init__(self, data_dir='output'):
        self.data_dir = Path(data_dir)
        self.quality_manager = None  # Se cargará dinámicamente
    
    def get_latest_data(self, pollutant: str, 
                       lat_min: Optional[float] = None,
                       lat_max: Optional[float] = None,
                       lon_min: Optional[float] = None,
                       lon_max: Optional[float] = None,
                       quality_threshold: str = 'MODERATE') -> dict:
        """
        GET /api/v1/tempo/{pollutant}/latest
        
        Parámetros:
            pollutant: 'NO2' o 'O3'
            lat_min, lat_max, lon_min, lon_max: Bounding box (opcional)
            quality_threshold: 'STRICT', 'MODERATE', 'PERMISSIVE'
        
        Retorna:
            JSON con datos filtrados, calidad validada y advertencias
        """
        
        try:
            # Buscar archivo más reciente
            pattern = f"SURFACE_{pollutant}_*.json"
            files = sorted(self.data_dir.glob(pattern), 
                          key=lambda x: x.stat().st_mtime, 
                          reverse=True)
            
            if not files:
                return {
                    'success': False,
                    'error': f'No hay datos disponibles para {pollutant}',
                    'code': 'NO_DATA_AVAILABLE'
                }
            
            latest_file = files[0]
            
            # Cargar datos
            with open(latest_file, 'r') as f:
                data = json.load(f)
            
            measurements = data.get('measurements', [])
            
            # Filtrar por bounding box si se especifica
            if all(v is not None for v in [lat_min, lat_max, lon_min, lon_max]):
                measurements = [
                    m for m in measurements
                    if lat_min <= m.get('latitude', 0) <= lat_max
                    and lon_min <= m.get('longitude', 0) <= lon_max
                ]
            
            # Aplicar filtro de calidad
            from quality_manager import DataQualityManager, QualityStrategy
            
            threshold_map = {
                'STRICT': QualityStrategy.STRICT,
                'MODERATE': QualityStrategy.MODERATE,
                'PERMISSIVE': QualityStrategy.PERMISSIVE
            }
            
            strategy = threshold_map.get(quality_threshold, QualityStrategy.MODERATE)
            manager = DataQualityManager(strategy=strategy)
            
            filtered_data, metadata = manager.filter_by_quality(measurements)
            
            # Calcular estadísticas
            if filtered_data:
                concentrations = [m.get('surface_concentration', 0) for m in filtered_data]
                aqis = [m.get('aqi', 0) for m in filtered_data]
                
                stats = {
                    'min_concentration': min(concentrations),
                    'max_concentration': max(concentrations),
                    'avg_concentration': sum(concentrations) / len(concentrations),
                    'median_concentration': sorted(concentrations)[len(concentrations)//2],
                    'min_aqi': min(aqis),
                    'max_aqi': max(aqis),
                    'avg_aqi': sum(aqis) / len(aqis)
                }
                
                # Determinar categoría predominante
                categories = {}
                for m in filtered_data:
                    cat = m.get('aqi_category', 'Desconocido')
                    categories[cat] = categories.get(cat, 0) + 1
                
                dominant_category = max(categories.items(), key=lambda x: x[1])[0]
                
                # Recomendación
                recommendation = self._get_recommendation(dominant_category, stats['avg_aqi'])
            else:
                stats = None
                dominant_category = None
                recommendation = None
            
            # Construir respuesta
            response = {
                'success': True,
                'pollutant': pollutant,
                'timestamp': datetime.now().isoformat(),
                'data_source': {
                    'file': latest_file.name,
                    'last_modified': datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat()
                },
                'data_quality': {
                    'reliability': metadata['data_reliability'],
                    'total_measurements': metadata['total_points'],
                    'valid_measurements': metadata['filtered_points'],
                    'quality_threshold': quality_threshold,
                    'fallback_used': metadata['fallback_used']
                },
                'warning': metadata.get('warning'),
                'statistics': stats,
                'air_quality': {
                    'dominant_category': dominant_category,
                    'recommendation': recommendation
                } if stats else None,
                'measurements': filtered_data[:100],  # Limitar a 100 para respuesta
                'pagination': {
                    'showing': min(100, len(filtered_data)),
                    'total_available': len(filtered_data),
                    'has_more': len(filtered_data) > 100
                }
            }
            
            return response
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'code': 'INTERNAL_ERROR'
            }
    
    def _get_recommendation(self, category: str, avg_aqi: float) -> dict:
        """Genera recomendación basada en categoría de AQI"""
        
        recommendations = {
            'Bueno': {
                'outdoor_activities': 'SEGURO',
                'message': 'La calidad del aire es buena. Ideal para actividades al aire libre.',
                'icon': '✅',
                'sensitive_groups': 'Sin restricciones'
            },
            'Moderado': {
                'outdoor_activities': 'SEGURO_CON_PRECAUCION',
                'message': 'La calidad del aire es aceptable. Personas muy sensibles deben considerar reducir actividades prolongadas.',
                'icon': '⚠️',
                'sensitive_groups': 'Precaución para personas con problemas respiratorios'
            },
            'Dañino para grupos sensibles': {
                'outdoor_activities': 'PRECAUCION',
                'message': 'Grupos sensibles deben limitar actividades prolongadas al aire libre.',
                'icon': '🟡',
                'sensitive_groups': 'Limitar exposición prolongada'
            },
            'Dañino': {
                'outdoor_activities': 'NO_RECOMENDADO',
                'message': 'Evita actividades intensas al aire libre. Todos pueden experimentar efectos en la salud.',
                'icon': '🔴',
                'sensitive_groups': 'Evitar actividades al aire libre'
            }
        }
        
        return recommendations.get(category, {
            'outdoor_activities': 'DESCONOCIDO',
            'message': 'No hay suficiente información para hacer una recomendación.',
            'icon': '❓',
            'sensitive_groups': 'Consultar con autoridades de salud'
        })
    
    def health_check(self) -> dict:
        """
        GET /api/v1/health
        
        Verifica estado del sistema
        """
        from datacenter_optimizer import DatacenterOptimizer
        
        optimizer = DatacenterOptimizer()
        stats = optimizer.get_system_stats()
        
        # Verificar si hay datos recientes (últimas 6 horas)
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=6)
        
        recent_files = []
        for surface_file in self.data_dir.glob('SURFACE_*.json'):
            modified = datetime.fromtimestamp(surface_file.stat().st_mtime)
            if modified >= cutoff:
                recent_files.append(surface_file.name)
        
        return {
            'status': 'healthy' if recent_files else 'stale_data',
            'timestamp': datetime.now().isoformat(),
            'system_stats': {
                'total_files': stats['total_files'],
                'total_size_gb': stats['total_size_gb'],
                'chunks_ready': stats['chunk_files']
            },
            'recent_data': {
                'files': recent_files,
                'count': len(recent_files)
            },
            'message': 'Sistema operativo' if recent_files else 'Datos desactualizados (>6 horas)'
        }

def demo_api():
    """Demostración de la API"""
    print("="*70)
    print("🌐 TEMPO API REST - Demo")
    print("="*70)
    
    api = TempoAPI()
    
    # 1. Health Check
    print("\n1️⃣  Health Check:")
    print("   GET /api/v1/health")
    health = api.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Archivos recientes: {health['recent_data']['count']}")
    
    # 2. Obtener datos NO2 (sin filtro geográfico)
    print("\n2️⃣  Obtener datos NO2:")
    print("   GET /api/v1/tempo/NO2/latest")
    result = api.get_latest_data('NO2')
    
    if result['success']:
        print(f"   ✅ Éxito")
        print(f"   Confiabilidad: {result['data_quality']['reliability']}")
        print(f"   Mediciones válidas: {result['data_quality']['valid_measurements']:,}")
        
        if result['statistics']:
            print(f"\n   📊 Estadísticas:")
            print(f"      NO2 promedio: {result['statistics']['avg_concentration']:.2f} µg/m³")
            print(f"      AQI promedio: {result['statistics']['avg_aqi']:.0f}")
        
        if result['air_quality']:
            print(f"\n   🌤️  Calidad del aire:")
            print(f"      Categoría: {result['air_quality']['dominant_category']}")
            rec = result['air_quality']['recommendation']
            print(f"      {rec['icon']} {rec['message']}")
        
        if result['warning']:
            print(f"\n   ⚠️  ADVERTENCIA: {result['warning']}")
    else:
        print(f"   ❌ Error: {result['error']}")
    
    # 3. Obtener datos O3 para El Salvador
    print("\n3️⃣  Obtener datos O3 (El Salvador):")
    print("   GET /api/v1/tempo/O3/latest?lat_min=13&lat_max=14&lon_min=-90&lon_max=-87")
    result = api.get_latest_data('O3', lat_min=13, lat_max=14, lon_min=-90, lon_max=-87)
    
    if result['success']:
        print(f"   ✅ Éxito")
        print(f"   Mediciones en región: {result['data_quality']['valid_measurements']:,}")
        
        if result['statistics']:
            print(f"   O3 promedio: {result['statistics']['avg_concentration']:.2f} ppb")
            print(f"   AQI promedio: {result['statistics']['avg_aqi']:.0f}")
    else:
        print(f"   ❌ Error: {result['error']}")
    
    print("\n" + "="*70)
    print("💡 Para implementar en producción:")
    print("   1. pip install fastapi uvicorn")
    print("   2. Adaptar este código a FastAPI endpoints")
    print("   3. Agregar autenticación (API keys)")
    print("   4. Configurar CORS para frontend")
    print("   5. Deploy en servidor (Railway, Render, AWS, etc.)")
    print("="*70 + "\n")

if __name__ == "__main__":
    demo_api()
