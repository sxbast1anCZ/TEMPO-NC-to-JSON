"""
Script auxiliar para inspeccionar la estructura de archivos TEMPO .nc
Útil para entender qué variables y grupos contienen los archivos
"""

import netCDF4 as nc
import sys
from pathlib import Path


def inspect_nc_file(filepath):
    """
    Inspecciona y muestra la estructura completa de un archivo .nc
    
    Args:
        filepath: Ruta al archivo .nc
    """
    print(f"\n{'='*70}")
    print(f"📂 Archivo: {filepath.name}")
    print(f"{'='*70}\n")
    
    try:
        dataset = nc.Dataset(filepath, 'r')
        
        # Atributos globales
        print("🌐 ATRIBUTOS GLOBALES:")
        print("-" * 70)
        for attr_name in dataset.ncattrs():
            attr_value = getattr(dataset, attr_name)
            print(f"  {attr_name}: {attr_value}")
        
        # Dimensiones
        print(f"\n📏 DIMENSIONES:")
        print("-" * 70)
        for dim_name, dim in dataset.dimensions.items():
            print(f"  {dim_name}: {len(dim)} {'(unlimited)' if dim.isunlimited() else ''}")
        
        # Variables en el nivel raíz
        print(f"\n📊 VARIABLES (nivel raíz):")
        print("-" * 70)
        if dataset.variables:
            for var_name, var in dataset.variables.items():
                print(f"  {var_name}:")
                print(f"    - Tipo: {var.dtype}")
                print(f"    - Dimensiones: {var.dimensions}")
                print(f"    - Shape: {var.shape}")
                if hasattr(var, 'units'):
                    print(f"    - Unidades: {var.units}")
                if hasattr(var, 'long_name'):
                    print(f"    - Nombre: {var.long_name}")
                print()
        else:
            print("  (No hay variables en el nivel raíz)")
        
        # Grupos
        print(f"\n📁 GRUPOS:")
        print("-" * 70)
        if dataset.groups:
            for group_name, group in dataset.groups.items():
                print(f"\n  Grupo: {group_name}")
                print(f"  {'-' * 65}")
                
                # Variables del grupo
                if group.variables:
                    print(f"  Variables en '{group_name}':")
                    for var_name, var in group.variables.items():
                        print(f"    • {var_name}:")
                        print(f"      - Tipo: {var.dtype}")
                        print(f"      - Dimensiones: {var.dimensions}")
                        print(f"      - Shape: {var.shape}")
                        if hasattr(var, 'units'):
                            print(f"      - Unidades: {var.units}")
                        if hasattr(var, 'long_name'):
                            print(f"      - Nombre: {var.long_name}")
                
                # Subgrupos
                if group.groups:
                    print(f"\n  Subgrupos en '{group_name}':")
                    for subgroup_name in group.groups.keys():
                        print(f"    • {subgroup_name}")
        else:
            print("  (No hay grupos definidos)")
        
        dataset.close()
        print(f"\n{'='*70}\n")
        
    except Exception as e:
        print(f"❌ Error al inspeccionar {filepath.name}: {e}\n")


def main():
    """Función principal"""
    print("\n🔍 INSPECTOR DE ARCHIVOS TEMPO .nc\n")
    
    # Verificar si se pasó un archivo como argumento
    if len(sys.argv) > 1:
        filepath = Path(sys.argv[1])
        if filepath.exists():
            inspect_nc_file(filepath)
        else:
            print(f"❌ Archivo no encontrado: {filepath}")
        return
    
    # Si no, inspeccionar todos los archivos en tempo_data/
    tempo_data = Path('tempo_data')
    
    if not tempo_data.exists():
        print("❌ No se encontró la carpeta 'tempo_data/'")
        print("   Uso: python inspeccionar_nc.py [ruta_archivo.nc]")
        return
    
    nc_files = list(tempo_data.glob('*.nc'))
    
    if not nc_files:
        print("⚠️  No se encontraron archivos .nc en 'tempo_data/'")
        print("   Coloca los archivos TEMPO descargados en esa carpeta.")
        print("\n   Uso alternativo: python inspeccionar_nc.py [ruta_archivo.nc]")
        return
    
    print(f"✅ Encontrados {len(nc_files)} archivo(s) .nc\n")
    
    for filepath in nc_files:
        inspect_nc_file(filepath)
        
        # Preguntar si continuar con el siguiente archivo
        if filepath != nc_files[-1]:
            respuesta = input("Presiona Enter para continuar con el siguiente archivo (o 'q' para salir)... ")
            if respuesta.lower() == 'q':
                break


if __name__ == '__main__':
    main()
