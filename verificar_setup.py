"""
Script de prueba para verificar la instalación y funcionamiento
"""

import sys


def check_dependencies():
    """Verifica que todas las dependencias estén instaladas"""
    print("🔍 Verificando dependencias...\n")
    
    dependencies = {
        'netCDF4': None,
        'numpy': None,
        'json': None,
        'pathlib': None
    }
    
    all_ok = True
    
    for module_name in dependencies.keys():
        try:
            if module_name == 'netCDF4':
                import netCDF4
                dependencies[module_name] = netCDF4.__version__
            elif module_name == 'numpy':
                import numpy
                dependencies[module_name] = numpy.__version__
            elif module_name == 'json':
                import json
                dependencies[module_name] = "built-in"
            elif module_name == 'pathlib':
                import pathlib
                dependencies[module_name] = "built-in"
            
            print(f"  ✅ {module_name:15} v{dependencies[module_name]}")
        
        except ImportError:
            print(f"  ❌ {module_name:15} NO INSTALADO")
            all_ok = False
    
    print()
    
    if not all_ok:
        print("⚠️  Faltan dependencias. Instala con:")
        print("   pip install -r requirements.txt\n")
        return False
    
    print("✅ Todas las dependencias están instaladas correctamente!\n")
    return True


def check_folders():
    """Verifica que las carpetas necesarias existan"""
    from pathlib import Path
    
    print("📁 Verificando estructura de carpetas...\n")
    
    folders = {
        'tempo_data': Path('tempo_data'),
        'output': Path('output')
    }
    
    all_ok = True
    
    for folder_name, folder_path in folders.items():
        if folder_path.exists():
            print(f"  ✅ {folder_name:15} existe")
        else:
            print(f"  ⚠️  {folder_name:15} no existe (se creará automáticamente)")
            all_ok = False
    
    print()
    return all_ok


def check_nc_files():
    """Verifica si hay archivos .nc disponibles"""
    from pathlib import Path
    
    print("📂 Buscando archivos .nc en tempo_data/...\n")
    
    tempo_data = Path('tempo_data')
    
    if not tempo_data.exists():
        print("  ⚠️  La carpeta 'tempo_data/' no existe aún")
        print("     Se creará al ejecutar el script principal.\n")
        return False
    
    nc_files = list(tempo_data.glob('*.nc'))
    
    if not nc_files:
        print("  ⚠️  No se encontraron archivos .nc")
        print("     Descarga archivos TEMPO y colócalos en 'tempo_data/'\n")
        return False
    
    print(f"  ✅ Encontrados {len(nc_files)} archivo(s):\n")
    
    for filepath in nc_files:
        size_mb = filepath.stat().st_size / (1024 * 1024)
        print(f"     • {filepath.name} ({size_mb:.2f} MB)")
    
    print()
    return True


def test_json_structure():
    """Muestra un ejemplo de la estructura JSON de salida"""
    print("📋 Estructura JSON de salida esperada:\n")
    
    example = {
        "metadata": {
            "scan_time": "2025-09-16T21:43:29Z",
            "product": "NO2",
            "points_extracted": 1523,
            "source_file": "TEMPO_NO2_L2_V03_20250916T214329Z_S012G07.nc"
        },
        "measurements": [
            {
                "latitude": -23.6509,
                "longitude": -70.3975,
                "timestamp": "2025-09-16T21:43:29Z",
                "pollutant": "NO2",
                "concentration_ugm3": 35.2,
                "aqi": 87,
                "quality_flag": 0.92
            },
            {
                "latitude": -23.6510,
                "longitude": -70.3980,
                "timestamp": "2025-09-16T21:43:29Z",
                "pollutant": "NO2",
                "concentration_ugm3": 42.8,
                "aqi": 95,
                "quality_flag": 0.88
            }
        ]
    }
    
    import json
    print(json.dumps(example, indent=2, ensure_ascii=False))
    print()


def main():
    """Función principal de prueba"""
    print("\n" + "="*70)
    print("🛰️  TEMPO DATA PROCESSOR - VERIFICACIÓN DEL SISTEMA")
    print("="*70 + "\n")
    
    # 1. Verificar dependencias
    deps_ok = check_dependencies()
    
    # 2. Verificar carpetas
    folders_ok = check_folders()
    
    # 3. Verificar archivos
    files_ok = check_nc_files()
    
    # 4. Mostrar ejemplo de JSON
    test_json_structure()
    
    # Resumen final
    print("="*70)
    print("📊 RESUMEN:")
    print("="*70 + "\n")
    
    if deps_ok:
        print("  ✅ Dependencias instaladas correctamente")
    else:
        print("  ❌ Faltan dependencias por instalar")
    
    if folders_ok:
        print("  ✅ Estructura de carpetas correcta")
    else:
        print("  ⚠️  Se crearán carpetas al ejecutar el script")
    
    if files_ok:
        print("  ✅ Archivos .nc encontrados - Listo para procesar!")
    else:
        print("  ⚠️  No hay archivos .nc - Descárgalos y colócalos en tempo_data/")
    
    print("\n" + "="*70)
    
    if deps_ok and files_ok:
        print("\n🚀 ¡TODO LISTO! Ejecuta el script principal:")
        print("   python extraer_datos.py\n")
    elif deps_ok:
        print("\n📥 Siguiente paso: Descarga archivos TEMPO")
        print("   Colócalos en la carpeta 'tempo_data/' y ejecuta:")
        print("   python extraer_datos.py\n")
    else:
        print("\n⚙️  Siguiente paso: Instala las dependencias")
        print("   pip install -r requirements.txt\n")


if __name__ == '__main__':
    main()
