# ⚡ GUÍA DE INICIO RÁPIDO - 5 MINUTOS

**Para tu amigo que quiere usar el programa por primera vez**

---

## 📝 CHECKLIST DE INSTALACIÓN

Sigue estos pasos en orden:

- [ ] **1. Instalar Python 3.13**
- [ ] **2. Descargar el proyecto**
- [ ] **3. Instalar dependencias**
- [ ] **4. Crear cuenta NASA (gratis)**
- [ ] **5. Configurar credenciales**
- [ ] **6. Probar que funciona**

---

## 🚀 PASO A PASO DETALLADO

### 1️⃣ Instalar Python (5 minutos)

**Windows:**
1. Ve a [python.org/downloads](https://www.python.org/downloads/)
2. Descarga **Python 3.13** (botón amarillo grande)
3. Ejecuta el instalador
4. **⚠️ MUY IMPORTANTE:** Marca la casilla **"Add Python to PATH"** antes de instalar
5. Click en "Install Now"
6. Espera a que termine

**Verificar:**
```powershell
python --version
```
Debería mostrar: `Python 3.13.x`

---

### 2️⃣ Descargar el Proyecto (2 minutos)

**Si tienes Git:**
```powershell
cd Desktop
git clone https://github.com/sxbast1anCZ/TEMPO-NC-Files-to-JSON.git
cd TEMPO-NC-Files-to-JSON
```

**Si NO tienes Git:**
1. Ve a: https://github.com/sxbast1anCZ/TEMPO-NC-Files-to-JSON
2. Click en el botón verde **"Code"**
3. Click en **"Download ZIP"**
4. Descomprime el archivo en una carpeta (ej: `Desktop/TEMPO-NC-Files-to-JSON`)
5. Abre PowerShell en esa carpeta:
   - Click derecho en la carpeta
   - "Abrir en Terminal" o "Abrir ventana de PowerShell aquí"

---

### 3️⃣ Instalar Dependencias (3 minutos)

En PowerShell, en la carpeta del proyecto:

```powershell
pip install -r requirements.txt
```

**Esto instalará:**
- netCDF4 (leer archivos satelitales)
- numpy (cálculos numéricos)
- requests (descargar de internet)
- beautifulsoup4 (procesar HTML)
- python-dotenv (leer configuración)

⏳ **Espera 2-3 minutos mientras se instala todo**

---

### 4️⃣ Crear Cuenta NASA - GRATIS (5 minutos)

1. Ve a: [urs.earthdata.nasa.gov/users/new](https://urs.earthdata.nasa.gov/users/new)
2. Llena el formulario:
   - Username: elige un nombre de usuario
   - Email: tu email
   - Password: crea una contraseña segura
   - Datos personales básicos
3. Click en **"Register for Earthdata Login"**
4. **Revisa tu email** y confirma la cuenta
5. **Guarda tus credenciales** (las necesitas en el siguiente paso)

📝 **Anota:**
- Username: _______________
- Password: _______________

---

### 5️⃣ Configurar Credenciales (1 minuto)

1. En la carpeta del proyecto, crea un archivo llamado **`.env`**
   
   **¿Cómo crear el archivo?**
   - Opción A: Haz click derecho → Nuevo → Documento de texto
   - Renómbralo a `.env` (sin extensión .txt)
   
   **O en PowerShell:**
   ```powershell
   New-Item -Path .env -ItemType File
   ```

2. Abre el archivo `.env` con Bloc de notas

3. Copia esto y **cambia con TUS datos**:
   ```env
   EARTHDATA_USERNAME=tu_usuario_aqui
   EARTHDATA_PASSWORD=tu_contraseña_aqui
   ```

4. **Ejemplo real:**
   ```env
   EARTHDATA_USERNAME=juan.perez
   EARTHDATA_PASSWORD=MiPassword2024!
   ```

5. Guarda el archivo (Ctrl+S)

⚠️ **IMPORTANTE:**
- NO uses espacios antes o después del `=`
- NO pongas comillas en el usuario o contraseña
- NO compartas este archivo con nadie

---

### 6️⃣ Probar que Funciona (1 minuto)

Ejecuta el verificador:

```powershell
python verificar_flujo.py
```

**✅ Si TODO está bien, verás:**
```
======================================================================
✅ VERIFICACIÓN COMPLETA EXITOSA
======================================================================

🎯 El flujo de procesamiento está funcionando correctamente:
   • Archivos SURFACE_* generados ✅
   • Estructura JSON válida ✅
   • Datos listos para API REST ✅
```

**❌ Si hay errores:**

| Error | Solución |
|-------|----------|
| `python no se reconoce` | Python no está en PATH. Reinstala Python marcando "Add to PATH" |
| `No module named 'netCDF4'` | Ejecuta: `pip install -r requirements.txt` |
| `FileNotFoundError: .env` | Crea el archivo `.env` en la carpeta del proyecto |

---

## 🎉 ¡LISTO! Ahora puedes usar el programa

### Primera Ejecución - Descargar y Procesar Datos

```powershell
python pipeline_optimizado.py
```

**Esto va a:**
1. 📥 Descargar ~240 MB de NASA (2 archivos: NO2 y O3)
2. 📊 Procesarlos y convertirlos a JSON
3. 🌡️ Calcular concentraciones y calidad del aire
4. 📦 Dividirlos en archivos pequeños
5. 🧹 Limpiar archivos temporales

⏱️ **Duración:** ~5 minutos

---

## 📁 ¿DÓNDE ESTÁN MIS ARCHIVOS?

Después de ejecutar el programa:

```
TEMPO-NC-Files-to-JSON/
└── output/
    ├── SURFACE_NO2_*.json          ⭐ USAR ESTE para NO2
    ├── SURFACE_O3_*.json           ⭐ USAR ESTE para O3
    └── chunks/                     📦 Archivos divididos
```

**Los archivos SURFACE_* son los importantes.**  
Tienen las concentraciones listas para usar en tu app.

---

## 🔄 EJECUTAR CADA VEZ QUE QUIERAS DATOS NUEVOS

```powershell
python pipeline_optimizado.py
```

**Frecuencia recomendada:** Cada 3 horas  
**Por qué:** La NASA actualiza los datos cada hora, pero procesar todo toma tiempo

---

## 🆘 PROBLEMAS COMUNES

### "No se encontraron archivos .nc"

**Causa:** No se descargaron archivos  
**Solución:**
1. Verifica tu internet
2. Revisa credenciales en `.env`
3. Intenta de nuevo

---

### "Authentication failed"

**Causa:** Usuario o contraseña incorrectos  
**Solución:**
1. Abre el archivo `.env`
2. Verifica que usuario y contraseña sean correctos
3. Prueba iniciar sesión en [urs.earthdata.nasa.gov](https://urs.earthdata.nasa.gov)

---

### El programa se detiene o congela

**Solución:**
1. Cierra la ventana de PowerShell
2. Abre una nueva
3. Vuelve a ejecutar el comando

---

## 💡 CONSEJOS PARA TU AMIGO

### ✅ HACER:

- ✅ Ejecutar el programa cada 3-4 horas si quieres datos frescos
- ✅ Guardar los archivos SURFACE_* en un lugar seguro
- ✅ Hacer backup de la carpeta `output/` si es importante
- ✅ Revisar las estadísticas con `python mostrar_estadisticas.py`

### ❌ NO HACER:

- ❌ NO borrar la carpeta `output/` (tiene los datos procesados)
- ❌ NO compartir el archivo `.env` (tiene tu contraseña)
- ❌ NO ejecutar el programa 100 veces seguidas (respeta la API de NASA)
- ❌ NO modificar archivos del programa sin saber qué hacen

---

## 📞 ¿NECESITAS AYUDA?

1. **Primero:** Ejecuta `python verificar_sistema.py` para ver qué falla
2. **Segundo:** Revisa esta guía de nuevo
3. **Tercero:** Contacta al desarrollador (Sebastian)

---

## 🎯 SIGUIENTE NIVEL

Una vez que tengas datos procesados:

1. **Ver estadísticas:**
   ```powershell
   python mostrar_estadisticas.py
   ```

2. **Configurar ejecución automática cada 3 horas:**
   ```powershell
   # Ejecutar como Administrador
   .\configurar_tarea_automatica.ps1
   ```

3. **Subir a Google Cloud** (opcional):
   - Lee `GUIA_GOOGLE_CLOUD.md` para instrucciones

---

**¡Éxito! 🚀**

Si llegaste hasta aquí, ya tienes todo funcionando.  
Ahora puedes usar los datos de calidad del aire en tu proyecto.

---

**Creado:** 4 de octubre de 2025  
**Autor:** Sebastian  
**Versión:** 1.0 - Guía para principiantes
