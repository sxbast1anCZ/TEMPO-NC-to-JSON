"""
Módulo de manejo inteligente de calidad de datos TEMPO

Este módulo implementa estrategias para manejar diferentes escenarios
de calidad de datos según las necesidades de la API REST.

Estrategias:
1. STRICT: Solo datos con quality_flag > 0.75 (máxima calidad)
2. MODERATE: Datos con quality_flag > 0.5 (calidad moderada)
3. PERMISSIVE: Datos con quality_flag > 0 (cualquier dato válido)
4. FALLBACK: Si no hay datos buenos, usa todos y marca como "baja confianza"

Autor: Sebastian
Fecha: Octubre 2025
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class QualityStrategy:
    """Estrategias de filtrado por calidad"""
    STRICT = 0.75      # Solo datos excelentes
    MODERATE = 0.50    # Datos buenos
    PERMISSIVE = 0.01  # Cualquier dato válido
    FALLBACK = 0.0     # Incluir todo si no hay alternativa

class DataQualityManager:
    """Gestor inteligente de calidad de datos"""
    
    def __init__(self, strategy=QualityStrategy.MODERATE):
        self.strategy = strategy
        self.stats = {
            'total_points': 0,
            'filtered_points': 0,
            'quality_distribution': {},
            'strategy_used': None,
            'fallback_triggered': False
        }
    
    def analyze_quality_distribution(self, measurements: List[Dict]) -> Dict:
        """
        Analiza la distribución de quality_flag en el dataset
        
        Returns:
            Dict con estadísticas de calidad
        """
        distribution = {}
        total = len(measurements)
        
        for m in measurements:
            qf = m.get('quality_flag', 0)
            qf_bucket = self._get_quality_bucket(qf)
            distribution[qf_bucket] = distribution.get(qf_bucket, 0) + 1
        
        return {
            'total': total,
            'distribution': distribution,
            'percentages': {k: (v/total)*100 for k, v in distribution.items()},
            'has_excellent': distribution.get('excellent', 0) > 0,
            'has_good': distribution.get('good', 0) > 0,
            'has_fair': distribution.get('fair', 0) > 0,
            'all_poor': distribution.get('poor', 0) == total
        }
    
    def _get_quality_bucket(self, qf: float) -> str:
        """Clasifica quality_flag en buckets"""
        if qf >= 0.75:
            return 'excellent'
        elif qf >= 0.5:
            return 'good'
        elif qf > 0:
            return 'fair'
        else:
            return 'poor'
    
    def filter_by_quality(self, measurements: List[Dict], 
                         force_strategy: float = None) -> Tuple[List[Dict], Dict]:
        """
        Filtra mediciones por calidad con fallback automático
        
        Args:
            measurements: Lista de mediciones
            force_strategy: Forzar una estrategia específica (opcional)
        
        Returns:
            (mediciones_filtradas, metadata)
        """
        self.stats['total_points'] = len(measurements)
        
        # Analizar distribución
        quality_analysis = self.analyze_quality_distribution(measurements)
        
        # Determinar estrategia a usar
        strategy_to_use = force_strategy or self.strategy
        
        # Intentar con la estrategia configurada
        filtered = [m for m in measurements if m.get('quality_flag', 0) >= strategy_to_use]
        
        # FALLBACK AUTOMÁTICO si no hay datos
        if len(filtered) == 0:
            print("⚠️  No hay datos con la estrategia MODERATE")
            
            # Intentar PERMISSIVE
            filtered = [m for m in measurements if m.get('quality_flag', 0) > QualityStrategy.PERMISSIVE]
            
            if len(filtered) == 0:
                print("⚠️  No hay datos con la estrategia PERMISSIVE")
                print("🔄 FALLBACK: Usando TODOS los datos (marcar como baja confianza)")
                
                filtered = measurements
                strategy_to_use = QualityStrategy.FALLBACK
                self.stats['fallback_triggered'] = True
            else:
                print(f"✅ Fallback a PERMISSIVE: {len(filtered):,} puntos")
                strategy_to_use = QualityStrategy.PERMISSIVE
        
        self.stats['filtered_points'] = len(filtered)
        self.stats['strategy_used'] = strategy_to_use
        self.stats['quality_distribution'] = quality_analysis
        
        # Metadata para la API
        metadata = {
            'total_points': len(measurements),
            'filtered_points': len(filtered),
            'quality_threshold': strategy_to_use,
            'fallback_used': self.stats['fallback_triggered'],
            'data_reliability': self._get_reliability_label(strategy_to_use),
            'quality_analysis': quality_analysis,
            'warning': None
        }
        
        # Advertencia si se usó fallback
        if self.stats['fallback_triggered']:
            metadata['warning'] = (
                "Los datos pueden tener baja confianza debido a condiciones "
                "atmosféricas adversas (nubes, aerosoles, etc.). "
                "Use con precaución."
            )
        
        return filtered, metadata
    
    def _get_reliability_label(self, threshold: float) -> str:
        """Etiqueta de confiabilidad para la API"""
        if threshold >= QualityStrategy.STRICT:
            return "EXCELENTE"
        elif threshold >= QualityStrategy.MODERATE:
            return "BUENA"
        elif threshold >= QualityStrategy.PERMISSIVE:
            return "ACEPTABLE"
        else:
            return "BAJA_CONFIANZA"
    
    def get_api_response(self, measurements: List[Dict], 
                        pollutant: str) -> Dict:
        """
        Genera respuesta lista para API REST con manejo inteligente de calidad
        
        Returns:
            Dict con estructura para API
        """
        filtered_data, metadata = self.filter_by_quality(measurements)
        
        # Calcular estadísticas
        if filtered_data:
            concentrations = [m.get('surface_concentration', 0) for m in filtered_data]
            aqis = [m.get('aqi', 0) for m in filtered_data]
            
            stats = {
                'min': min(concentrations),
                'max': max(concentrations),
                'mean': sum(concentrations) / len(concentrations),
                'median': sorted(concentrations)[len(concentrations)//2],
                'aqi_max': max(aqis),
                'aqi_mean': sum(aqis) / len(aqis)
            }
        else:
            stats = None
        
        return {
            'success': True,
            'pollutant': pollutant,
            'timestamp': datetime.now().isoformat(),
            'data_quality': {
                'reliability': metadata['data_reliability'],
                'total_measurements': metadata['total_points'],
                'valid_measurements': metadata['filtered_points'],
                'quality_threshold': metadata['quality_threshold'],
                'fallback_used': metadata['fallback_used']
            },
            'warning': metadata.get('warning'),
            'statistics': stats,
            'measurements': filtered_data[:1000],  # Limitar a 1000 para API
            'has_more': len(filtered_data) > 1000,
            'total_available': len(filtered_data)
        }

def main():
    """Ejemplo de uso"""
    print("="*70)
    print("🔍 DATA QUALITY MANAGER - Sistema de Validación Inteligente")
    print("="*70)
    
    # Ejemplo con archivo NO2 nuevo
    print("\nProbando con archivo NO2 V04 (debería tener quality_flag = 1.0)...")
    
    try:
        with open('output/SURFACE_NO2_TEMPO_NO2_L2_V04_20251004T152407Z_S005G09.json', 'r') as f:
            data = json.load(f)
        
        manager = DataQualityManager(strategy=QualityStrategy.MODERATE)
        api_response = manager.get_api_response(data['measurements'], 'NO2')
        
        print(f"\n✅ Resultado:")
        print(f"   Confiabilidad: {api_response['data_quality']['reliability']}")
        print(f"   Mediciones totales: {api_response['data_quality']['total_measurements']:,}")
        print(f"   Mediciones válidas: {api_response['data_quality']['valid_measurements']:,}")
        print(f"   Fallback usado: {api_response['data_quality']['fallback_used']}")
        
        if api_response['warning']:
            print(f"\n⚠️  Advertencia: {api_response['warning']}")
        
        if api_response['statistics']:
            print(f"\n📊 Estadísticas:")
            print(f"   NO2 promedio: {api_response['statistics']['mean']:.2f} µg/m³")
            print(f"   AQI promedio: {api_response['statistics']['aqi_mean']:.0f}")
        
    except FileNotFoundError:
        print("❌ Archivo no encontrado")
    
    # Ejemplo con archivo viejo (quality_flag = 0)
    print("\n" + "="*70)
    print("Probando con archivo NO2 V03 (quality_flag = 0, debería usar fallback)...")
    
    try:
        with open('output/SURFACE_NO2_TEMPO_NO2_L2_V03_20250916T214329Z_S012G07.json', 'r') as f:
            data = json.load(f)
        
        manager = DataQualityManager(strategy=QualityStrategy.MODERATE)
        api_response = manager.get_api_response(data['measurements'], 'NO2')
        
        print(f"\n✅ Resultado:")
        print(f"   Confiabilidad: {api_response['data_quality']['reliability']}")
        print(f"   Mediciones totales: {api_response['data_quality']['total_measurements']:,}")
        print(f"   Mediciones válidas: {api_response['data_quality']['valid_measurements']:,}")
        print(f"   Fallback usado: {api_response['data_quality']['fallback_used']}")
        
        if api_response['warning']:
            print(f"\n⚠️  Advertencia: {api_response['warning']}")
    
    except FileNotFoundError:
        print("❌ Archivo no encontrado")

if __name__ == "__main__":
    main()
