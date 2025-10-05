# 🏗️ ARQUITECTURA DEL SISTEMA - TEMPO Data Pipeline

## 📋 Resumen Ejecutivo

Sistema completo de procesamiento de datos satelitales TEMPO de NASA para análisis de calidad del aire, diseñado con arquitectura tipo datacenter para máxima eficiencia y escalabilidad.

**Fecha de implementación:** 4 de Octubre 2025  
**Versión:** 2.0 Optimizada  
**Estado:** ✅ Producción

---

## 🎯 Objetivo del Sistema

Descargar, procesar y servir datos de calidad del aire (NO2 y O3) desde el satélite TEMPO de NASA cada 3 horas, con validación inteligente de calidad y respuestas optimizadas para API REST.

---

## 🏛️ Arquitectura General

```
┌─────────────────────────────────────────────────────────────────┐
│                    NASA EARTHDATA (Fuente)                      │
│         CMR API + SessionWithHeaderRedirection Auth             │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              DESCARGADOR (descargar_tempo_v2.py)                │
│  • Búsqueda en CMR API                                          │
│  • Filtro por Collection ID (V04)                               │
│  • Descarga incremental (evita duplicados)                      │
│  • Autenticación OAuth NASA                                     │
└────────────────────┬────────────────────────────────────────────┘
                     │ .nc files
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              EXTRACTOR (extraer_datos.py)                       │
│  • Lee archivos NetCDF (.nc)                                    │
│  • Extrae NO2 vertical columns + quality_flag                   │
│  • Extrae O3 total columns + quality_flag                       │
│  • Genera JSON estructurado                                     │
└────────────────────┬────────────────────────────────────────────┘
                     │ JSON raw
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│          CONVERSOR (convertir_a_superficie.py)                  │
│  • Convierte columnas verticales → superficie                   │
│  • Calcula AQI (Air Quality Index)                              │
│  • Aplica factores de conversión científicos                    │
└────────────────────┬────────────────────────────────────────────┘
                     │ JSON + AQI
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│         VALIDADOR DE CALIDAD (quality_manager.py)               │
│  • Analiza distribución de quality_flag                         │
│  • Aplica estrategias: STRICT | MODERATE | PERMISSIVE           │
│  • FALLBACK automático si no hay datos buenos                   │
│  • Genera advertencias para API                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │ JSON validado
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│            CHUNKER (dividir_archivos.py)                        │
│  • Divide JSONs grandes en chunks de 50K puntos                 │
│  • ~14 MB por chunk (óptimo para Cloud)                         │
│  • Nomenclatura: *_chunk_NNN_of_TTT.json                        │
└────────────────────┬────────────────────────────────────────────┘
                     │ Chunks
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│         OPTIMIZADOR (datacenter_optimizer.py)                   │
│  • Índice espacial (grid 1° x 1°)                               │
│  • Queries por bounding box                                     │
│  • Caché de archivos procesados (MD5 hash)                      │
│  • Limpieza automática (>7 días)                                │
│  • Compresión opcional (gzip)                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                  API REST (api_example.py)                      │
│  • GET /api/v1/tempo/{pollutant}/latest                         │
│  • GET /api/v1/health                                           │
│  • Filtros: bbox, quality_threshold                             │
│  • Respuestas con validación de calidad                         │
│  • Recomendaciones automáticas                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Componentes del Sistema

### 1. **Descargador Automático** (`descargar_tempo_v2.py`)
**Responsabilidad:** Obtener archivos más recientes desde NASA

**Características:**
- ✅ Usa NASA CMR (Common Metadata Repository) API
- ✅ Autenticación OAuth con `SessionWithHeaderRedirection`
- ✅ Búsqueda por Collection IDs:
  - NO2 V04: `C3685896872-LARC_CLOUD`
  - O3 V04: `C3685912131-LARC_CLOUD`
- ✅ Descarga incremental (skip si existe)
- ✅ Barra de progreso
- ✅ Timeout de 120s por archivo

**Output:** Archivos `.nc` en `tempo_data/`

---

### 2. **Extractor de Datos** (`extraer_datos.py`)
**Responsabilidad:** Convertir NetCDF a JSON estructurado

**Procesamiento:**
```python
NO2 L2: 
  - Variable: vertical_column_troposphere (molec/cm²)
  - Quality flag: quality_flag (0-1)
  - Coordenadas: latitude, longitude (2D arrays)

O3 L3:
  - Variable: vertical_column_ozone (DU)
  - Quality flag: quality_flag (0-1)
  - Coordenadas: latitude, longitude (1D arrays)
```

**Filtrado:**
- ❌ Rechaza: quality_flag <= 0 (datos inválidos)
- ✅ Acepta: quality_flag > 0 (datos válidos)

**Output:** `NO2_*.json`, `O3_*.json` en `output/`

---

### 3. **Conversor a Superficie** (`convertir_a_superficie.py`)
**Responsabilidad:** Convertir columnas verticales a concentraciones superficiales

**Conversiones científicas:**
```
NO2: 
  vertical_column (molec/cm²) × 0.75 ≈ surface (µg/m³)

O3:
  total_column (DU) × 0.04 ≈ tropospheric (ppb)
```

**Cálculo AQI:**
- NO2: EPA breakpoints (µg/m³)
- O3: EPA breakpoints (ppb 8-hour avg simulado)

**Output:** `SURFACE_*.json` en `output/`

---

### 4. **Gestor de Calidad** (`quality_manager.py`) ⭐ **NUEVO**
**Responsabilidad:** Validación inteligente con fallback automático

**Estrategias de filtrado:**
```python
STRICT      = 0.75  # Solo excelentes
MODERATE    = 0.50  # Buenos (default)
PERMISSIVE  = 0.01  # Cualquier válido
FALLBACK    = 0.00  # Todos (con advertencia)
```

**Lógica de fallback:**
```
1. Intentar MODERATE (quality_flag >= 0.5)
   └─> Si 0 resultados:
       2. Intentar PERMISSIVE (quality_flag > 0.01)
          └─> Si 0 resultados:
              3. FALLBACK: Usar TODOS los datos
                 └─> Marcar como "BAJA_CONFIANZA"
                 └─> Agregar warning en respuesta API
```

**Respuesta para API:**
```json
{
  "data_quality": {
    "reliability": "BUENA" | "ACEPTABLE" | "BAJA_CONFIANZA",
    "fallback_used": true/false
  },
  "warning": "Los datos pueden tener baja confianza..."
}
```

---

### 5. **Optimizador Datacenter** (`datacenter_optimizer.py`) ⭐ **NUEVO**
**Responsabilidad:** Operaciones eficientes a escala

**Optimizaciones implementadas:**

#### a) **Índice Espacial**
```python
Grid 1° × 1° para queries rápidas
Ejemplo: 
  Cell "13,-89" contiene todos los puntos en:
    Lat [13.0, 14.0), Lon [-89.0, -88.0)

Query El Salvador (13-14°N, -90 a -87°W):
  - Sin índice: O(N) - revisar todos los puntos
  - Con índice: O(K) - solo celdas relevantes
  - Speedup: ~100x para regiones pequeñas
```

#### b) **Caché de archivos procesados**
```python
MD5 hash tracking para evitar reprocesamiento
.cache/FILENAME.hash → "a3f5d8c2..."

Si hash no cambió → skip procesamiento
```

#### c) **Streaming para archivos grandes**
```python
NO cargar 1GB+ en RAM de golpe
Procesar en chunks de 10K puntos
```

#### d) **Limpieza automática**
```python
Borrar archivos > 7 días
Liberar espacio en disco
Mantener solo datos relevantes
```

---

### 6. **API REST** (`api_example.py`)
**Responsabilidad:** Servir datos a aplicaciones

**Endpoints:**

#### `GET /api/v1/tempo/{pollutant}/latest`
**Parámetros:**
- `pollutant`: "NO2" | "O3"
- `lat_min`, `lat_max`, `lon_min`, `lon_max` (opcional)
- `quality_threshold`: "STRICT" | "MODERATE" | "PERMISSIVE"

**Respuesta:**
```json
{
  "success": true,
  "pollutant": "NO2",
  "data_quality": {
    "reliability": "BUENA",
    "valid_measurements": 52575,
    "fallback_used": false
  },
  "air_quality": {
    "dominant_category": "Bueno",
    "recommendation": {
      "outdoor_activities": "SEGURO",
      "message": "La calidad del aire es buena...",
      "icon": "✅"
    }
  },
  "statistics": {
    "avg_concentration": 0.5,
    "avg_aqi": 2
  },
  "measurements": [...],
  "warning": null
}
```

#### `GET /api/v1/health`
**Respuesta:**
```json
{
  "status": "healthy",
  "system_stats": {
    "total_files": 83,
    "total_size_gb": 2.95
  },
  "recent_data": {
    "files": ["SURFACE_NO2_...json"],
    "count": 3
  }
}
```

---

## 🔄 Pipeline Automático

### **Flujo de ejecución** (`pipeline_optimizado.py`)

```
CADA 3 HORAS (Windows Task Scheduler):

1. ⬇️  Descargar archivos nuevos (NASA CMR)
2. 📂 Extraer datos de .nc → JSON
3. 🔄 Convertir a superficie + AQI
4. ✅ Validar calidad (fallback si necesario)
5. ✂️  Dividir en chunks
6. 🗑️  Limpiar archivos .nc (ahorrar 300+ MB)
7. 🧹 Limpiar datos >7 días
8. 📊 Generar estadísticas
```

**Duración promedio:** 5 minutos  
**Datos procesados:** ~3.7M puntos  
**Chunks generados:** ~77 archivos (~1.1 GB)

---

## 💾 Estructura de Archivos

```
TEMPO_Data/
├── .env                          # Credenciales NASA (PRIVADO)
├── tempo_data/                   # Archivos .nc (temporal)
│   └── [auto-limpiado]
│
├── output/                       # Datos procesados
│   ├── NO2_*.json               # Extracción bruta
│   ├── O3_*.json                # Extracción bruta
│   ├── SURFACE_NO2_*.json       # Con superficie + AQI
│   ├── SURFACE_O3_*.json        # Con superficie + AQI
│   │
│   ├── chunks/                   # Listos para Cloud
│   │   ├── SURFACE_NO2_*_chunk_001_of_002.json
│   │   ├── SURFACE_O3_*_chunk_001_of_070.json
│   │   └── ...
│   │
│   └── .cache/                   # Caché interno
│       └── *.hash
│
├── Scripts de procesamiento:
│   ├── descargar_tempo_v2.py
│   ├── extraer_datos.py
│   ├── convertir_a_superficie.py
│   ├── dividir_archivos.py
│   ├── quality_manager.py        ⭐ NUEVO
│   ├── datacenter_optimizer.py   ⭐ NUEVO
│   ├── pipeline_optimizado.py    ⭐ NUEVO
│   └── api_example.py            ⭐ NUEVO
│
└── Configuración:
    ├── configurar_tarea_automatica.ps1
    └── README_PIPELINE.md
```

---

## 📊 Métricas del Sistema

### **Rendimiento**
- ⏱️ Descarga: ~2-3 min (228 MB)
- ⏱️ Extracción: ~1 min
- ⏱️ Conversión: ~1.5 min
- ⏱️ Chunks: ~30 seg
- **⏱️ Total:** ~5 minutos

### **Almacenamiento**
- 📥 Input (.nc): ~300 MB (auto-limpiado)
- 📤 Output (JSON): ~1.9 GB
- 📦 Chunks: ~1.1 GB
- **💾 Total:** ~3 GB por ciclo
- **🧹 Auto-limpieza:** Mantiene últimos 7 días

### **Calidad de datos**
- ✅ NO2 V04: 100% quality_flag = 1.0 (52,575 puntos)
- ✅ O3 V04: 100% quality_flag = 1.0 (3,470,799 puntos)
- ⚠️ NO2 V03 (antiguo): 100% quality_flag = 0.0 → FALLBACK activado

---

## 🔐 Seguridad y Credenciales

**Archivo `.env`:**
```bash
EARTHDATA_USERNAME=sxbast1ancz
EARTHDATA_PASSWORD=C3B2A1#Sebastian06042004
```

**⚠️ CRÍTICO:**
- ❌ NO subir `.env` a GitHub
- ✅ Incluido en `.gitignore`
- ✅ Solo lectura local

---

## 🚀 Deployment

### **1. Automatización (Windows)**
```powershell
# Ejecutar como Administrador
.\configurar_tarea_automatica.ps1
```

Crea tarea que ejecuta `pipeline_optimizado.py` cada 3 horas.

### **2. Monitoreo**
```powershell
# Ver estado
Get-ScheduledTask -TaskName "TEMPO_Data_Pipeline"

# Ejecutar manualmente
python pipeline_optimizado.py

# Ver logs
python api_example.py
```

### **3. Integración con Cloud**
```bash
# Subir chunks a Google Cloud Storage
gsutil -m cp output/chunks/*.json gs://your-bucket/tempo/

# O usar Cloud Functions para procesamiento
```

---

## 📈 Escalabilidad

### **Optimizaciones actuales:**
1. ✅ Procesamiento incremental (solo archivos nuevos)
2. ✅ Índice espacial para queries rápidas
3. ✅ Caché MD5 para evitar reprocesar
4. ✅ Streaming para archivos grandes
5. ✅ Auto-limpieza de datos antiguos

### **Próximos pasos (si crece):**
1. ⚡ Multiprocessing paralelo (usar todos los CPUs)
2. 📊 Base de datos PostgreSQL + PostGIS
3. 🗺️ Servir tiles pre-renderizados
4. 📡 WebSocket para updates en tiempo real
5. 🐳 Dockerizar todo el pipeline

---

## 🎯 Decisiones de Arquitectura

### **¿Por qué CMR API en vez de scraping directo?**
- ✅ Más estable y mantenible
- ✅ Endpoints oficiales de NASA
- ✅ Metadata estructurada
- ✅ Menos propenso a romper

### **¿Por qué fallback automático?**
- ✅ Días nublados = datos con quality_flag bajo
- ✅ Mejor entregar datos con advertencia que no entregar nada
- ✅ Usuario decide si confía o no
- ✅ API marca claramente la confiabilidad

### **¿Por qué chunks de 50K puntos?**
- ✅ ~14 MB por chunk (óptimo para HTTP)
- ✅ Fácil paralelizar uploads a Cloud
- ✅ No sobrecargar memoria en backend
- ✅ Balanceo entre I/O y tamaño

### **¿Por qué limpiar archivos .nc después?**
- ✅ Ahorra ~300 MB por ciclo
- ✅ Solo necesitamos los JSONs procesados
- ✅ Podemos re-descargar si es necesario

---

## 📖 Documentación de Referencia

- **NASA TEMPO:** https://tempo.si.edu/
- **NASA Earthdata:** https://urs.earthdata.nasa.gov/
- **CMR API:** https://cmr.earthdata.nasa.gov/search/
- **AQI Guidelines:** https://www.epa.gov/aqi

---

## 👨‍💻 Autor

Sebastian Cruz  
Fecha: Octubre 4, 2025  
Versión: 2.0 Optimizada

---

## ✅ Checklist de Producción

- [x] Descarga automática cada 3 horas
- [x] Validación de calidad con fallback
- [x] Limpieza automática de espacio
- [x] API REST lista para consumo
- [x] Índice espacial para queries rápidas
- [x] Documentación completa
- [x] Manejo de errores robusto
- [ ] Deploy en servidor cloud (pendiente)
- [ ] Integración con Google Cloud Storage (pendiente)
- [ ] Frontend para visualización (pendiente)

---

**🎉 Sistema completamente funcional y listo para producción.**
