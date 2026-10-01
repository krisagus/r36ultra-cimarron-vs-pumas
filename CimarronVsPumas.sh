#!/bin/bash
# ==============================================================================
# Lanzador de Cimarrón vs Pumas para ArkOS / R36 Ultra (RK3326 - 720x720)
# ==============================================================================

# 1. Permisos para dispositivos de video DRM/KMS, framebuffer y consola tty1
sudo chmod 666 /dev/dri/* /dev/fb0 /dev/tty1 2>/dev/null || chmod 666 /dev/dri/* /dev/fb0 /dev/tty1 2>/dev/null || true

# 2. Preload de libSDL2 nativo de ArkOS con soporte de aceleración KMSDRM
if [ -f "/usr/lib/aarch64-linux-gnu/libSDL2-2.0.so.0.3000.10" ]; then
    export LD_PRELOAD="/usr/lib/aarch64-linux-gnu/libSDL2-2.0.so.0.3000.10"
elif [ -f "/usr/lib/aarch64-linux-gnu/libSDL2-2.0.so.0" ]; then
    export LD_PRELOAD="/usr/lib/aarch64-linux-gnu/libSDL2-2.0.so.0"
else
    NATIVE_SDL=$(find /usr/lib -name "libSDL2-2.0.so.0*" 2>/dev/null | head -n 1)
    if [ -n "$NATIVE_SDL" ]; then
        export LD_PRELOAD="$NATIVE_SDL"
    fi
fi

# 3. Variables de entorno gráficas y de audio
export SDL_VIDEODRIVER=kmsdrm
export SDL_AUDIODRIVER=alsa
export SDL_NOMOUSE=1
export SDL_ASSERT=always_ignore
export TERM=linux
export PYTHONUNBUFFERED=1

# 4. Configuración SDL Game Controller para hardware GO-Super Gamepad
export SDL_GAMECONTROLLERCONFIG="190000004b4800000011000000010000,GO-Super Gamepad,a:b1,b:b0,x:b2,y:b3,back:b12,start:b13,dpup:b8,dpdown:b9,dpleft:b10,dpright:b11,leftshoulder:b4,rightshoulder:b5,lefttrigger:b6,righttrigger:b7,leftstick:b14,rightstick:b15,leftx:a0,lefty:a1,rightx:a2,righty:a3,platform:Linux,"

# 5. Pausar monitor de eventos de ArkOS (evita interceptar combinaciones de teclas)
sudo systemctl stop oga_events 2>/dev/null || true

# 6. Ocultar cursor y limpiar terminal en /dev/tty1
printf "\033[?25l" > /dev/tty1 2>/dev/null || true
printf "\033c" > /dev/tty1 2>/dev/null || true

# 7. Localizar directorio del juego
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -d "$SCRIPT_DIR/cimarron_vs_pumas" ]; then
    GAME_DIR="$SCRIPT_DIR/cimarron_vs_pumas"
elif [ -d "/roms/ports/cimarron_vs_pumas" ]; then
    GAME_DIR="/roms/ports/cimarron_vs_pumas"
else
    GAME_DIR="$SCRIPT_DIR"
fi

cd "$GAME_DIR"

# 8. Ejecución del juego con redirección de E/S y captura de logs
python3 -u main.py < /dev/tty1 > crash_log.txt 2>&1

# 9. Restauración del entorno de consola y reinicio de servicios
printf "\033[?25h" > /dev/tty1 2>/dev/null || true
printf "\033c" > /dev/tty1 2>/dev/null || true
sudo systemctl restart oga_events 2>/dev/null &

exit 0
