# Reporte Académico de Implementación: Cimarrón vs Pumas

## 1. Mecánica Implementada
Se implementó el ciclo de físicas de combate en 2D basado en el motor Pygame. El sistema incluye un motor de gravedad, detección de colisiones con un plano de suelo delimitado matemáticamente (`FLOOR = 650`), y bounding boxes (Cajas de colisión) adaptadas a una resolución de 720x720 (proporción 1:1, ideal para la pantalla de la consola R36 Ultra). Las entradas fueron abstractas mediante `pygame.joystick` para capturar la botonería real de ArkOS (D-Pad, A, B, X, Y).

## 2. Implementación de Red (Data Science y Protocolos)
Para permitir que dos consolas físicas se conecten localmente en la universidad **sin necesidad de internet ni configurar IPs manualmente**, se implementó un sistema basado en **Sockets UDP (User Datagram Protocol) no bloqueantes** a través de un Hotspot Wi-Fi móvil.
*   **Discovery Broadcast**: El Host abre el puerto `5005` y escucha. El cliente envía ráfagas UDP de broadcast (`255.255.255.255`) hasta recibir un `ACK` del Host.
*   **Data Packing Binario**: En lugar de enviar strings pesados (como JSON), se utilizó `struct.pack` de Python (`!4sIffiiB`). Esto empaqueta las coordenadas X, Y, los puntos de vida, el ID de acción y la bandera booleana de dirección en escasos ~20 bytes por frame, maximizando el rendimiento (60 FPS) y previniendo la saturación del router del celular.

## 3. Elementos Probabilísticos y Telemetría
Para cumplir con los estrictos requerimientos de análisis de la materia de Ciencia de Datos y Sistemas Complejos, se diseñó el módulo `telemetry.py` que pre-aloja memoria lineal mediante `NumPy` (`np.zeros()`), lo cual evita activar el Garbage Collector (GC) de Python repetidamente y previene los infames "micro-stutters" en procesadores ARM de bajo consumo (como el RK3326 de la consola).

Los dos cálculos en tiempo real realizados al salir de la partida incluyen:
1.  **Entropía de Shannon (H)**: 
    Se calcula la incertidumbre del estado del canal. Matemáticamente, determina qué tan estocástica es la pérdida de paquetes durante el combate basándose en un buffer circular.
2.  **Cadenas de Markov (Modelo Gilbert-Elliott)**:
    Se modela el canal de comunicación móvil como una cadena de Markov de dos estados: **G (Good)** y **B (Bad)**. La telemetría cuenta empíricamente las transiciones de estado de pérdida de datagramas de red y extrae las probabilidades base:
    *   P(G -> B) (Probabilidad de entrar a un estado de pérdida).
    *   P(B -> G) (Probabilidad de recuperar la señal).

## 4. Adaptación a la Arquitectura "Coding With Russ"
A diferencia del tutorial original (orientado a PC en teclado de resolución 16:9 con físicas completas acopladas a la animación), el sistema se desacopló en:
*   Manejo de red explícito que **sobrescribe** directamente las variables de posición del oponente (`net_data`).
*   Inyección de controles unificados para mando (Gamepad SDL) y soporte para cierre mediante combinaciones tipo consola `Start + Select`.
*   Aislamiento en módulos `main.py`, `fighter.py`, `network_manager.py` y `telemetry.py` para cumplir las mejores prácticas de POO.
