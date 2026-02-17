# 🏝️ File Island - Digimon Infinite Streamer

**File Island** es una plataforma de streaming 24/7 diseñada para reproducir de forma ininterrumpida la serie Digimon. Este proyecto utiliza un motor de procesamiento de video en tiempo real basado en **FFmpeg** y **Python**, sirviendo el contenido a través del protocolo **HLS** (HTTP Live Streaming) para una compatibilidad total con navegadores modernos.



## 🚀 Características Principales

* **Emisión 24/7 Non-Stop:** Reproducción en bucle infinito de todas las temporadas configuradas.
* **Zero Disk Wear (RAM Disk):** Los fragmentos de video se generan en `/dev/shm`, evitando escrituras constantes en el SSD/HDD.
* **Sincronización de Metadatos:** Actualización automática del título del episodio actual en la interfaz web.
* **Estética RDT Custom:** Interfaz basada en el diseño de "Ride to Gondor" adaptada al universo Digimon.
* **Optimización de Red:** Configuración lista para NGINX y túneles de Cloudflare.

## 🛠️ Requisitos del Sistema

* **Servidor:** Linux (Ubuntu/Debian recomendado).
* **Procesamiento:** `ffmpeg` y `ffprobe` instalados.
* **Entorno:** Python 3.x.
* **Web:** NGINX configurado como proxy inverso.
* **Memoria:** Al menos 100MB libres en `/dev/shm` (RAM Disk).

## 📂 Estructura del Proyecto

```text
/var/www/fileisland/
├── backend/
│   ├── streamer.py        # Script principal de control y FFmpeg
│   └── playlist.txt       # Lista de archivos generada dinámicamente
├── frontend/
│   ├── index.html         # Interfaz web con Video.js
│   ├── fileisland.png     # Logo y favicon de la web
│   └── logo-icon.jpeg     # Logo de Reconquista Dev Team
└── live/                  # (Alias NGINX) -> /dev/shm/hls_fileisland/
