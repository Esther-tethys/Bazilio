import os
import sys
import numpy as np
from flask import Flask, request, jsonify, send_file
import io
from antlr4 import *

# Asegurar importación de los archivos de ANTLR4
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from BazilioLexer import BazilioLexer
from BazilioParser import BazilioParser

app = Flask(__name__)

# Diccionario completo de frecuencias base
NOTE_FREQUENCIES = {
    'C3': 130.81, 'C#3': 138.59, 'D3': 146.83, 'D#3': 155.56,
    'E3': 164.81, 'F3': 174.61, 'F#3': 185.00, 'G3': 196.00,
    'G#3': 207.65, 'A3': 220.00, 'A#3': 233.08, 'B3': 246.94,
    'C4': 261.63, 'C#4': 277.18, 'D4': 293.66, 'D#4': 311.13,
    'E4': 329.63, 'F4': 349.23, 'F#4': 369.99, 'G4': 392.00,
    'G#4': 415.30, 'A4': 440.00, 'A#4': 466.16, 'B4': 493.88,
    'C5': 523.25, 'C#5': 554.37, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46,
    'G5': 783.99, 'A5': 880.00, 'B5': 987.77
}

def traducir_solfeo_a_ingles(token):
    t = token.upper()
    t = t.replace('DOS', 'C#').replace('RES', 'D#').replace('FAS', 'F#')
    t = t.replace('SOLS', 'G#').replace('LAS', 'A#').replace('SIS', 'B#')
    t = t.replace('SOL', 'G').replace('DO', 'C').replace('RE', 'D')
    t = t.replace('MI', 'E').replace('FA', 'F').replace('LA', 'A').replace('SI', 'B')
    return t

def validar_y_convertir_notas(texto):
    limpio = texto.replace('|', ' ').replace('-', ' ').replace(',', ' ')
    tokens = limpio.split()
    
    if not tokens:
        return None, "Por favor, ingresa al menos una nota."

    frecuencias = []
    invalidas = []

    for token in tokens:
        partes = token.split(':')
        raw_nota = partes[0]
        mult = float(partes[1]) if len(partes) > 1 and partes[1].replace('.', '', 1).isdigit() else 1.0

        ingles_nota = traducir_solfeo_a_ingles(raw_nota)
        key = ingles_nota
        if not any(char.isdigit() for char in key):
            key = key + '4'

        if key in NOTE_FREQUENCIES:
            frecuencias.append((NOTE_FREQUENCIES[key], mult))
        else:
            invalidas.append(raw_nota)

    if invalidas:
        invalidas_str = ", ".join(f"'{n}'" for n in set(invalidas))
        return None, f"Error: Se encontraron notas no válidas: {invalidas_str}."

    return frecuencias, None

def generar_onda_nota(frecuencia, duracion=0.4, sample_rate=44100):
    t = np.linspace(0, duracion, int(sample_rate * duracion), False)
    onda = 0.5 * np.sin(2 * np.pi * frecuencia * t)
    
    num_muestras = len(onda)
    ataque = int(sample_rate * 0.02)
    desvanecimiento = int(sample_rate * 0.05)
    
    envolvente = np.ones(num_muestras)
    if ataque < num_muestras:
        envolvente[:ataque] = np.linspace(0, 1, ataque)
    if desvanecimiento < num_muestras:
        envolvente[-desvanecimiento:] = np.linspace(1, 0, desvanecimiento)
        
    return onda * envolvente

def audio_buffer_a_wav_bytes(notes, sample_rate=44100):
    base_duracion = 0.4
    total_duracion = sum(base_duracion * n[1] for n in notes)
    total_samples = int(sample_rate * total_duracion)
    
    onda_total = np.zeros(total_samples)
    current_idx = 0
    
    for freq, mult in notes:
        duracion = base_duracion * mult
        onda = generar_onda_nota(freq, duracion=duracion, sample_rate=sample_rate)
        fin_idx = current_idx + len(onda)
        if fin_idx <= total_samples:
            onda_total[current_idx:fin_idx] += onda
        current_idx = fin_idx

    scaled = np.int16(onda_total / (np.max(np.abs(onda_total)) + 1e-5) * 32767)
    
    from scipy.io import wavfile
    buffer = io.BytesIO()
    wavfile.write(buffer, sample_rate, scaled)
    buffer.seek(0)
    return buffer

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bazilio ANTLR4 Parser y Audio</title>
        <style>
            body { font-family: sans-serif; background-color: #1a1625; color: #e0d7f5; padding: 20px; max-width: 800px; margin: auto; }
            h2 { color: #c084fc; }
            textarea { width: 100%; height: 130px; background: #2a2438; color: #fff; border: 1px solid #7e22ce; border-radius: 8px; padding: 10px; font-family: monospace; box-sizing: border-box; }
            button { background-color: #9333ea; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; margin-top: 10px; margin-right: 5px; font-weight: bold; }
            button:hover { background-color: #a855f7; }
            .btn-audio { background-color: #059669; }
            .btn-audio:hover { background-color: #10b981; }
            pre { background: #0f0d15; padding: 15px; border-radius: 8px; color: #a7f3d0; overflow-x: auto; }
            audio { margin-top: 10px; width: 100%; }
        </style>
    </head>
    <body>
        <h2>Intérprete y Generador Musical Bazilio</h2>
        <p>Escribe o pega tus notas musicales a continuación:</p>
        <textarea id="textoNotas">| Re4:1.5 Do4:0.5 Do4:2 | Sol#3 La#3 Mi4 Fa4</textarea><br>
        <button onclick="analizar()">Analizar Notas (ANTLR4)</button>
        <button class="btn-audio" onclick="generarAudio()">🔊 Reproducir / Descargar Audio</button>
        
        <div id="contenedorAudio" style="display:none; margin-top: 15px;">
            <audio id="reproductorAudio" controls></audio><br>
            <a id="enlaceDescarga" download="audio_bazilio.wav"><button style="background-color:#4f46e5;">📥 Descargar archivo .WAV</button></a>
        </div>

        <h3>Resultado del Análisis:</h3>
        <pre id="resultado">// El resultado aparecerá aquí...</pre>

        <script>
            async function analizar() {
                const notas = document.getElementById('textoNotas').value;
                document.getElementById('resultado').textContent = "Procesando sintaxis...";
                try {
                    const res = await fetch('/analizar', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ notas })
                    });
                    const data = await res.json();
                    document.getElementById('resultado').textContent = JSON.stringify(data, null, 2);
                } catch (err) {
                    document.getElementById('resultado').textContent = "Error de conexión con el servidor.";
                }
            }

            async function generarAudio() {
                const notas = document.getElementById('textoNotas').value;
                try {
                    const res = await fetch('/generar_audio', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ notas })
                    });
                    if (!res.ok) {
                        const err = await res.json();
                        alert("Error: " + err.error);
                        return;
                    }
                    const blob = await res.blob();
                    const url = URL.createObjectURL(blob);
                    
                    const audio = document.getElementById('reproductorAudio');
                    audio.src = url;
                    
                    const enlace = document.getElementById('enlaceDescarga');
                    enlace.href = url;

                    document.getElementById('contenedorAudio').style.display = 'block';
                    audio.play();
                } catch (err) {
                    alert("Ocurrió un error al generar el audio.");
                }
            }
        </script>
    </body>
    </html>
    '''

@app.route('/analizar', methods=['POST'])
def analizar_endpoint():
    datos = request.get_json() or {}
    texto_notas = datos.get('notas', '')

    if not texto_notas.strip():
        return jsonify({"exito": False, "error": "El texto ingresado está vacío."}), 400

    _, error_notas = validar_y_convertir_notas(texto_notas)
    if error_notas:
        return jsonify({"exito": False, "error": error_notas}), 400

    try:
        input_stream = InputStream(texto_notas)
        lexer = BazilioLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = BazilioParser(stream)
        tree = parser.programa()
        
        return jsonify({
            "exito": True,
            "mensaje": "¡Análisis sintáctico procesado con éxito!",
            "arbol": str(tree.toStringTree(recog=parser))
        })
    except Exception as e:
        return jsonify({"exito": False, "error": f"Error durante el análisis: {str(e)}"}), 500

@app.route('/generar_audio', methods=['POST'])
def generar_audio_endpoint():
    datos = request.get_json() or {}
    texto_notas = datos.get('notas', '')

    frecuencias, error = validar_y_convertir_notas(texto_notas)
    if error:
        return jsonify({"exito": False, "error": error}), 400

    try:
        wav_buffer = audio_buffer_a_wav_bytes(frecuencias)
        return send_file(wav_buffer, mimetype='audio/wav', as_attachment=True, download_name='bazilio_audio.wav')
    except Exception as e:
        return jsonify({"exito": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)