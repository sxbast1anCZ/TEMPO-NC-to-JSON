# 🛰️ TEMPO Air Quality Data Pipeline

Sistema automatizado para descargar y procesar datos de calidad del aire desde el satélite TEMPO de la NASA.

**¿Qué hace este programa?**
- 📥 Descarga automáticamente datos de NO2 (dióxido de nitrógeno) y O3 (ozono) desde la NASA
- 📊 Procesa los archivos y los convierte a formato JSON fácil de usar
- 🌡️ Calcula concentraciones superficiales y niveles de calidad del aire (AQI)
- 📦 Genera archivos listos para usar en tu aplicación web o móvil

> 🚀 **¿Primera vez usando el programa?** Lee la [**GUÍA DE INICIO RÁPIDO**](INICIO_RAPIDO.md) - 5 minutos paso a paso

---

## � GUÍA DE INSTALACIÓN RÁPIDA

### Paso 1️⃣: Instalar Python

**Si no tienes Python instalado:**

1. Ve a [python.org/downloads](https://www.python.org/downloads/)
2. Descarga **Python 3.13** (o superior)
3. **IMPORTANTE:** Durante la instalación, marca la casilla **"Add Python to PATH"**
4. Verifica la instalación:
   ```powershell
   python --version
   ```
   Debería mostrar algo como: `Python 3.13.0`

---

### Paso 2️⃣: Descargar el Proyecto

**Opción A - Con Git (Recomendado):**
```powershell
git clone https://github.com/sxbast1anCZ/TEMPO-NC-Files-to-JSON.git
cd TEMPO-NC-Files-to-JSON
```

**Opción B - Sin Git:**
1. Ve al repositorio en GitHub
2. Click en "Code" → "Download ZIP"
3. Descomprime el archivo
4. Abre PowerShell en esa carpeta

---

### Paso 3️⃣: Instalar Dependencias

Abre PowerShell en la carpeta del proyecto y ejecuta:

```powershell
pip install -r requirements.txt
```

Esto instalará automáticamente todo lo necesario. **Toma un café, tardará 2-3 minutos** ☕

---

### Paso 4️⃣: Crear Cuenta NASA (GRATIS)

El programa descarga datos desde la NASA, necesitas una cuenta gratuita:

1. Ve a [urs.earthdata.nasa.gov/users/new](https://urs.earthdata.nasa.gov/users/new)
2. Llena el formulario (es gratis, no pide tarjeta de crédito)
3. Verifica tu email
4. **Guarda tu usuario y contraseña** (los necesitarás en el siguiente paso)

---

### Paso 5️⃣: Configurar Credenciales

1. En la carpeta del proyecto, crea un archivo llamado **`.env`** (exactamente así, con el punto al inicio)
2. Ábrelo con el Bloc de notas o cualquier editor de texto
3. Copia esto y **reemplaza con tus datos**:

```env
EARTHDATA_USERNAME=tu_usuario_de_nasa
EARTHDATA_PASSWORD=tu_contraseña_de_nasa
```

**Ejemplo:**
```env
EARTHDATA_USERNAME=juan.perez
EARTHDATA_PASSWORD=MiPassword123
```

4. **IMPORTANTE:** Guarda el archivo y NO lo compartas con nadie

> � **Tip:** Si no ves la extensión `.env`, asegúrate de guardar como "Todos los archivos" en el Bloc de notas

---

### Paso 6️⃣: ¡Probar que Todo Funciona!

Ejecuta este comando para verificar la instalación:

```powershell
python verificar_flujo.py
```

**Si todo está bien, verás:**
```
✅ VERIFICACIÓN COMPLETA EXITOSA
🎯 El flujo de procesamiento está funcionando correctamente
```

**Si hay errores:**
- Revisa que instalaste Python correctamente (Paso 1)
- Verifica que el archivo `.env` tenga tus credenciales correctas (Paso 5)
- Asegúrate de estar en la carpeta correcta del proyecto

---

## 🎯 CÓMO USAR EL PROGRAMA

### Opción 1: Ejecutar Todo Automáticamente (MÁS FÁCIL) ⭐

Ejecuta este comando y déjalo trabajar:

```powershell
python pipeline_optimizado.py
```

**¿Qué hace?**
1. Descarga los archivos más recientes desde NASA (~240 MB)
2. Los procesa y convierte a JSON
3. Calcula concentraciones y calidad del aire
4. Divide en archivos pequeños para fácil manejo
5. Limpia archivos temporales

**Duración:** ~5 minutos  
**Frecuencia recomendada:** Cada 3 horas (puedes configurar ejecución automática abajo)

---

### Opción 2: Paso a Paso (Si quieres control manual)

```powershell
# 1. Descargar archivos desde NASA
python descargar_tempo_v2.py

# 2. Procesar archivos descargados
python extraer_datos.py

# 3. Convertir a concentraciones superficiales
python convertir_a_superficie.py

# 4. Dividir en archivos pequeños (opcional)
python dividir_archivos.py
```

---

### Opción 3: Verificar y Ver Estadísticas

```powershell
# Ver estadísticas de los datos procesados
python mostrar_estadisticas.py

# Verificar que todo funciona bien
python verificar_flujo.py
```

---

## 📁 ¿DÓNDE ESTÁN LOS ARCHIVOS GENERADOS?

Después de ejecutar el programa, encontrarás los archivos aquí:

```
TEMPO-NC-Files-to-JSON/
└── output/
    ├── SURFACE_NO2_*.json          ⭐ USAR ESTOS para NO2
    ├── SURFACE_O3_*.json           ⭐ USAR ESTOS para O3
    └── chunks/
        ├── SURFACE_NO2_*_chunk_001.json
        ├── SURFACE_NO2_*_chunk_002.json
        └── ... (archivos divididos)
```

**Archivos SURFACE_* son los que necesitas para tu aplicación.**  
Contienen las concentraciones en µg/m³ (NO2) y ppb (O3) listas para usar.

---

## 📊 FORMATO DE LOS DATOS

Los archivos JSON tienen esta estructura:

```json
{
  "metadata": {
    "scan_time": "2025-10-04T18:24:07Z",
    "product": "NO2",
    "points_extracted": 13358
  },
  "measurements": [
    {
      "latitude": 40.7128,
      "longitude": -74.0060,
      "timestamp": "2025-10-04T18:24:07Z",
      "pollutant": "NO2",
      "surface_concentration_ugm3": 45.32,
      "aqi": 92,
      "aqi_category": "Moderado",
      "quality_flag": 1.0
    }
  ]
}
```

**Campos importantes:**
- `latitude`, `longitude` - Ubicación del punto
- `surface_concentration_ugm3` - Concentración en µg/m³ (NO2)
- `tropospheric_concentration_ppb` - Concentración en ppb (O3)
- `aqi` - Índice de calidad del aire (0-500)
- `aqi_category` - Categoría: "Bueno", "Moderado", etc.

---

## ⏰ CONFIGURAR EJECUCIÓN AUTOMÁTICA (Opcional)

Para que el programa se ejecute solo cada 3 horas:

### En Windows:

1. **Abre PowerShell como Administrador** (click derecho → "Ejecutar como administrador")
2. Ejecuta:
   ```powershell
   .\configurar_tarea_automatica.ps1
   ```
3. Confirma cuando te lo pida
4. ¡Listo! El programa se ejecutará automáticamente cada 3 horas

### Verificar la tarea automática:

```powershell
# Ver estado de la tarea
Get-ScheduledTask -TaskName "TEMPO_Data_Pipeline"

# Ejecutar manualmente
Start-ScheduledTask -TaskName "TEMPO_Data_Pipeline"

# Desactivar
Disable-ScheduledTask -TaskName "TEMPO_Data_Pipeline"
```

---

## 🆘 SOLUCIÓN DE PROBLEMAS COMUNES

### ❌ Error: "python no se reconoce como comando"

**Solución:** Python no está en el PATH.
1. Desinstala Python
2. Vuélvelo a instalar marcando **"Add Python to PATH"**
3. Reinicia PowerShell

---

### ❌ Error: "Authentication failed"

**Solución:** Credenciales incorrectas.
1. Verifica que el archivo `.env` existe
2. Revisa que usuario y contraseña sean correctos
3. Inicia sesión en [urs.earthdata.nasa.gov](https://urs.earthdata.nasa.gov) para confirmar que funcionan

---

### ❌ Error: "No se encontraron archivos .nc"

**Solución:** No se descargaron archivos.
1. Verifica tu conexión a internet
2. Revisa las credenciales en `.env`
3. Ejecuta primero `python descargar_tempo_v2.py`

---

### ❌ Error: "ModuleNotFoundError: No module named 'netCDF4'"

**Solución:** Dependencias no instaladas.
```powershell
pip install -r requirements.txt
```

---

### 🆘 Ninguna solución funciona

Ejecuta el verificador del sistema:

```powershell
python verificar_sistema.py
```

Te dirá exactamente qué está fallando y cómo arreglarlo.

---

## 📚 DOCUMENTACIÓN ADICIONAL

Si quieres profundizar más:

- **`LIMPIEZA_COMPLETADA.md`** - Estructura del proyecto y archivos
- **`GUIA_GOOGLE_CLOUD.md`** - Cómo subir los datos a Google Cloud
- **`SCRIPTS.md`** - Descripción de cada script disponible

---

## 💡 CONSEJOS Y MEJORES PRÁCTICAS

### ✅ Recomendaciones:

1. **Ejecuta el pipeline cada 3 horas** para tener datos actualizados
2. **Usa los archivos SURFACE_*** - son los más fáciles de usar
3. **Revisa las estadísticas** con `python mostrar_estadisticas.py`
4. **Haz backup** de la carpeta `output/` periódicamente
5. **NO compartas** tu archivo `.env` con nadie

### 📊 Tamaño de Datos Esperado:

- **NO2:** ~15-60 MB por archivo (10,000-200,000 puntos)
- **O3:** ~1,000 MB por archivo (3,000,000+ puntos)
- **Chunks:** ~15-50 MB cada uno (más fáciles de manejar)

### ⏱️ Tiempos de Ejecución:

- Descarga: ~2 minutos
- Procesamiento: ~2 minutos
- Total: ~5 minutos por ejecución

---

## 🎯 SIGUIENTES PASOS

**Una vez que tengas los datos:**

1. **Para aplicación web:** Lee los archivos SURFACE_*.json directamente
2. **Para aplicación móvil:** Usa los chunks para cargar datos por partes
3. **Para análisis:** Importa los JSON en pandas, Excel, o tu herramienta favorita
4. **Para API REST:** Sube a Google Cloud y crea endpoints (ver `GUIA_GOOGLE_CLOUD.md`)

---

## 🤝 CRÉDITOS Y AGRADECIMIENTOS

- **Datos:** NASA TEMPO Mission ([tempo.si.edu](https://tempo.si.edu))
- **API:** NASA Common Metadata Repository (CMR)
- **Proyecto:** Desarrollado por Sebastian
- **Versión de datos:** V04 (última versión estable, octubre 2025)

---

## 📞 SOPORTE

**¿Tienes problemas?**

1. Ejecuta `python verificar_sistema.py` primero
2. Revisa la sección "Solución de Problemas" arriba
3. Contacta al desarrollador del proyecto

---

**Última actualización:** 4 de octubre de 2025  
**Versión:** 2.0 (Optimizada con Datacenter Features)


