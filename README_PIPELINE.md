# TEMPO Data Pipeline - Sistema de Descarga y Procesamiento Automático

## 🎯 ¿Qué hace este sistema?

Este sistema descarga y procesa automáticamente datos de TEMPO (satélite de NASA) cada 3 horas.

### Flujo completo:
1. **Descarga** archivos más recientes de NO2 y O3 desde NASA Earthdata
2. **Extrae** datos de los archivos .nc (NetCDF)
3. **Convierte** columnas verticales a concentraciones superficiales
4. **Calcula** AQI (Air Quality Index)
5. **Divide** en chunks de ~50,000 puntos para Cloud
6. **Limpia** archivos .nc antiguos para ahorrar espacio

## 📋 Archivos del sistema

### Scripts principales:
- `descargar_tempo_v2.py` - Descarga archivos desde NASA CMR API
- `extraer_datos.py` - Extrae datos de archivos .nc
- `convertir_a_superficie.py` - Convierte a concentraciones + AQI
- `dividir_archivos.py` - Divide JSONs grandes en chunks
- `pipeline_completo.py` - Orquestador que ejecuta todo

### Scripts de utilidad:
- `mostrar_estadisticas.py` - Muestra stats de archivos procesados
- `verificar_setup.py` - Verifica instalación
- `inspeccionar_nc.py` - Inspecciona estructura de archivos .nc

### Configuración:
- `.env` - Credenciales de NASA Earthdata (PRIVADO)
- `configurar_tarea_automatica.ps1` - Crea tarea programada en Windows

## 🚀 Uso

### Ejecución manual (una vez):
```powershell
python pipeline_completo.py
```

### Automatización (cada 3 horas):
```powershell
# Ejecutar como Administrador
.\configurar_tarea_automatica.ps1
```

Esto creará una tarea en Windows Task Scheduler que ejecutará el pipeline automáticamente cada 3 horas.

### Comandos útiles:

```powershell
# Ver estado de la tarea
Get-ScheduledTask -TaskName "TEMPO_Data_Pipeline"

# Ejecutar ahora
Start-ScheduledTask -TaskName "TEMPO_Data_Pipeline"

# Deshabilitar temporalmente
Disable-ScheduledTask -TaskName "TEMPO_Data_Pipeline"

# Habilitar de nuevo
Enable-ScheduledTask -TaskName "TEMPO_Data_Pipeline"

# Eliminar tarea
Unregister-ScheduledTask -TaskName "TEMPO_Data_Pipeline" -Confirm:$false
```

## 📊 Salidas generadas

### Estructura de directorios:
```
TEMPO_Data/
├── tempo_data/          # Archivos .nc descargados (se eliminan automáticamente)
├── output/              # Archivos JSON procesados
│   ├── NO2_*.json      # Datos extraídos de NO2
│   ├── O3_*.json       # Datos extraídos de O3
│   ├── SURFACE_NO2_*.json  # NO2 con concentraciones superficiales + AQI
│   ├── SURFACE_O3_*.json   # O3 con concentraciones superficiales + AQI
│   └── chunks/         # Chunks divididos (~50K puntos cada uno)
│       ├── NO2_chunk_001.json
│       ├── NO2_chunk_002.json
│       ├── O3_chunk_001.json
│       └── ...
```

### Formato de datos:

**Archivos de extracción (NO2_*.json, O3_*.json):**
```json
{
  "metadata": {
    "source_file": "TEMPO_NO2_L2_V04_20251004T152407Z_S005G09.nc",
    "pollutant": "NO2",
    "processing_date": "2025-10-04T16:31:22"
  },
  "measurements": [
    {
      "latitude": 53.94,
      "longitude": -133.05,
      "vertical_column": 3.83e-01,
      "quality_flag": 1.0,
      "timestamp": "2025-10-04T15:24:07Z"
    }
  ]
}
```

**Archivos de superficie (SURFACE_*.json):**
```json
{
  "metadata": { ... },
  "measurements": [
    {
      "latitude": 53.94,
      "longitude": -133.05,
      "surface_concentration": 2.87,
      "unit": "µg/m³",
      "aqi": 2,
      "aqi_category": "Bueno",
      "quality_flag": 1.0,
      "timestamp": "2025-10-04T15:24:07Z"
    }
  ]
}
```

## ⚙️ Configuración

### Credenciales NASA Earthdata

Archivo `.env`:
```
EARTHDATA_USERNAME=tu_usuario
EARTHDATA_PASSWORD=tu_contraseña
```

**⚠️ IMPORTANTE:** Nunca compartas el archivo `.env` ni lo subas a GitHub.

### Obtener credenciales:
1. Crea cuenta en: https://urs.earthdata.nasa.gov/users/new
2. Confirma email
3. Usa username y password en `.env`

## 🔧 Requisitos

### Python 3.x con paquetes:
```bash
pip install netCDF4 numpy python-dotenv beautifulsoup4 requests
```

### Espacio en disco:
- Archivos .nc: ~200 MB cada 3 horas (se eliminan automáticamente)
- JSONs procesados: ~500 MB cada 3 horas (acumulativo)
- Chunks: ~14 MB por archivo

### Internet:
- Descargas de ~200-400 MB cada 3 horas
- Requiere conexión estable para autenticación NASA

## 📈 Datos generados

### NO2 (Dióxido de Nitrógeno):
- **Producto:** TEMPO_NO2_L2_V04
- **Frecuencia:** Cada hora (aprox.)
- **Puntos por archivo:** ~50,000 - 200,000
- **Quality flags:** Filtra automáticamente datos con quality_flag <= 0

### O3 (Ozono):
- **Producto:** TEMPO_O3TOT_L2_V04
- **Frecuencia:** Cada hora (aprox.)
- **Puntos por archivo:** ~50,000 - 3,500,000
- **Quality flags:** Filtra automáticamente datos con quality_flag <= 0

### Conversiones aplicadas:
- **NO2:** vertical_column × 0.75 ≈ superficie (µg/m³)
- **O3:** vertical_column (DU) × 0.04 ≈ troposférico (ppb)

### AQI Breakpoints:
- **NO2:** Basado en EPA (µg/m³)
- **O3:** Basado en EPA (ppb troposférico)

## 🐛 Solución de problemas

### "No se descargaron archivos nuevos"
- Verifica credenciales en `.env`
- Verifica conexión a internet
- NASA puede tener delay de 2-4 horas en publicar archivos

### "Error al extraer datos"
- Verifica que netCDF4 esté instalado: `pip show netCDF4`
- Archivo .nc puede estar corrupto, espera siguiente descarga

### "Tarea programada no se ejecuta"
- Verifica que Task Scheduler esté habilitado
- Verifica permisos de la tarea
- Revisa logs en Task Scheduler

### Calidad de datos
- Solo procesa datos con `quality_flag > 0`
- Si todos los datos tienen quality_flag = 0, espera siguiente archivo
- Días nublados tendrán menos datos disponibles

## 📞 Soporte

Para problemas con:
- **NASA Earthdata:** https://earthdata.nasa.gov/contact
- **TEMPO datos:** https://tempo.si.edu/
- **Credenciales:** https://urs.earthdata.nasa.gov/

## 📝 Licencia

Este proyecto es de uso personal. Los datos TEMPO son cortesía de NASA y están disponibles públicamente.

## 🙏 Créditos

- **Datos:** NASA TEMPO Mission
- **Distribución:** NASA Langley Atmospheric Science Data Center (LARC)
- **API:** NASA Common Metadata Repository (CMR)
