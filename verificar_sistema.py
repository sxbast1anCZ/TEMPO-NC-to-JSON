"""
Script de verificación completa del sistema

Verifica que todo esté funcionando correctamente después de la implementación.

Autor: Sebastian
Fecha: Octubre 2025
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
import sys

def check(description, condition, details=""):
    """Helper para mostrar checks"""
    status = "✅" if condition else "❌"
    print(f"{status} {description}")
    if details and not condition:
        print(f"   {details}")
    return condition

def main():
    print("="*70)
    print("🔍 VERIFICACIÓN COMPLETA DEL SISTEMA TEMPO")
    print("="*70)
    print()
    
    all_ok = True
    
    # 1. Verificar estructura de directorios
    print("📁 Verificando estructura de directorios...")
    all_ok &= check("Directorio tempo_data/", Path('tempo_data').exists())
    all_ok &= check("Directorio output/", Path('output').exists())
    all_ok &= check("Directorio output/chunks/", Path('output/chunks').exists())
    all_ok &= check("Directorio output/.cache/", Path('output/.cache').exists())
    print()
    
    # 2. Verificar archivos de configuración
    print("⚙️  Verificando configuración...")
    env_exists = Path('.env').exists()
    all_ok &= check("Archivo .env", env_exists, "Crea .env con credenciales NASA")
    all_ok &= check("Archivo .gitignore", Path('.gitignore').exists())
    print()
    
    # 3. Verificar scripts principales
    print("📜 Verificando scripts...")
    scripts = [
        'descargar_tempo_v2.py',
        'extraer_datos.py',
        'convertir_a_superficie.py',
        'dividir_archivos.py',
        'quality_manager.py',
        'datacenter_optimizer.py',
        'pipeline_optimizado.py',
        'api_example.py'
    ]
    
    for script in scripts:
        all_ok &= check(f"Script {script}", Path(script).exists())
    print()
    
    # 4. Verificar datos procesados
    print("📊 Verificando datos procesados...")
    output_dir = Path('output')
    
    # JSONs principales
    no2_files = list(output_dir.glob('SURFACE_NO2_*.json'))
    o3_files = list(output_dir.glob('SURFACE_O3_*.json'))
    
    all_ok &= check(f"Archivos NO2 procesados ({len(no2_files)})", len(no2_files) > 0)
    all_ok &= check(f"Archivos O3 procesados ({len(o3_files)})", len(o3_files) > 0)
    
    # Chunks
    chunks_dir = Path('output/chunks')
    chunk_files = list(chunks_dir.glob('*.json')) if chunks_dir.exists() else []
    all_ok &= check(f"Chunks generados ({len(chunk_files)})", len(chunk_files) > 0)
    print()
    
    # 5. Verificar calidad de datos
    print("🔍 Verificando calidad de datos...")
    
    if no2_files:
        latest_no2 = sorted(no2_files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
        try:
            with open(latest_no2, 'r') as f:
                data = json.load(f)
            
            measurements = data.get('measurements', [])
            total = len(measurements)
            
            if total > 0:
                # Analizar quality flags
                quality_flags = [m.get('quality_flag', 0) for m in measurements]
                good_quality = sum(1 for qf in quality_flags if qf >= 0.5)
                pct_good = (good_quality / total) * 100
                
                print(f"   📄 {latest_no2.name}")
                print(f"      Total de puntos: {total:,}")
                print(f"      Puntos con buena calidad: {good_quality:,} ({pct_good:.1f}%)")
                
                all_ok &= check(f"   NO2 tiene datos válidos", total > 0)
                
                if pct_good >= 50:
                    print(f"      ✅ Excelente calidad de datos")
                elif good_quality > 0:
                    print(f"      ⚠️  Calidad moderada - algunos datos buenos")
                else:
                    print(f"      ⚠️  Baja calidad - fallback será usado")
        except Exception as e:
            print(f"   ❌ Error al verificar NO2: {e}")
            all_ok = False
    print()
    
    # 6. Verificar frescura de datos
    print("🕒 Verificando frescura de datos...")
    cutoff = datetime.now() - timedelta(hours=6)
    
    recent_files = []
    for surface_file in output_dir.glob('SURFACE_*.json'):
        modified = datetime.fromtimestamp(surface_file.stat().st_mtime)
        if modified >= cutoff:
            recent_files.append((surface_file.name, modified))
    
    if recent_files:
        print(f"   ✅ {len(recent_files)} archivo(s) procesado(s) en las últimas 6 horas")
        for name, modified in sorted(recent_files, key=lambda x: x[1], reverse=True)[:3]:
            print(f"      • {name}")
            print(f"        {modified.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"   ⚠️  No hay datos procesados en las últimas 6 horas")
        print(f"      Ejecuta: python pipeline_optimizado.py")
    print()
    
    # 7. Verificar espacio en disco
    print("💾 Verificando uso de disco...")
    from datacenter_optimizer import DatacenterOptimizer
    
    try:
        optimizer = DatacenterOptimizer()
        stats = optimizer.get_system_stats()
        
        print(f"   Total de archivos: {stats['total_files']}")
        print(f"   Tamaño total: {stats['total_size_gb']:.2f} GB ({stats['total_size_mb']:.1f} MB)")
        
        if stats['total_size_gb'] < 10:
            print(f"   ✅ Uso de disco normal")
        else:
            print(f"   ⚠️  Uso de disco alto - considera ejecutar limpieza")
    except Exception as e:
        print(f"   ⚠️  No se pudo verificar: {e}")
    print()
    
    # 8. Verificar dependencias de Python
    print("🐍 Verificando dependencias de Python...")
    dependencies = {
        'netCDF4': 'netCDF4',
        'numpy': 'numpy',
        'requests': 'requests',
        'beautifulsoup4': 'bs4',
        'python-dotenv': 'dotenv'
    }
    
    missing = []
    for package, import_name in dependencies.items():
        try:
            __import__(import_name)
            check(f"   {package}", True)
        except ImportError:
            check(f"   {package}", False, f"Instala con: pip install {package}")
            missing.append(package)
            all_ok = False
    
    if missing:
        print(f"\n   Para instalar faltantes:")
        print(f"   pip install {' '.join(missing)}")
    print()
    
    # 9. Test de API
    print("🌐 Probando API...")
    try:
        from api_example import TempoAPI
        api = TempoAPI()
        
        health = api.health_check()
        all_ok &= check("   API health check", health['status'] == 'healthy' or health['status'] == 'stale_data')
        
        if health['status'] == 'healthy':
            print(f"      ✅ Sistema saludable con {health['recent_data']['count']} archivos recientes")
        else:
            print(f"      ⚠️  {health['message']}")
    except Exception as e:
        print(f"   ❌ Error en API: {e}")
        all_ok = False
    print()
    
    # 10. Verificar tarea programada (Windows)
    print("⏰ Verificando tarea programada...")
    import platform
    
    if platform.system() == 'Windows':
        import subprocess
        try:
            result = subprocess.run(
                ['powershell', '-Command', 'Get-ScheduledTask -TaskName "TEMPO_Data_Pipeline" -ErrorAction SilentlyContinue'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if 'TEMPO_Data_Pipeline' in result.stdout:
                print("   ✅ Tarea programada configurada")
                print("      Para ejecutar manualmente:")
                print("      Start-ScheduledTask -TaskName 'TEMPO_Data_Pipeline'")
            else:
                print("   ⚠️  Tarea programada no encontrada")
                print("      Para configurar, ejecuta (como Administrador):")
                print("      .\\configurar_tarea_automatica.ps1")
        except Exception as e:
            print(f"   ⚠️  No se pudo verificar: {e}")
    else:
        print("   ⏭️  No es Windows, configurar cron job manualmente")
    print()
    
    # RESUMEN FINAL
    print("="*70)
    if all_ok:
        print("✅ SISTEMA COMPLETAMENTE FUNCIONAL")
        print()
        print("Próximos pasos:")
        print("1. Ejecutar: .\\configurar_tarea_automatica.ps1 (si no está configurado)")
        print("2. Esperar 3 horas y verificar que se generan datos nuevos")
        print("3. Probar API: python api_example.py")
        print("4. Integrar con tu backend/frontend")
    else:
        print("⚠️  SISTEMA REQUIERE ATENCIÓN")
        print()
        print("Revisa los puntos marcados con ❌ arriba.")
        print("Consulta ARQUITECTURA.md para más detalles.")
    print("="*70)
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
