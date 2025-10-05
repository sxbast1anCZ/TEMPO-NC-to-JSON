"""
Script para extraer datos de archivos TEMPO (.nc) de la NASA
Procesa NO2, O3 y Aerosol Index y genera JSONs estructurados
"""

import netCDF4 as nc
import numpy as np
import json
from datetime import datetime
from pathlib import Path
import glob


class TEMPOProcessor:
    """Procesador de archivos TEMPO de la NASA"""
    
    # Factores de conversión y configuración AQI
    AQI_BREAKPOINTS = {
        'NO2': [  # en µg/m³
            (0, 53, 0, 50),      # Bueno
            (54, 100, 51, 100),   # Moderado
            (101, 360, 101, 150), # Insalubre para grupos sensibles
            (361, 649, 151, 200), # Insalubre
            (650, 1249, 201, 300),# Muy insalubre
            (1250, 2049, 301, 500)# Peligroso
        ],
        'O3': [  # en ppb (convertir a µg/m³: ppb * 2.0)
            (0, 54, 0, 50),
            (55, 70, 51, 100),
            (71, 85, 101, 150),
            (86, 105, 151, 200),
            (106, 200, 201, 300),
            (201, 404, 301, 500)
        ],
        'AOD': [  # Aerosol Optical Depth (proxy para PM)
            (0, 0.15, 0, 50),
            (0.151, 0.25, 51, 100),
            (0.251, 0.35, 101, 150),
            (0.351, 0.42, 151, 200),
            (0.421, 0.50, 201, 300),
            (0.501, 1.0, 301, 500)
        ]
    }
    
    def __init__(self, input_folder='tempo_data', output_folder='output'):
        """
        Inicializa el procesador
        
        Args:
            input_folder: Carpeta con archivos .nc
            output_folder: Carpeta donde guardar JSONs
        """
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True)
    
    def calculate_aqi(self, concentration, pollutant_type):
        """
        Calcula el AQI (Air Quality Index) para una concentración dada
        
        Args:
            concentration: Concentración del contaminante
            pollutant_type: Tipo de contaminante ('NO2', 'O3', 'AOD')
        
        Returns:
            AQI calculado o None si no es válido
        """
        if concentration is None or np.isnan(concentration) or concentration < 0:
            return None
        
        breakpoints = self.AQI_BREAKPOINTS.get(pollutant_type, [])
        
        for bp_lo, bp_hi, aqi_lo, aqi_hi in breakpoints:
            if bp_lo <= concentration <= bp_hi:
                # Fórmula AQI: I = ((I_hi - I_lo) / (C_hi - C_lo)) * (C - C_lo) + I_lo
                aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (concentration - bp_lo) + aqi_lo
                return round(aqi)
        
        # Si está fuera de rango, retornar el máximo
        return 500
    
    def extract_timestamp(self, filename):
        """
        Extrae el timestamp del nombre del archivo TEMPO
        Formato: TEMPO_PRODUCT_L2_V03_YYYYMMDDTHHMMSSz_SXXGXX
        
        Args:
            filename: Nombre del archivo
        
        Returns:
            Timestamp en formato ISO 8601
        """
        try:
            # Buscar el patrón de fecha en el nombre del archivo
            parts = filename.split('_')
            for part in parts:
                if 'T' in part and 'Z' in part:
                    # Formato: 20250916T214329Z
                    date_str = part.replace('Z', '')
                    dt = datetime.strptime(date_str, '%Y%m%dT%H%M%S')
                    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        except Exception as e:
            print(f"⚠️  No se pudo extraer timestamp de {filename}: {e}")
        
        return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    def process_no2_file(self, filepath):
        """
        Procesa archivo TEMPO de NO2
        
        Args:
            filepath: Ruta al archivo .nc
        
        Returns:
            Diccionario con datos estructurados
        """
        print(f"📂 Procesando NO2: {filepath.name}")
        
        try:
            dataset = nc.Dataset(filepath, 'r')
            
            # Extraer variables principales
            # TEMPO almacena datos en grupos, explorar estructura
            if 'product' in dataset.groups:
                product_group = dataset.groups['product']
                no2_column = product_group.variables.get('vertical_column_troposphere', None)
                quality_flag = product_group.variables.get('main_data_quality_flag', None)
            else:
                # Intentar acceso directo
                no2_column = dataset.variables.get('vertical_column_troposphere', 
                                                   dataset.variables.get('nitrogen_dioxide_vertical_column', None))
                quality_flag = dataset.variables.get('main_data_quality_flag', 
                                                     dataset.variables.get('quality_flag', None))
            
            # Extraer coordenadas geográficas
            if 'geolocation' in dataset.groups:
                geo_group = dataset.groups['geolocation']
                latitude = geo_group.variables['latitude'][:]
                longitude = geo_group.variables['longitude'][:]
            else:
                latitude = dataset.variables['latitude'][:]
                longitude = dataset.variables['longitude'][:]
            
            # IMPORTANTE: TEMPO proporciona columnas verticales en moléculas/cm²
            # NO son concentraciones superficiales, sino integración de toda la columna troposférica
            # Para uso práctico, convertimos a unidades × 10^15 molec/cm² (unidad estándar)
            CONVERSION_FACTOR = 1e-15  # Mantener en 10^15 molec/cm²
            
            timestamp = self.extract_timestamp(filepath.name)
            measurements = []
            
            # Iterar sobre los datos
            no2_data = no2_column[:] if no2_column is not None else np.array([])
            quality_data = quality_flag[:] if quality_flag is not None else np.ones_like(no2_data)
            
            for i in range(latitude.shape[0]):
                for j in range(latitude.shape[1]):
                    lat = float(latitude[i, j])
                    lon = float(longitude[i, j])
                    
                    # Verificar valores válidos
                    if np.isnan(lat) or np.isnan(lon):
                        continue
                    
                    if no2_column is not None:
                        no2_val = float(no2_data[i, j])
                        quality_val = float(quality_data[i, j]) if quality_data.size > 0 else 1.0
                        
                        # Filtrar valores inválidos Y datos de mala calidad
                        if np.isnan(no2_val) or no2_val < 0:
                            continue
                        
                        # IMPORTANTE: Filtrar por quality_flag
                        # quality_flag = 0 indica datos malos (nubes, errores)
                        # Solo aceptar quality_flag > 0 (datos válidos)
                        if quality_val <= 0:
                            continue
                        
                        # Convertir a µg/m³
                        concentration = no2_val * CONVERSION_FACTOR
                        
                        measurements.append({
                            "latitude": round(lat, 6),
                            "longitude": round(lon, 6),
                            "timestamp": timestamp,
                            "pollutant": "NO2",
                            "vertical_column": round(concentration, 4),  # 10^15 molec/cm²
                            "unit": "10^15 molec/cm²",
                            "quality_flag": round(quality_val, 3)
                        })
            
            dataset.close()
            
            return {
                "metadata": {
                    "scan_time": timestamp,
                    "product": "NO2",
                    "points_extracted": len(measurements),
                    "source_file": filepath.name
                },
                "measurements": measurements
            }
        
        except Exception as e:
            print(f"❌ Error procesando {filepath.name}: {e}")
            return None
    
    def process_o3_file(self, filepath):
        """
        Procesa archivo TEMPO de O3 (Ozono total) - Soporta L2 y L3
        
        Args:
            filepath: Ruta al archivo .nc
        
        Returns:
            Diccionario con datos estructurados
        """
        print(f"📂 Procesando O3: {filepath.name}")
        
        try:
            dataset = nc.Dataset(filepath, 'r')
            
            # Detectar si es L2 o L3
            is_l3 = 'L3' in filepath.name or dataset.processing_level == '3'
            
            if is_l3:
                # Procesamiento L3 (grilla regular)
                product_group = dataset.groups['product']
                o3_column = product_group.variables.get('column_amount_o3', None)
                
                # Coordenadas en L3 son arrays 1D
                latitude = dataset.variables['latitude'][:]
                longitude = dataset.variables['longitude'][:]
                
                # L3 tiene dimensión de tiempo
                o3_data = o3_column[0, :, :] if o3_column is not None else np.array([])
                
            else:
                # Procesamiento L2 (píxeles originales)
                if 'product' in dataset.groups:
                    product_group = dataset.groups['product']
                    o3_column = product_group.variables.get('ozone_total_vertical_column', None)
                    quality_flag = product_group.variables.get('main_data_quality_flag', None)
                else:
                    o3_column = dataset.variables.get('ozone_total_vertical_column', 
                                                      dataset.variables.get('ozone', None))
                    quality_flag = dataset.variables.get('main_data_quality_flag', 
                                                         dataset.variables.get('quality_flag', None))
                
                # Coordenadas en L2
                if 'geolocation' in dataset.groups:
                    geo_group = dataset.groups['geolocation']
                    latitude = geo_group.variables['latitude'][:]
                    longitude = geo_group.variables['longitude'][:]
                else:
                    latitude = dataset.variables['latitude'][:]
                    longitude = dataset.variables['longitude'][:]
                
                o3_data = o3_column[:] if o3_column is not None else np.array([])
            
            timestamp = self.extract_timestamp(filepath.name)
            measurements = []
            
            # IMPORTANTE: TEMPO proporciona O3 en Dobson Units (DU)
            # Mantenemos las unidades originales DU
            # 1 DU = 2.69×10^16 moléculas/cm² de O3
            CONVERSION_FACTOR = 1.0  # Mantener en DU
            
            if is_l3:
                # Iterar sobre grilla regular L3
                for i in range(len(latitude)):
                    for j in range(len(longitude)):
                        lat = float(latitude[i])
                        lon = float(longitude[j])
                        
                        if o3_column is not None:
                            o3_val = float(o3_data[i, j])
                            
                            # Filtrar valores inválidos
                            if np.isnan(o3_val) or o3_val < 0:
                                continue
                            
                            concentration = o3_val * CONVERSION_FACTOR
                            
                            measurements.append({
                                "latitude": round(lat, 6),
                                "longitude": round(lon, 6),
                                "timestamp": timestamp,
                                "pollutant": "O3",
                                "vertical_column_du": round(concentration, 4),  # Dobson Units
                                "unit": "DU",
                                "quality_flag": 1.0  # L3 no tiene quality flag individual
                            })
            else:
                # Iterar sobre píxeles L2
                quality_data = quality_flag[:] if quality_flag is not None else np.ones_like(o3_data)
                
                for i in range(latitude.shape[0]):
                    for j in range(latitude.shape[1]):
                        lat = float(latitude[i, j])
                        lon = float(longitude[i, j])
                        
                        if np.isnan(lat) or np.isnan(lon):
                            continue
                        
                        if o3_column is not None:
                            o3_val = float(o3_data[i, j])
                            quality_val = float(quality_data[i, j]) if quality_data.size > 0 else 1.0
                            
                            if np.isnan(o3_val) or o3_val < 0:
                                continue
                            
                            concentration = o3_val * CONVERSION_FACTOR
                            
                            measurements.append({
                                "latitude": round(lat, 6),
                                "longitude": round(lon, 6),
                                "timestamp": timestamp,
                                "pollutant": "O3",
                                "vertical_column_du": round(concentration, 4),  # Dobson Units
                                "unit": "DU",
                                "quality_flag": round(quality_val, 3)
                            })
            
            dataset.close()
            
            return {
                "metadata": {
                    "scan_time": timestamp,
                    "product": "O3",
                    "points_extracted": len(measurements),
                    "source_file": filepath.name
                },
                "measurements": measurements
            }
        
        except Exception as e:
            print(f"❌ Error procesando {filepath.name}: {e}")
            return None
    
    def process_aerosol_file(self, filepath):
        """
        Procesa archivo TEMPO de Aerosoles (proxy para PM)
        
        Args:
            filepath: Ruta al archivo .nc
        
        Returns:
            Diccionario con datos estructurados
        """
        print(f"📂 Procesando Aerosol: {filepath.name}")
        
        try:
            dataset = nc.Dataset(filepath, 'r')
            
            # Extraer Aerosol Optical Depth (AOD) como proxy de PM
            if 'product' in dataset.groups:
                product_group = dataset.groups['product']
                aod = product_group.variables.get('aerosol_optical_depth', None)
                quality_flag = product_group.variables.get('main_data_quality_flag', None)
            else:
                aod = dataset.variables.get('aerosol_optical_depth', 
                                            dataset.variables.get('AOD', None))
                quality_flag = dataset.variables.get('main_data_quality_flag', 
                                                     dataset.variables.get('quality_flag', None))
            
            # Coordenadas
            if 'geolocation' in dataset.groups:
                geo_group = dataset.groups['geolocation']
                latitude = geo_group.variables['latitude'][:]
                longitude = geo_group.variables['longitude'][:]
            else:
                latitude = dataset.variables['latitude'][:]
                longitude = dataset.variables['longitude'][:]
            
            timestamp = self.extract_timestamp(filepath.name)
            measurements = []
            
            aod_data = aod[:] if aod is not None else np.array([])
            quality_data = quality_flag[:] if quality_flag is not None else np.ones_like(aod_data)
            
            for i in range(latitude.shape[0]):
                for j in range(latitude.shape[1]):
                    lat = float(latitude[i, j])
                    lon = float(longitude[i, j])
                    
                    if np.isnan(lat) or np.isnan(lon):
                        continue
                    
                    if aod is not None:
                        aod_val = float(aod_data[i, j])
                        quality_val = float(quality_data[i, j]) if quality_data.size > 0 else 1.0
                        
                        if np.isnan(aod_val) or aod_val < 0:
                            continue
                        
                        measurements.append({
                            "latitude": round(lat, 6),
                            "longitude": round(lon, 6),
                            "timestamp": timestamp,
                            "pollutant": "AOD",
                            "concentration_ugm3": round(aod_val, 4),  # AOD es adimensional
                            "aqi": self.calculate_aqi(aod_val, 'AOD'),
                            "quality_flag": round(quality_val, 3)
                        })
            
            dataset.close()
            
            return {
                "metadata": {
                    "scan_time": timestamp,
                    "product": "Aerosol_Index",
                    "points_extracted": len(measurements),
                    "source_file": filepath.name
                },
                "measurements": measurements
            }
        
        except Exception as e:
            print(f"❌ Error procesando {filepath.name}: {e}")
            return None
    
    def process_all_files(self):
        """
        Procesa todos los archivos .nc en la carpeta de entrada
        """
        print("🚀 Iniciando procesamiento de archivos TEMPO...")
        print(f"📁 Carpeta de entrada: {self.input_folder.absolute()}")
        print(f"📁 Carpeta de salida: {self.output_folder.absolute()}\n")
        
        # Buscar archivos por tipo
        no2_files = list(self.input_folder.glob('TEMPO_NO2*.nc'))
        o3_files = list(self.input_folder.glob('TEMPO_O3*.nc'))
        aer_files = list(self.input_folder.glob('TEMPO_AER*.nc'))
        
        total_files = len(no2_files) + len(o3_files) + len(aer_files)
        
        if total_files == 0:
            print("⚠️  No se encontraron archivos .nc en la carpeta tempo_data/")
            print("   Asegúrate de colocar los archivos descargados en esa carpeta.")
            return
        
        print(f"✅ Encontrados {total_files} archivos:")
        print(f"   • NO2: {len(no2_files)}")
        print(f"   • O3: {len(o3_files)}")
        print(f"   • Aerosol: {len(aer_files)}\n")
        
        processed_count = 0
        
        # Procesar archivos NO2
        for filepath in no2_files:
            data = self.process_no2_file(filepath)
            if data and data['measurements']:
                output_file = self.output_folder / f"NO2_{filepath.stem}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"✅ Guardado: {output_file.name} ({len(data['measurements'])} puntos)\n")
                processed_count += 1
        
        # Procesar archivos O3
        for filepath in o3_files:
            data = self.process_o3_file(filepath)
            if data and data['measurements']:
                output_file = self.output_folder / f"O3_{filepath.stem}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"✅ Guardado: {output_file.name} ({len(data['measurements'])} puntos)\n")
                processed_count += 1
        
        # Procesar archivos Aerosol
        for filepath in aer_files:
            data = self.process_aerosol_file(filepath)
            if data and data['measurements']:
                output_file = self.output_folder / f"AEROSOL_{filepath.stem}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"✅ Guardado: {output_file.name} ({len(data['measurements'])} puntos)\n")
                processed_count += 1
        
        print(f"\n🎉 Procesamiento completado!")
        print(f"📊 Archivos procesados: {processed_count}/{total_files}")
        print(f"📁 JSONs guardados en: {self.output_folder.absolute()}")


def main():
    """Función principal"""
    processor = TEMPOProcessor(
        input_folder='tempo_data',
        output_folder='output'
    )
    processor.process_all_files()


if __name__ == '__main__':
    main()
