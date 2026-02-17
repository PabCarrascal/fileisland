import subprocess
import os
import time
import threading
import re

HLS_PATH = "/dev/shm/hls_fileisland/"
TITULO_FILE = os.path.join(HLS_PATH, "titulo.txt")
MEDIA_ROOT = "/media/HDD3TB/SERIES/series/"
PLAYLIST_FILE = "/var/www/fileisland/backend/playlist.txt"

# Ajustado a la ruta exacta que pasaste
ORDEN_CARPETAS = [
    "Digimon Adventure (1999)/Season 01"
]

playlist_data = []

def obtener_duracion(archivo):
    try:
        cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{archivo}"'
        return float(os.popen(cmd).read().strip())
    except:
        return 1320  # Fallback 22 min por episodio

def generar_lista_y_titulos():
    global playlist_data
    playlist_data = []
    
    if not os.path.exists(HLS_PATH):
        os.makedirs(HLS_PATH, exist_ok=True)
    
    with open(PLAYLIST_FILE, "w") as f:
        for carpeta in ORDEN_CARPETAS:
            ruta = os.path.join(MEDIA_ROOT, carpeta)
            if os.path.exists(ruta):
                # Escaneamos los archivos .mkv
                videos = [v for v in os.listdir(ruta) if v.lower().endswith('.mkv')]
                for v in sorted(videos):
                    video_path = os.path.join(ruta, v)
                    duracion = obtener_duracion(video_path)
                    
                    # Limpiamos el nombre para el título (quitamos extensión)
                    titulo = v.replace(".mkv", "")
                    playlist_data.append({"titulo": titulo, "duracion": duracion})
                    
                    # Formato concat para ffmpeg con escape de comillas
                    f.write(f"file '{video_path.replace(chr(39), chr(39)+chr(92)+chr(39)+chr(39))}'\n")

def monitorizar_titulos(proceso):
    inicio_stream = time.time()
    while True:
        tiempo_actual = (time.time() - inicio_stream)
        duracion_total_playlist = sum(item['duracion'] for item in playlist_data)
        
        if duracion_total_playlist > 0:
            tiempo_en_ciclo = tiempo_actual % duracion_total_playlist
            acumulado = 0
            titulo_actual = "Digimon Adventure"
            
            for item in playlist_data:
                acumulado += item['duracion']
                if tiempo_en_ciclo < acumulado:
                    titulo_actual = item['titulo']
                    break
            
            with open(TITULO_FILE, "w") as f:
                f.write(titulo_actual)
        
        time.sleep(10)

def iniciar_ffmpeg():
    comando = [
        'ffmpeg', '-loglevel', 'error', '-nostats',
        '-re', '-stream_loop', '-1', '-f', 'concat', '-safe', '0', '-i', PLAYLIST_FILE,
        '-map', '0:v:0',
        '-map', '0:a:0?',
        '-c:v', 'libx264', 
        '-preset', 'ultrafast', 
        '-tune', 'zerolatency', 
        '-crf', '23', 
        '-maxrate', '3000k', 
        '-bufsize', '6000k',
        '-pix_fmt', 'yuv420p', 
        '-g', '50', 
        '-c:a', 'aac', '-b:a', '128k', '-ac', '2', '-ar', '44100',
        '-f', 'hls', '-hls_time', '4', '-hls_list_size', '5', '-hls_flags', 'delete_segments',
        os.path.join(HLS_PATH, 'live.m3u8')
    ]
    return subprocess.Popen(comando)

if __name__ == "__main__":
    generar_lista_y_titulos()
    if not os.path.exists(TITULO_FILE):
        with open(TITULO_FILE, "w") as f: f.write("Iniciando archivos...")
    while True:
        proceso = iniciar_ffmpeg()
        hilo_titulos = threading.Thread(target=monitorizar_titulos, args=(proceso,), daemon=True)
        hilo_titulos.start()
        proceso.wait()
        time.sleep(5)
