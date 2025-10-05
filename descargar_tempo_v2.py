"""
Script para descargar automáticamente los archivos más recientes de TEMPO
usando NASA CMR API + Earthdata autenticación.

Descarga:
- NO2 L2 V04 (Tropospheric Vertical Column)
- O3 Total Column L3 V04

Autor: Sebastian
Fecha: Octubre 2025
"""

import os
import requests
from datetime import datetime, timedelta
from pathlib import Path
import json
from dotenv import load_dotenv

# Cargar credenciales
load_dotenv()
USERNAME = os.getenv('EARTHDATA_USERNAME')
PASSWORD = os.getenv('EARTHDATA_PASSWORD')

# Configuración
CMR_SEARCH_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"
DOWNLOAD_DIR = Path('tempo_data')

# Collection IDs actualizados (V04 - más recientes)
COLLECTION_IDS = {
    'NO2': 'C3685896872-LARC_CLOUD',    # TEMPO NO2 V04
    'O3': 'C3685912131-LARC_CLOUD'      # TEMPO O3 Total Column V04
}

class SessionWithHeaderRedirection(requests.Session):
    """
    Session para autenticación NASA Earthdata
    """
    AUTH_HOST = 'urs.earthdata.nasa.gov'
    
    def __init__(self, username, password):
        super().__init__()
        self.auth = (username, password)
    
    def rebuild_auth(self, prepared_request, response):
        headers = prepared_request.headers
        url = prepared_request.url
        
        if 'Authorization' in headers:
            original_parsed = requests.utils.urlparse(response.request.url)
            redirect_parsed = requests.utils.urlparse(url)
            
            if (original_parsed.hostname != redirect_parsed.hostname) and \
                    redirect_parsed.hostname != self.AUTH_HOST and \
                    original_parsed.hostname != self.AUTH_HOST:
                del headers['Authorization']
        return

class TempoDownloader:
    """Descargador de archivos TEMPO desde NASA"""
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = SessionWithHeaderRedirection(username, password)
    
    def search_granules(self, product, days_back=7):
        """Busca archivos (granules) en CMR"""
        
        if product not in COLLECTION_IDS:
            print(f"❌ Producto desconocido: {product}")
            return []
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            'collection_concept_id': COLLECTION_IDS[product],
            'temporal': f"{start_date.strftime('%Y-%m-%dT00:00:00Z')},{end_date.strftime('%Y-%m-%dT23:59:59Z')}",
            'sort_key': '-start_date',  # Más recientes primero
            'page_size': 200
        }
        
        print(f"🔍 Buscando archivos de {product} (últimos {days_back} días)...")
        
        try:
            response = requests.get(CMR_SEARCH_URL, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ Error CMR: HTTP {response.status_code}")
                return []
            
            data = response.json()
            entries = data.get('feed', {}).get('entry', [])
            
            print(f"📋 Encontrados: {len(entries)} archivos")
            
            granules = []
            for entry in entries:
                title = entry.get('title', '')
                time_start = entry.get('time_start', '')
                
                # Extraer URLs de descarga
                links = entry.get('links', [])
                download_links = [
                    link['href'] for link in links 
                    if link.get('rel') == 'http://esipfed.org/ns/fedsearch/1.1/data#'
                       and link['href'].endswith('.nc')
                ]
                
                if download_links:
                    granules.append({
                        'title': title,
                        'time': time_start,
                        'url': download_links[0],
                        'timestamp': datetime.strptime(time_start, '%Y-%m-%dT%H:%M:%S.%fZ') if time_start else None
                    })
            
            # Ordenar por timestamp
            granules.sort(key=lambda x: x['timestamp'] if x['timestamp'] else datetime.min, reverse=True)
            
            return granules
            
        except Exception as e:
            print(f"❌ Error al buscar: {e}")
            return []
    
    def download_file(self, url, filename, output_dir):
        """Descarga un archivo con barra de progreso"""
        output_path = output_dir / filename
        
        # Verificar si ya existe
        if output_path.exists():
            print(f"⏭️  Ya existe: {filename}")
            return output_path
        
        try:
            print(f"📥 Descargando: {filename}")
            response = self.session.get(url, stream=True, timeout=120)
            
            if response.status_code != 200:
                print(f"❌ Error HTTP {response.status_code}")
                return None
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f:
                if total_size == 0:
                    f.write(response.content)
                else:
                    downloaded = 0
                    chunk_size = 1024 * 1024  # 1 MB
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress = (downloaded / total_size) * 100
                        mb_downloaded = downloaded / 1024 / 1024
                        mb_total = total_size / 1024 / 1024
                        print(f"   {progress:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='\r')
            
            file_size = output_path.stat().st_size / 1024 / 1024
            print(f"\n✅ Descargado: {filename} ({file_size:.1f} MB)")
            return output_path
            
        except Exception as e:
            print(f"\n❌ Error al descargar: {e}")
            if output_path.exists():
                output_path.unlink()
            return None
    
    def get_latest_file(self, product, max_days_back=7):
        """Descarga el archivo más reciente de un producto"""
        print(f"\n{'='*70}")
        print(f"🛰️  {product}: Buscando archivo más reciente")
        print(f"{'='*70}")
        
        granules = self.search_granules(product, days_back=max_days_back)
        
        if not granules:
            print(f"⚠️  No se encontraron archivos de {product}")
            return None
        
        # Tomar el más reciente
        latest = granules[0]
        
        print(f"\n🎯 Archivo más reciente:")
        print(f"   Nombre: {latest['title']}")
        print(f"   Fecha: {latest['time']}")
        print(f"   Total disponibles: {len(granules)}")
        
        # Descargar
        downloaded_path = self.download_file(
            latest['url'],
            latest['title'],
            DOWNLOAD_DIR
        )
        
        return downloaded_path

def main():
    """Función principal"""
    print("\n" + "="*70)
    print("🛰️  TEMPO Data Downloader - NASA CMR API")
    print("="*70)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Directorio: {DOWNLOAD_DIR.absolute()}")
    
    # Verificar credenciales
    if not USERNAME or not PASSWORD:
        print("\n❌ ERROR: Credenciales no encontradas")
        print("Verifica tu archivo .env")
        return
    
    print(f"👤 Usuario: {USERNAME}")
    
    # Crear directorio
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    
    # Crear downloader
    downloader = TempoDownloader(USERNAME, PASSWORD)
    
    # Descargar productos
    downloaded_files = {}
    
    for product in ['NO2', 'O3']:
        downloaded = downloader.get_latest_file(product, max_days_back=7)
        if downloaded:
            downloaded_files[product] = downloaded
    
    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN")
    print("="*70)
    
    if downloaded_files:
        for product, filepath in downloaded_files.items():
            size_mb = filepath.stat().st_size / 1024 / 1024
            print(f"✅ {product}: {filepath.name}")
            print(f"   Tamaño: {size_mb:.1f} MB")
    else:
        print("⚠️  No se descargaron archivos nuevos")
    
    print("\n✨ Proceso completado\n")
    return downloaded_files

if __name__ == "__main__":
    main()
