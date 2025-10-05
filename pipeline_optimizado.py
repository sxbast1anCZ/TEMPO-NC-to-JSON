"""
PIPELINE OPTIMIZADO v2.0 - Máxima eficiencia tipo DATACENTER

Mejoras implementadas:
✅ Procesamiento incremental (solo archivos nuevos)
✅ Quality filtering inteligente con fallback automático
✅ Caché para evitar reprocesamiento
✅ Limpieza automática de archivos antiguos
✅ Índice espacial para queries rápidas
✅ Estadísticas en tiempo real
✅ Manejo de errores robusto

Autor: Sebastian
Fecha: Octubre 2025
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
import json
import shutil
from quality_manager import DataQualityManager, QualityStrategy
from datacenter_optimizer import DatacenterOptimizer

def run_command(script_name, description):
    """Ejecuta un script de Python y muestra el resultado"""
    print(f"\n{'='*70}")
    print(f"> {description}")
    print(f"{'='*70}")
    
    try:
        # Configurar entorno para soportar UTF-8
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutos máximo
            env=env,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            print(result.stdout)
            print(f"✅ {description} - COMPLETADO")
            return True
        else:
            print(result.stdout)
            print(result.stderr)
            print(f"❌ {description} - ERROR")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱️  {description} - TIMEOUT (>10 min)")
        return False
    except Exception as e:
        print(f"❌ Error al ejecutar {script_name}: {e}")
        return False

def validate_data_quality():
    """Valida calidad de datos procesados"""
    print(f"\n{'='*70}")
    print("🔍 Validando calidad de datos")
    print(f"{'='*70}")
    
    output_dir = Path('output')
    quality_report = {
        'files_checked': 0,
        'high_quality': 0,
        'medium_quality': 0,
        'low_quality': 0,
        'warnings': []
    }
    
    # Verificar archivos SURFACE (ya convertidos)
    for surface_file in output_dir.glob('SURFACE_*.json'):
        try:
            with open(surface_file, 'r') as f:
                data = json.load(f)
            
            manager = DataQualityManager(strategy=QualityStrategy.MODERATE)
            filtered, metadata = manager.filter_by_quality(data['measurements'])
            
            quality_report['files_checked'] += 1
            reliability = metadata['data_reliability']
            
            if reliability == "EXCELENTE" or reliability == "BUENA":
                quality_report['high_quality'] += 1
                status = "✅"
            elif reliability == "ACEPTABLE":
                quality_report['medium_quality'] += 1
                status = "⚠️ "
            else:
                quality_report['low_quality'] += 1
                status = "❌"
                quality_report['warnings'].append(f"{surface_file.name}: {metadata.get('warning', 'Baja calidad')}")
            
            print(f"   {status} {surface_file.name}")
            print(f"      Confiabilidad: {reliability}")
            print(f"      Puntos válidos: {metadata['filtered_points']:,}/{metadata['total_points']:,}")
            
        except Exception as e:
            print(f"   ❌ Error al validar {surface_file.name}: {e}")
    
    # Resumen
    print(f"\n{'='*70}")
    print("📊 RESUMEN DE CALIDAD")
    print(f"{'='*70}")
    print(f"   Archivos verificados: {quality_report['files_checked']}")
    print(f"   ✅ Alta calidad: {quality_report['high_quality']}")
    print(f"   ⚠️  Calidad media: {quality_report['medium_quality']}")
    print(f"   ❌ Baja calidad: {quality_report['low_quality']}")
    
    if quality_report['warnings']:
        print(f"\n⚠️  ADVERTENCIAS:")
        for warning in quality_report['warnings']:
            print(f"   • {warning}")
    
    return quality_report

def clean_nc_files():
    """Elimina archivos .nc de tempo_data/ para ahorrar espacio"""
    print(f"\n{'='*70}")
    print("🧹 Limpiando archivos .nc temporales")
    print(f"{'='*70}")
    
    tempo_data = Path('tempo_data')
    nc_files = list(tempo_data.glob('*.nc'))
    
    if not nc_files:
        print("   No hay archivos .nc para eliminar")
        return
    
    total_size = 0
    for nc_file in nc_files:
        size = nc_file.stat().st_size / 1024 / 1024  # MB
        total_size += size
        print(f"   🗑️  Eliminando: {nc_file.name} ({size:.1f} MB)")
        nc_file.unlink()
    
    print(f"\n✅ Liberados: {total_size:.1f} MB")

def get_output_stats():
    """Muestra estadísticas de los archivos generados"""
    print(f"\n{'='*70}")
    print("📊 ESTADÍSTICAS DE SALIDA")
    print(f"{'='*70}")
    
    optimizer = DatacenterOptimizer()
    stats = optimizer.get_system_stats()
    
    print(f"\n💾 Almacenamiento:")
    print(f"   Total de archivos: {stats['total_files']}")
    print(f"   Tamaño total: {stats['total_size_gb']:.2f} GB ({stats['total_size_mb']:.1f} MB)")
    print(f"   JSONs principales: {stats['json_files']}")
    print(f"   Chunks listos para Cloud: {stats['chunk_files']}")
    
    # Detalle de archivos más recientes
    output_dir = Path('output')
    json_files = sorted(output_dir.glob('SURFACE_*.json'), key=lambda x: x.stat().st_mtime, reverse=True)[:3]
    
    if json_files:
        print(f"\n📄 Archivos más recientes:")
        for jf in json_files:
            size = jf.stat().st_size / 1024 / 1024
            modified = datetime.fromtimestamp(jf.stat().st_mtime)
            print(f"   • {jf.name}")
            print(f"     Tamaño: {size:.1f} MB | Modificado: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
            
            try:
                with open(jf, 'r') as f:
                    data = json.load(f)
                    count = len(data.get('measurements', []))
                    print(f"     Puntos: {count:,}")
            except:
                pass

def clean_old_data(days_to_keep=7):
    """Limpia datos antiguos automáticamente"""
    print(f"\n{'='*70}")
    print(f"🧹 Limpieza de datos antiguos (>{days_to_keep} días)")
    print(f"{'='*70}")
    
    optimizer = DatacenterOptimizer()
    optimizer.clean_old_files(days_to_keep=days_to_keep)

def main():
    """Función principal del pipeline optimizado"""
    start_time = datetime.now()
    
    print("\n" + "="*70)
    print("🚀 PIPELINE OPTIMIZADO v2.0 - DATACENTER MODE")
    print("="*70)
    print(f"📅 Inicio: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    steps_completed = []
    steps_failed = []
    
    # PASO 1: Descargar archivos más recientes
    if run_command('descargar_tempo_v2.py', 'Paso 1: Descargar archivos TEMPO'):
        steps_completed.append("Descarga")
    else:
        steps_failed.append("Descarga")
        print("\n⚠️  Error en descarga. Continuando con archivos existentes...")
    
    # PASO 2: Extraer datos de archivos .nc
    if run_command('extraer_datos.py', 'Paso 2: Extraer datos de .nc'):
        steps_completed.append("Extracción")
    else:
        steps_failed.append("Extracción")
        print("\n❌ Error crítico en extracción. Abortando pipeline.")
        return
    
    # PASO 3: Convertir a concentraciones superficiales + AQI
    if run_command('convertir_a_superficie.py', 'Paso 3: Convertir a superficie + AQI'):
        steps_completed.append("Conversión")
    else:
        steps_failed.append("Conversión")
        print("\n⚠️  Error en conversión. Continuando...")
    
    # PASO 4: Validar calidad de datos (NUEVO)
    quality_report = validate_data_quality()
    steps_completed.append("Validación de calidad")
    
    # PASO 5: Dividir en chunks
    if run_command('dividir_archivos.py', 'Paso 5: Dividir en chunks'):
        steps_completed.append("División en chunks")
    else:
        steps_failed.append("División en chunks")
        print("\n⚠️  Error al dividir chunks. Continuando...")
    
    # PASO 6: Limpiar archivos .nc
    clean_nc_files()
    
    # PASO 7: Limpiar datos antiguos (NUEVO)
    clean_old_data(days_to_keep=7)
    
    # PASO 8: Estadísticas finales
    get_output_stats()
    
    # RESUMEN FINAL
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n{'='*70}")
    print("🏁 PIPELINE COMPLETADO")
    print(f"{'='*70}")
    print(f"⏱️  Duración: {duration:.1f} segundos ({duration/60:.1f} minutos)")
    print(f"✅ Pasos exitosos: {len(steps_completed)}")
    if steps_completed:
        for step in steps_completed:
            print(f"   • {step}")
    
    if steps_failed:
        print(f"\n⚠️  Pasos fallidos: {len(steps_failed)}")
        for step in steps_failed:
            print(f"   • {step}")
    
    # Alertas de calidad
    if quality_report['low_quality'] > 0:
        print(f"\n⚠️  ALERTA: {quality_report['low_quality']} archivo(s) con baja calidad")
        print("   Los datos están disponibles pero marcados como baja confianza")
        print("   La API REST debe advertir a los usuarios")
    
    print(f"\n📅 Finalizado: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    # Siguiente ejecución
    from datetime import timedelta
    next_run = end_time + timedelta(hours=3)
    print(f"⏰ Próxima ejecución programada: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

if __name__ == "__main__":
    main()
