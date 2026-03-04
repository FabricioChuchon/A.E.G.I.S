# A.E.G.I.S. - Autonomous Evasion & Guidance Intelligent System

![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)


**A.E.G.I.S.** es un sistema de software desarrollado bajo el paradigma de **Programación Orientada a Objetos (POO)**. Su objetivo es proporcionar una solución autónoma y eficiente para el diagnóstico y maniobras de evasión de basura espacial en la órbita baja terrestre (LEO)

## 🚀 Características Principales

* **Dinámica Orbital HCW**: Implementación de las ecuaciones de Hill-Clohessy-Wiltshire para modelar la dinámica relativa y calcular la Matriz de Transición de Estado.
* **Evaluación de Riesgo**: Motor de análisis probabilístico gaussiano para predecir impactos y calcular el *Time of Closest Approach* (TCA).
* **Guiado Autónomo**: Optimización de maniobras de escape utilizando el paradigma de Obstáculos de Velocidad Lineal Equivalente (ELVO).
* **Telemetría IoT**: Arquitectura de monitoreo remoto basada en el protocolo MQTT para la transmisión de datos críticos como combustible y alertas.
* **Validación Estadística**: Simulaciones de Monte Carlo para verificar la supervivencia y trazabilidad física de las maniobras.

## 🛠️ Tecnologías utilizadas

* **NumPy**: Procesamiento de álgebra lineal y cálculos de matrices de transición con baja latencia.
* **Matplotlib**: Generación de Radar Táctico 3D y HUD de integridad en tiempo real.
* **Paho-MQTT**: Gestión del enlace de telemetría entre el satélite y dispositivos móviles.
* **Unittest**: Automatización de pruebas unitarias para asegurar la robustez de la física orbital.
* **PySerial**: Permite la comunicación entre el software de alto nivel (Python) y el hardware de detección (Arduino/Radar)


## 🛠️ Instalación y Configuración

Sigue estos pasos para desplegar el entorno de simulación A.E.G.I.S. en tu computadora:

### 1. Requisitos Previos
Asegúrate de tener instalado **Python 3.9** o superior. Se recomienda el uso de un entorno virtual para mantener las dependencias aisladas.

### 2. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/AEGIS-Project.git
cd AEGIS-Project
```

### 3. Instalación de Dependencias
```bash
python -m pip install numpy matplotlib paho-mqtt pyserial
```

### 4. Configuración del Broker MQTT
El sistema está configurado por defecto para usar el broker público de Mosquitto:
* Servidor: test.mosquitto.org
* Puerto: 1883
* Tópico base: uni/aegis/fabricio/

Nota: Para visualizar la telemetría en tiempo real, puedes usar clientes como IoT MQTT Panel o una app móvil configurada con el mismo tópico.


### 5. Configuración del Arduino

En el IDE de arduino copiamos el código del archivo "Arduino_code.txt", lo compilamos y lo exportamos al Arduino

### 6. Ejecución del Sistema
Para iniciar el motor de simulación y el dashboard dinámico
```bash
python main.py
```
Luego, desde el dispositivo móvil donde se configuró el cliente IoT, accionamos el botón "Lanzar Satélite"

### 7. Ejecución de los Test
Si queremos "probar" cada módulo por separado para ver si funciona correctamente o hay algun error de simulación.

Para probar los propulsores del satélite
```bash
python test_actuators.py
```
Para probar el cerebro del satélite
```bash
python test_brain.py
```
Para probar la física de la simulación
```bash
python test_physics.py
```
Y si queremos probar todos los módulos a la vez
```bash
python -m unittest discover
```
También podemos correr una simulación de Montecarlo para poder verificar la eficacia de nuestro algoritmo
```bash
python montecarlo.py
```
## ⚙️ Configuración y Parámetros Modificables
Para ajustar el comportamiento de la simulación, puedes modificar los siguientes parámetros directamente en los archivos
* Altitud de la Órbita: (Physics.py / Montecarlo.py): Por defecto está configurada en 800 km. Puedes cambiar este valor en la instanciación de RelativeDynamics para ver cómo varía el periodo orbital y la matriz de transición.
* Cantidad de Basura Espacial (main.py/ line 39): Cambiamos la cantidad de iteraciones de la variable "i" por el número querido de basura, se recomienda poner un valor no mayor a 10 por cuestiones de rendimiento y eficiencia del algoritmo de evasión 
* Sensibilidad de Riesgo (Brain.py): El parámetro sigma en AegisBrain define qué tan "nervioso" es el satélite ante una aproximación. Un valor menor hará que el sistema sea más sensible a las distancias de fallo.
* Capacidad de Combustible (Actuators.py): En la clase PropulsionSystem, puedes modificar la masa inicial de propelente y el impulso específico para probar motores con diferente eficiencia.
* Umbral de Detección (Sensors.py): El detection_range del radar (por defecto 200 m) define qué tan cerca debe estar un escombro para que el sistema lo rastree.
* Escenario de Estrés (Montecarlo.py): Puedes aumentar el número de iterations (por defecto 100) para obtener reportes estadísticos más robustos sobre la supervivencia del satélite.


## 📖 Manual de Operación
Siga estos pasos para una simulación exitosa:
### 1. Sin datos del Sensor Físico:
### 1.1. Fase de Standby y Conexión
* Al ejecutar main.py, escogemos la primera opción y el sistema inicializará el motor de física HCW y el enlace de telemetría.
* El programa se detendrá en un estado de Standby, esperando la señal de ignición desde el broker MQTT.
### 1.2. Comando de Ignición
* Para iniciar la secuencia de vuelo, envíe el mensaje de texto INICIAR al tópico uni/aegis/fabricio/comando.
* Una vez recibido el comando, el satélite comenzará su propagación orbital y el escaneo de amenazas.
### 1.3. Monitoreo y Radar 
* Radar Táctico 3D: Muestra la posición relativa del satélite y los escombros en un marco LVLH.
* Sensor PPI (Polar): Proporciona una vista bidimensional de la proximidad de las amenazas detectadas por el sensor de proximidad.
* HUD de Integridad: En la esquina superior izquierda de la pantalla, podrá visualizar en tiempo real:
      - Distancia de fallo (Miss Distance).
      - Probabilidad de colisión estimada por el AegisBrain.
      - Estado del combustible y vector de empuje aplicado.
### 1.4. Maniobras de Evasión
* El sistema es totalmente autónomo. Si el AegisBrain detecta un riesgo que supera el umbral de seguridad, el GuidanceSystem calculará y aplicará automáticamente un vector Delta-V.
* Verá una "trayectoria fantasma" (línea cian) que representa la proyección de la maniobra de escape.

### 2. Con datos del Sensor Físico:
* Al ejecutar el main.py, escogemos la segunda opción y el sistema inicializará el entorno gráfico.
* En caso no esté conectado el puerto USB y no se haya configurado el nombre correctamente el nombre del puerto, saldrá una alerta.
* Si está correctamente conectado, podremos poner objetos en el rango de detección del sensor y se materializarán en la simulación.

## 📞 Contacto


* **Desarrollado por**: 
    * Chuchon Huillca Fabricio Xavier fabricio.chuchon.h@uni.pe
    * Rojas Huaman Sebastián Estefano José María s.rojas.h@uni.pe
    * Cortez Segura Rodrigo Yesu rodrigo.cortez.s@uni.pe
* **Universidad**: Universidad Nacional de Ingeniería 

---
© 2026 A.E.G.I.S. Project - Universidad Nacional de Ingeniería.
