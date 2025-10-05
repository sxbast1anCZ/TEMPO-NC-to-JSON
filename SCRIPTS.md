# 📜 Descripción de Scripts

## 🚀 Scripts Principales

### `pipeline_optimizado.py`
**Propósito:** Orquestador principal del sistema completo.

Ejecuta secuencialmente:
1. Descarga últimos archivos TEMPO desde NASA
2. Extrae datos con filtro de calidad
3. Convierte a unidades de superficie
4. Valida calidad con estrategia inteligente
5. Divide en chunks optimizados
6. Limpia archivos antiguos

**Uso:** `python pipeline_optimizado.py`

**Duración:** ~5 minutos

---

### `descargar_tempo_v2.py`
**Propósito:** Descarga automática desde NASA CMR API.

**Características:**
- Busca últimos granules de NO2 y O3 (V04)
- Autenticación OAuth con NASA Earthdata
- Barra de progreso de descarga
- Guarda archivos .nc en `tempo_data/`

**Uso:** `python descargar_tempo_v2.py`

**Credenciales:** Requiere `.env` con NASA_USERNAME y NASA_PASSWORD

---

### `extraer_datos.py`
**Propósito:** Extrae datos de archivos .nc a JSON.

**Características:**
- Lee archivos NetCDF4 de TEMPO
- Filtra por `quality_flag > 0`
- Detecta automáticamente tipo de contaminante (NO2/O3)
- Guarda en `output/extracted/`

**Uso:** `python extraer_datos.py`

---

### `convertir_a_superficie.py`
**Propósito:** Convierte columnas verticales a concentraciones de superficie.

**Características:**
- NO2: `vertical_column × 0.75` → µg/m³
- O3: `total_column × 0.04` → ppb troposférico
- Preserva metadata y calidad
- Guarda en `output/surface/`

**Uso:** `python convertir_a_superficie.py`

---

### `dividir_archivos.py`
**Propósito:** Divide JSONs grandes en chunks manejables.

**Características:**
- Tamaño objetivo: 15-20 MB por chunk
- Preserva metadata en cada chunk
- Añade información de paginación
- Guarda en `output/chunks/`

**Uso:** `python dividir_archivos.py`

---

## 🎯 Módulos de Gestión

### `quality_manager.py`
**Propósito:** Validación inteligente de calidad de datos.

**Características:**
- Estrategias de calidad: STRICT, MODERATE, PERMISSIVE, FALLBACK
- Degradación automática si no hay datos suficientes
- Calcula estadísticas de calidad
- Retorna confiabilidad para API

**Funciones principales:**
- `filter_by_quality(data, strategy)` - Filtra por umbral de calidad
- `validate_quality_and_fallback(data)` - Aplica estrategia con fallback
- `get_api_response(data)` - Formatea respuesta para REST API

---

### `datacenter_optimizer.py`
**Propósito:** Optimizaciones a nivel datacenter.

**Características:**
- **Índice espacial:** Grid 1°×1° para consultas O(K) vs O(N)
- **Cache MD5:** Previene reprocesamiento de archivos duplicados
- **Streaming:** Procesamiento por chunks sin cargar todo en RAM
- **Auto-limpieza:** Borra archivos >7 días y .nc temporales

**Funciones principales:**
- `build_spatial_index(data)` - Construye grid de localización
- `query_by_bbox(index, lat_min, lat_max, lon_min, lon_max)` - Query regional rápido
- `clean_old_files(days=7)` - Limpieza automática

---

## 🔧 Utilidades

### `verificar_sistema.py`
**Propósito:** Diagnóstico completo del sistema.

**Verifica:**
- ✅ Estructura de directorios
- ✅ Scripts principales
- ✅ Archivos generados recientes (<6 horas)
- ✅ Dependencias Python instaladas
- ✅ API funcional

**Uso:** `python verificar_sistema.py`

---

### `mostrar_estadisticas.py`
**Propósito:** Muestra estadísticas de archivos procesados.

**Características:**
- Detecta automáticamente tipo de contaminante
- Calcula mean, median, min, max, std
- Muestra distribución de quality_flags
- Análisis por región

**Uso:** `python mostrar_estadisticas.py`

---

### `configurar_tarea.ps1`
**Propósito:** Configura Windows Task Scheduler.

**Características:**
- Crea tarea "TEMPO_Data_Pipeline"
- Ejecución cada 3 horas
- Timeout de 1 hora
- Funciona con batería y requiere red

**Uso:** `powershell -ExecutionPolicy Bypass -File configurar_tarea.ps1`

---

### `api_example.py`
**Propósito:** Ejemplo de endpoints REST API.

**Endpoints de ejemplo:**
- `GET /latest` - Últimos datos procesados
- `GET /location?lat=X&lon=Y&radius=Z` - Datos por ubicación
- `GET /health` - Health check

**Uso:** `python api_example.py`

---

## 📊 Scripts de Análisis (Deprecated)

### `convertir_a_geojson.py`
Convierte JSONs a formato GeoJSON para visualización en mapas.

### `generar_mapas.py`
Genera mapas HTML interactivos con Folium.

---

## 🔄 Flujo de Ejecución Recomendado

```
pipeline_optimizado.py
├─> descargar_tempo_v2.py
├─> extraer_datos.py
├─> convertir_a_superficie.py
├─> quality_manager.py (validación)
├─> dividir_archivos.py
└─> datacenter_optimizer.py (limpieza)
```

**Resultado:** 77 chunks JSON listos para cloud (~1.1 GB)

---

## 🌐 Próximos Pasos

Para integración con Google Cloud y NestJS, consulta:
- [`GUIA_GOOGLE_CLOUD_NESTJS.md`](GUIA_GOOGLE_CLOUD_NESTJS.md)

Para arquitectura completa:
- [`ARQUITECTURA.md`](ARQUITECTURA.md)
- [`RESUMEN_EJECUTIVO.md`](RESUMEN_EJECUTIVO.md)
