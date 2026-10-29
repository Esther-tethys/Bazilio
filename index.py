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
    'C5': 523.25, 'C#5': 554.37, 'D5': 587.33, 'D#5': 622.25,
    'E5': 659.25, 'F5': 698.46, 'F#5': 739.99, 'G5': 783.99,
    'G#5': 830.61, 'A5': 880.00, 'A#5': 932.33, 'B5': 987.77,
    'C6': 1046.50, 'C#6': 1108.73, 'D6': 1174.66, 'D#6': 1244.51,
    'E6': 1318.51, 'F6': 1396.91, 'F#6': 1479.98, 'G6': 1567.98,
    'G#6': 1661.22, 'A6': 1760.00, 'A#6': 1864.66, 'B6': 1975.53
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
            key = key + '6'

        if key in NOTE_FREQUENCIES:
            # Sin el multiplicador extra, toma directamente la frecuencia natural de la octava
            freq_base = NOTE_FREQUENCIES[key]
            frecuencias.append((freq_base, mult))
        else:
            invalidas.append(raw_nota)

    if invalidas:
        invalidas_str = ", ".join(f"'{n}'" for n in set(invalidas))
        return None, f"Error: Se encontraron notas no válidas: {invalidas_str}."

    return frecuencias, None

def generar_onda_nota(frecuencia, duracion=0.4, sample_rate=44100):
    t = np.linspace(0, duracion, int(sample_rate * duracion), False)
    
    # Onda triangular limpia y suave
    phase = (t * frecuencia) % 1.0
    onda = 0.4 * (2 * np.abs(2 * phase - 1) - 1)
    
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

def generar_pdf_partitura(notes):
    buffer = io.BytesIO()
    try:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 2))
        ax.axis('off')
        
        for i in range(5):
            ax.axhline(i * 0.2, color='black', lw=1)
            
        ax.text(0.05, 0.8, "♩ = 120", fontsize=12, fontweight='bold')
        ax.text(0.15, 0.4, "🎼 C", fontsize=16)
        
        for idx, (freq, mult) in enumerate(notes):
            x = 0.3 + (idx * 0.05)
            y = 0.4 + ((idx % 5) * 0.05)
            ax.plot(x, y, 'ko', markersize=6)
            
        plt.savefig(buffer, format='pdf', bbox_inches='tight', dpi=200)
        plt.close(fig)
    except Exception:
        buffer.write(b"Reporte de Partitura - Bazilio\nNotas procesadas:\n" + str(notes).encode('utf-8'))
        
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
        <title>Bazilio ANTLR4 Parser y Archivos</title>
        <style>
            body { font-family: sans-serif; background-color: #1a1625; color: #e0d7f5; padding: 20px; max-width: 800px; margin: auto; }
            h2 { color: #c084fc; }
            textarea { width: 100%; height: 130px; background: #2a2438; color: #fff; border: 1px solid #7e22ce; border-radius: 8px; padding: 10px; font-family: monospace; box-sizing: border-box; }
            button { background-color: #9333ea; color: white; border: none; padding: 10px 15px; border-radius: 6px; cursor: pointer; margin-top: 10px; margin-right: 5px; font-weight: bold; font-size: 13px; }
            button:hover { background-color: #a855f7; }
            .btn-audio { background-color: #059669; }
            .btn-audio:hover { background-color: #10b981; }
            .btn-pdf { background-color: #dc2626; }
            .btn-pdf:hover { background-color: #ef4444; }
            .btn-bzl { background-color: #d97706; }
            .btn-bzl:hover { background-color: #f59e0b; }
            pre { background: #0f0d15; padding: 15px; border-radius: 8px; color: #a7f3d0; overflow-x: auto; }
            audio { margin-top: 10px; width: 100%; }
            .seccion-botones { margin-top: 10px; display: flex; flex-wrap: wrap; gap: 5px; }
        </style>
    </head>
    <body>
        <h2>Intérprete y Generador Musical Bazilio</h2>
        <p>Escribe o pega tus notas musicales a continuación:</p>
        <textarea id="textoNotas">| Re4:1.5 Do4:0.5 Do4:2 | Sol#3 La#3 Mi4 Fa4</textarea><br>
        
        <div class="seccion-botones">
            <button onclick="analizar()">🔍 Analizar Notas (ANTLR4)</button>
            <button class="btn-audio" onclick="generarAudio()">🔊 Reproducir / WAV</button>
            <button class="btn-pdf" onclick="descargarPDF()">📥 Descargar PDF</button>
            <button class="btn-bzl" onclick="descargarBZL()">📥 Descargar .BZL</button>
        </div>
        
        <div id="contenedorAudio" style="display:none; margin-top: 15px;">
            <audio id="reproductorAudio" controls></audio><br>
            <a id="enlaceDescargaWav" download="audio_bazilio.wav"><button style="background-color:#4f46e5; margin-top:5px;">📥 Descargar archivo .WAV</button></a>
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
                    
                    const enlace = document.getElementById('enlaceDescargaWav');
                    enlace.href = url;

                    document.getElementById('contenedorAudio').style.display = 'block';
                    audio.play();
                } catch (err) {
                    alert("Ocurrió un error al generar el audio.");
                }
            }

            async function descargarPDF() {
                const notas = document.getElementById('textoNotas').value;
                try {
                    const res = await fetch('/generar_pdf', {
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
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'Partitura.pdf';
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                } catch (err) {
                    alert("Error al descargar el PDF.");
                }
            }

            async function descargarBZL() {
                const notas = document.getElementById('textoNotas').value;
                try {
                    const res = await fetch('/generar_bzl', {
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
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'notas.bzl';
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                } catch (err) {
                    alert("Error al descargar el archivo .bzl.");
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

@app.route('/generar_pdf', methods=['POST'])
def generar_pdf_endpoint():
    datos = request.get_json() or {}
    texto_notas = datos.get('notas', '')

    frecuencias, error = validar_y_convertir_notas(texto_notas)
    if error:
        return jsonify({"exito": False, "error": error}), 400

    try:
        pdf_buffer = generar_pdf_partitura(frecuencias)
        return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name='Partitura.pdf')
    except Exception as e:
        return jsonify({"exito": False, "error": str(e)}), 500

@app.route('/generar_bzl', methods=['POST'])
def generar_bzl_endpoint():
    datos = request.get_json() or {}
    texto_notas = datos.get('notas', '')

    if not texto_notas.strip():
        return jsonify({"exito": False, "error": "El texto está vacío."}), 400

    try:
        contenido = f"# Archivo Bazilio (.bzl)\n# Notas Musicales\n\n{texto_notas}"
        bzl_buffer = io.BytesIO(contenido.encode('utf-8'))
        return send_file(bzl_buffer, mimetype='text/plain', as_attachment=True, download_name='notas.bzl')
    except Exception as e:
        return jsonify({"exito": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)