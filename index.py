import os
import sys
import numpy as np
from flask import Flask, request, jsonify
from antlr4 import *

# Asegurar importación de los archivos de ANTLR4
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from BazilioLexer import BazilioLexer
from BazilioParser import BazilioParser

app = Flask(__name__)

# Diccionario completo de frecuencias base (Octavas 3, 4 y 5, incluyendo sostenidos)
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
    """Traduce notación en español (Do, Re, Mi...) al formato anglosajón (C, D, E...)."""
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

# Página de inicio con una interfaz web minimalista en HTML
@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bazilio ANTLR4 Parser</title>
        <style>
            body { font-family: sans-serif; background-color: #1a1625; color: #e0d7f5; padding: 20px; max-width: 800px; margin: auto; }
            h2 { color: #c084fc; }
            textarea { width: 100%; height: 150px; background: #2a2438; color: #fff; border: 1px solid #7e22ce; border-radius: 8px; padding: 10px; font-family: monospace; box-sizing: border-box; }
            button { background-color: #9333ea; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; margin-top: 10px; font-weight: bold; }
            button:hover { background-color: #a855f7; }
            pre { background: #0f0d15; padding: 15px; border-radius: 8px; color: #a7f3d0; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h2>Analizador Gramatical Bazilio (ANTLR4)</h2>
        <p>Escribe o pega tus notas musicales a continuación:</p>
        <textarea id="textoNotas">| Re4:1.5 Do4:0.5 Do4:2 | Sol#3 La#3 Mi4 Fa4</textarea><br>
        <button onclick="analizar()">Analizar Notas</button>
        <h3>Resultado:</h3>
        <pre id="resultado">// El resultado del análisis aparecerá aquí...</pre>

        <script>
            async function analizar() {
                const notas = document.getElementById('textoNotas').value;
                document.getElementById('resultado').textContent = "Procesando...";
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

    # Validar formato y notas musicales
    _, error_notas = validar_y_convertir_notas(texto_notas)
    if error_notas:
        return jsonify({"exito": False, "error": error_notas}), 400

    try:
        input_stream = InputStream(texto_notas)
        lexer = BazilioLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = BazilioParser(stream)
        
        # Llamada a la regla inicial de tu gramática Bazilio.g4
        tree = parser.programa()
        
        return jsonify({
            "exito": True,
            "mensaje": "¡Análisis sintáctico procesado con éxito!",
            "arbol": str(tree.toStringTree(recog=parser))
        })
    except Exception as e:
        return jsonify({"exito": False, "error": f"Error durante el análisis: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)