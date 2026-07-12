import os, json
import pandas as pd
from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from werkzeug.utils import secure_filename
from data_handler import load_data, resumen_por_periodo, meses_disponibles, allowed_file, agregar_categoria
from pdf_generator import generar_pdf
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'data')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']
CACHE_FILE = os.path.join(UPLOAD_FOLDER, '_cache.json')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

df_global = None
nombre_archivo_actual = None

def _df_to_cache(df, filename):
    data = df.to_dict('records')
    import numpy as np
    for r in data:
        for k, v in r.items():
            if isinstance(v, pd.Timestamp):
                r[k] = v.isoformat()
            elif isinstance(v, np.integer):
                r[k] = int(v)
            elif isinstance(v, np.floating):
                r[k] = float(v)
            elif pd.isna(v):
                r[k] = None
    payload = {'filename': filename, 'rows': data}
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False)

def _load_cache():
    global df_global, nombre_archivo_actual
    if not os.path.exists(CACHE_FILE):
        return
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        df = pd.DataFrame(payload['rows'])
        for col in ['fecha']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        for col in ['ingreso', 'egreso', 'monto']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df_global = df
        nombre_archivo_actual = payload.get('filename')
    except Exception:
        pass

_load_cache()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

@app.route('/api/upload', methods=['POST'])
def upload():
    global df_global, nombre_archivo_actual
    if 'file' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo'}), 400
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Formato no válido. Usa .xlsx o .csv'}), 400
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    try:
        df_global = load_data(filepath)
        df_global = agregar_categoria(df_global)
        nombre_archivo_actual = filename
        _df_to_cache(df_global, filename)
        meses = meses_disponibles(df_global)
        ahora = datetime.now()
        mes_actual = ahora.month
        año_actual = ahora.year
        if meses:
            ultimo = meses[-1]
            mes_actual = ultimo['mes']
            año_actual = ultimo['año']
        resumen = resumen_por_periodo(df_global, periodo='mensual', año=año_actual, mes=mes_actual)
        return jsonify({
            'mensaje': 'Archivo cargado correctamente',
            'archivo': filename,
            'meses': meses,
            'resumen': resumen,
            'mes_seleccionado': mes_actual,
            'año_seleccionado': año_actual,
            'total_transacciones': len(df_global),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data')
def get_data():
    global df_global
    if df_global is None:
        return jsonify({'error': 'No hay datos cargados'}), 400
    periodo = request.args.get('periodo', 'mensual')
    año = request.args.get('año', None)
    mes = request.args.get('mes', None)
    año = int(año) if año else None
    mes = int(mes) if mes else None
    resumen = resumen_por_periodo(df_global, periodo=periodo, año=año, mes=mes)
    return jsonify(resumen)

@app.route('/api/meses')
def get_meses():
    global df_global
    if df_global is None:
        return jsonify({'error': 'No hay datos cargados'}), 400
    return jsonify(meses_disponibles(df_global))

@app.route('/api/exportar-pdf', methods=['POST'])
def exportar_pdf():
    global df_global
    if df_global is None:
        return jsonify({'error': 'No hay datos cargados'}), 400
    data = request.get_json() or {}
    periodo = data.get('periodo', 'mensual')
    año = data.get('año', None)
    mes = data.get('mes', None)
    año = int(año) if año else None
    mes = int(mes) if mes else None
    resumen = resumen_por_periodo(df_global, periodo=periodo, año=año, mes=mes)
    meses_nombres = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                     'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    mes_nombre = meses_nombres[mes] if mes else ''
    año_str = str(año) if año else ''
    periodo_label = 'Semanal' if periodo == 'semanal' else 'Mensual'
    pdf_buf = generar_pdf(resumen, periodo_label, mes_nombre, año_str)
    return send_file(
        pdf_buf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'Informe_Gastos_{mes_nombre}_{año_str}.pdf'
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
