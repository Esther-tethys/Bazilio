import numpy as np
import sounddevice as sd
import sys
import os
from flask import Flask, request, jsonify
from antlr4 import *

# Asegurar importación de los archivos de ANTLR4
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from BazilioLexer import BazilioLexer
from BazilioParser import BazilioParser

app = Flask(__name__)

# Pagina de inicio con una interfaz gráfica minimalista en HTML
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
            body { font-family: sans-serif; background-color: #1a1625; color: #e0d7f5; padding: 20px; }
            h2 { color: #c084fc; }
            textarea { width: 100%; height: 180px; background: #2a2438; color: #fff; border: 1px solid #7e22ce; border-radius: 8px; padding: 10px; font-family: monospace; }
            button { background-color: #9333ea; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; margin-top: 10px; font-weight: bold; }
            button:hover { background-color: #a855f7; }
            pre { background: #0f0d15; padding: 15px; border-radius: 8px; color: #a7f3d0; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h2>Analizador Gramatical Bazilio</h2>
        <p>Escribe o pega tus notas a continuación:</p>
        <textarea id="textoNotas" placeholder="Escribe aquí tus notas..."></textarea><br>
        <button onclick="analizar()">Analizar Notas</button>
        <h3>Resultado:</h3>
        <pre id="resultado">// El resultado aparecerá aquí...</pre>

        <script>
            async function analizar() {
                const notas = document.getElementById('textoNotas').value;
                const res = await fetch('/analizar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ notas })
                });
                const data = await res.json();
                document.getElementById('resultado').textContent = JSON.stringify(data, null, 2);
            }
        </script>
    </body>
    </html>
    '''

@app.route('/analizar', methods=['POST'])
def analizar_endpoint():
    datos = request.get_json()
    texto_notas = datos.get('notas', '')

    if not texto_notas.strip():
        return jsonify({"exito": False, "error": "El texto ingresado está vacío."}), 400

    try:
        input_stream = InputStream(texto_notas)
        lexer = BazilioLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = BazilioParser(stream)
        
        # Llama a tu regla inicial de Bazilio.g4 (ej. programa)
        tree = parser.programa()
        
        return jsonify({
            "exito": True,
            "mensaje": "Análisis completado sin errores.",
            "arbol": str(tree.toStringTree(recog=parser))
        })
    except Exception as e:
        return jsonify({"exito": False, "error": str(e)}), 500

if __name__ == '__main__':
    # Permite acceso en red local durante pruebas
    app.run(host='0.0.0.0', port=5000, debug=True)

# Asegurar que Python encuentre los archivos generados por ANTLR4 (BazilioLexer, BazilioParser, etc.)
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from BazilioLexer import BazilioLexer
from BazilioParser import BazilioParser
# from BazilioVisitor import BazilioVisitor  # Descomenta si usas un visitor personalizado

def procesar_texto_notas(texto_notas: str):
    """
    Recibe el contenido en texto plano de las notas y ejecuta 
    el análisis léxico y sintáctico utilizando ANTLR4.
    """
    if not texto_notas or not texto_notas.strip():
        return {"exito": False, "error": "El texto recibido está vacío."}

    try:
        # 1. Convertir el string de texto en un flujo de entrada para ANTLR
        input_stream = InputStream(texto_notas)
        
        # 2. Inicializar el Lexer con el stream de entrada
        lexer = BazilioLexer(input_stream)
        stream = CommonTokenStream(lexer)
        
        # 3. Inicializar el Parser con el flujo de tokens
        parser = BazilioParser(stream)
        
        # Opcional: Manejo de errores personalizado para evitar que imprima directo en consola
        # parser.removeErrorListeners()
        # parser.addErrorListener(TuCustomErrorListener())
        
        # 4. Llamar a la regla inicial de tu gramática (ej. 'programa', cámbiala por la tuya de Bazilio.g4)
        tree = parser.programa()
        
        # 5. Recorrer el árbol con tu Visitor o Listener si necesitas extraer datos o evaluar
        # visitor = BazilioVisitor()
        # resultado_evaluacion = visitor.visit(tree)
        
        return {
            "exito": True,
            "mensaje": "¡Análisis sintáctico procesado con éxito!",
            "arbol": tree,
            # "resultado": resultado_evaluacion
        }
        
    except Exception as e:
        return {
            "exito": False,
            "error": f"Error durante el análisis: {str(e)}"
        }

# --- Ejemplo de prueba si ejecutas este archivo directamente ---
if __name__ == '__main__':
    ejemplo_notas = """
    // Aquí iría el contenido de prueba de tus notas en formato Bazilio
    inicio_nota("Ideas de proyectos");
    agregar_linea("Revisar gramática ANTLR4");
    fin_nota();
    """
    
    respuesta = procesar_texto_notas(ejemplo_notas)
    print(respuesta)

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
    # Sostenidos en español
    t = t.replace('DOS', 'C#').replace('RES', 'D#').replace('FAS', 'F#')
    t = t.replace('SOLS', 'G#').replace('LAS', 'A#').replace('SIS', 'B#')
    # Notas base
    t = t.replace('SOL', 'G').replace('DO', 'C').replace('RE', 'D')
    t = t.replace('MI', 'E').replace('FA', 'F').replace('LA', 'A').replace('SI', 'B')
    return t

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

def validar_y_convertir_notas(texto):
    # Ignorar barras de compás, guiones y comas
    limpio = texto.replace('|', ' ').replace('-', ' ').replace(',', ' ')
    tokens = limpio.split()
    
    if not tokens:
        return None, "Por favor, ingresa al menos una nota."

    frecuencias = []
    invalidas = []

    for token in tokens:
        # Separar nota y duración (ej: Re4:1.5 -> Re4 y 1.5)
        partes = token.split(':')
        raw_nota = partes[0]
        mult = float(partes[1]) if len(partes) > 1 and partes[1].replace('.', '', 1).isdigit() else 1.0

        # Traducir de solfeo a inglés
        ingles_nota = traducir_solfeo_a_ingles(raw_nota)
        
        # Si no lleva octava explícita, agregar por defecto la octava 4
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

def reproducir_audio():
    texto = txt_entrada.get("1.0", tk.END).strip()
    datos, error = validar_y_convertir_notas(texto)

    if error:
        messagebox.showerror("Error de Validación", error)
        lbl_estado.config(text="Error en la entrada", fg="#D97706")
        return

    try:
        sample_rate = 44100
        base_duracion = 0.4
        
        lbl_estado.config(text="Reproduciendo audio...", fg="#7C3AED")
        root.update()

        audio_completo = []
        for freq, mult in datos:
            duracion = base_duracion * mult
            onda = generar_onda_nota(freq, duracion=duracion, sample_rate=sample_rate)
            audio_completo.append(onda)
            
        if audio_completo:
            signal = np.concatenate(audio_completo)
            sd.play(signal, sample_rate)
            sd.wait()

        lbl_estado.config(text="Reproducción finalizada", fg="#4A2E68")
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error al reproducir: {e}")
        lbl_estado.config(text="Error", fg="#DC2626")

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

    scaled = np.int16(onda_total / np.max(np.abs(onda_total) + 1e-5) * 32767)
    return scaled

def render_score_canvas_to_file(notes, filename):
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
            
        plt.savefig(filename, bbox_inches='tight', dpi=200)
        plt.close(fig)
    except Exception:
        with open(filename, 'w') as f:
            f.write("Reporte de Partitura - Bazilio\nNotas procesadas:\n" + str(notes))

def downloadAll():
    notes_raw, error = validar_y_convertir_notas(txt_entrada.get("1.0", tk.END).strip())
    if error:
        messagebox.showerror("Error", error)
        return

    carpeta_destino = filedialog.askdirectory(title="Selecciona la carpeta donde guardar los archivos")
    if not carpeta_destino:
        return

    try:
        ruta_bzl = os.path.join(carpeta_destino, 'notas.bzl')
        with open(ruta_bzl, 'w', encoding='utf-8') as f:
            f.write("# Archivo Bazilio (.bzl)\n# Notas Musicales con barras de compás\n\n" + txt_entrada.get("1.0", tk.END).strip())

        ruta_pdf = os.path.join(carpeta_destino, 'Partitura.pdf')
        render_score_canvas_to_file(notes_raw, ruta_pdf)

        ruta_wav = os.path.join(carpeta_destino, 'audio.wav')
        from scipy.io import wavfile
        audio_data = audio_buffer_a_wav_bytes(notes_raw)
        wavfile.write(ruta_wav, 44100, audio_data)

        messagebox.showinfo("Éxito", f"¡Archivos guardados correctamente en:\n{carpeta_destino}")
        lbl_estado.config(text="¡Archivos descargados con éxito!", fg="#059669")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron guardar los archivos: {e}")

# --- Interfaz Gráfica (Tkinter) ---
root = tk.Tk()
root.title("Estudio Musical Bazilio - Python Intérprete")
root.geometry("520x480")
root.configure(bg="#F3EEF9")

lbl_titulo = tk.Label(root, text="Traducción de Notas a Audio", font=('Inter', 14, 'bold'), bg="#F3EEF9", fg="#4A2E68")
lbl_titulo.pack(pady=(20, 5))

lbl_sub = tk.Label(root, text="Intérprete Python para Bazilio (Soporta | y Duraciones)", font=('Inter', 9), bg="#F3EEF9", fg="#7A6296")
lbl_sub.pack(pady=(0, 15))

frame_txt = tk.Frame(root, bg="#FFFFFF", bd=1, relief="solid")
frame_txt.pack(fill="x", padx=25, pady=5)

lbl_nota = tk.Label(frame_txt, text="NOTAS MUSICALES:", font=('Inter', 9, 'bold'), bg="#FFFFFF", fg="#6C538B")
lbl_nota.pack(anchor="w", padx=10, pady=(10, 2))

txt_entrada = tk.Text(frame_txt, height=5, bg="#FAF7FC", fg="#322144", font=('Consolas', 10), relief="flat")
txt_entrada.pack(fill="x", padx=10, pady=(0, 10))
txt_entrada.insert(tk.END, "| Re4:1.5 Do4:0.5 Do4:2 | Sol#3 La#3 Mi4 Fa4")

btn_reproducir = tk.Button(root, text="▶ Convertir y Reproducir Audio", bg="#9B72CF", fg="white", font=('Inter', 10, 'bold'), relief="flat", cursor="hand2", command=reproducir_audio)
btn_reproducir.pack(fill="x", padx=25, pady=10, ipady=8)

btn_descargar = tk.Button(root, text="📥 Descargar Todos los Archivos (.WAV, .BZL, .PDF)", bg="#4A2E68", fg="white", font=('Inter', 10, 'bold'), relief="flat", cursor="hand2", command=downloadAll)
btn_descargar.pack(fill="x", padx=25, pady=5, ipady=8)

lbl_estado = tk.Label(root, text="Listo", font=('Inter', 9, 'italic'), bg="#F3EEF9", fg="#7A6296")
lbl_estado.pack(pady=5)

root.mainloop()