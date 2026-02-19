import subprocess
import os
import time
import threading
import re
import json

# CONFIGURACIÓN DE RUTAS
HLS_PATH = "/dev/shm/hls_fileisland/"
MEDIA_ROOT = "/media/HDD3TB/SERIES/series/" 
PLAYLIST_FILE = "/var/www/fileisland/backend/playlist.txt"
STATUS_FILE = os.path.join(HLS_PATH, "status.json")

# Orden de reproducción
ORDEN_REPRODUCCION = [
    "Digimon Adventure (1999)/Season 01"
]

playlist_data = []
inicio_stream = time.time() # Reloj global

def obtener_duracion(archivo):
    try:
        cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{archivo}"'
        return float(os.popen(cmd).read().strip())
    except:
        return 1320 # Fallback 22 min

def generar_lista_y_titulos():
    global playlist_data
    playlist_data = []
    
    if not os.path.exists(HLS_PATH):
        os.makedirs(HLS_PATH, exist_ok=True)
    
    with open(PLAYLIST_FILE, "w") as f:
        for sub_ruta in ORDEN_REPRODUCCION:
            ruta_completa = os.path.join(MEDIA_ROOT, sub_ruta)
            
            if os.path.exists(ruta_completa):
                videos = [v for v in os.listdir(ruta_completa) if v.lower().endswith('.mkv')]
                videos.sort()
                
                for v in videos:
                    video_path = os.path.join(ruta_completa, v)
                    duracion = obtener_duracion(video_path)
                    titulo_web = v.replace(" (1999)", "").replace(".mkv", "")
                    
                    playlist_data.append({"titulo": titulo_web, "duracion": duracion})
                    path_ffmpeg = video_path.replace("'", "'\\''")
                    f.write(f"file '{path_ffmpeg}'\n")

def monitorizar_titulos():
    global inicio_stream
    while True:
        if not playlist_data:
            time.sleep(5)
            continue
            
        tiempo_actual = (time.time() - inicio_stream)
        duracion_total = sum(item['duracion'] for item in playlist_data)
        
        if duracion_total > 0:
            tiempo_en_ciclo = tiempo_actual % duracion_total
            acumulado = 0
            
            titulo_actual = "Calculando..."
            titulo_siguiente = "Calculando..."
            
            for i, item in enumerate(playlist_data):
                acumulado += item['duracion']
                if tiempo_en_ciclo < acumulado:
                    titulo_actual = item['titulo']
                    siguiente_index = (i + 1) % len(playlist_data)
                    titulo_siguiente = playlist_data[siguiente_index]['titulo']
                    break
            
            estado = {
                "actual": titulo_actual,
                "siguiente": titulo_siguiente
            }
            
            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(estado, f, ensure_ascii=False)
        
        time.sleep(10)

def iniciar_ffmpeg():
    comando = [
        'ffmpeg', '-loglevel', 'error', '-nostats',
        '-re', '-stream_loop', '-1', '-f', 'concat', '-safe', '0', '-i', PLAYLIST_FILE,
        
        '-map', '0:v:0', 
        '-map', '0:a:0?', 
        
        # Eliminar subtítulos flotantes
        '-sn', 
        
        # Normalización estricta de Video (720p 24fps) y Bandas negras auto
        '-c:v', 'libx264', 
        '-vf', 'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2',
        '-r', '24', 
        
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-crf', '23', 
        '-maxrate', '3000k', 
        '-bufsize', '6000k',
        '-pix_fmt', 'yuv420p',
        '-g', '48', 
        
        # Normalización estricta de Audio
        '-c:a', 'aac', '-b:a', '128k', '-ac', '2', '-ar', '44100',
        '-af', 'aresample=async=1',
        
        # Configuración HLS (15 segmentos = 60 seg de margen)
        '-f', 'hls', '-hls_time', '4', '-hls_list_size', '15', '-hls_flags', 'delete_segments',
        os.path.join(HLS_PATH, 'live.m3u8')
    ]
    return subprocess.Popen(comando)

if __name__ == "__main__":
    print("--- Generando Playlist de File Island ---")
    generar_lista_y_titulos()
    
    if not os.path.exists(HLS_PATH):
        os.makedirs(HLS_PATH, exist_ok=True)
        
    if not os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "w", encoding="utf-8") as f: 
            json.dump({"actual": "Inicializando...", "siguiente": "Standby..."}, f)
    
    threading.Thread(target=monitorizar_titulos, daemon=True).start()
    
    print("--- Iniciando Stream 24/7 ---")
    while True:
        inicio_stream = time.time() # Reset de sincronización por si FFmpeg crashea
        proceso = iniciar_ffmpeg()
        proceso.wait()
        print("Aviso: FFmpeg se detuvo. Reiniciando en 5 segundos...")
        time.sleep(5)
