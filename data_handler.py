import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def _convert(v):
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if pd.isna(v):
        return None
    return v

def _clean_record(d):
    return {k: _convert(v) for k, v in d.items()}

ALLOWED_EXTENSIONS = {'xlsx', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_data(filepath):
    ext = filepath.rsplit('.', 1)[1].lower()
    if ext == 'xlsx':
        df = pd.read_excel(filepath)
    else:
        df = pd.read_csv(filepath, encoding='utf-8-sig')
    df.columns = [c.strip().lower() for c in df.columns]
    col_map = {'fecha': 'fecha', 'concepto': 'concepto', 'ingreso': 'ingreso', 'egreso': 'egreso'}
    df = df.rename(columns=col_map)
    df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True, errors='coerce')
    df['ingreso'] = pd.to_numeric(df['ingreso'], errors='coerce').fillna(0)
    df['egreso'] = pd.to_numeric(df['egreso'], errors='coerce').fillna(0)
    df['monto'] = df['ingreso'] - df['egreso']
    df['mes'] = df['fecha'].dt.month
    df['año'] = df['fecha'].dt.year
    df['semana'] = df['fecha'].dt.isocalendar().week
    return df.dropna(subset=['fecha'])

def categorizar(concepto):
    concepto = concepto.lower()
    cats = {
        'viáticos': ['viático', 'viaje', 'gasolina', 'taxi', 'vuelo', 'hotel', 'hospedaje', 'transporte', 'uber', 'combustible', 'estacionamiento', 'peaje'],
        'despensas': ['super', 'mercado', 'despensa', 'abarrote', 'fruta', 'verdura', 'carne', 'comida'],
        'servicios': ['agua', 'luz', 'gas', 'internet', 'teléfono', 'renta', 'alquiler', 'mantenimiento', 'seguro'],
        'suntuarios': ['restaurante', 'cine', 'netflix', 'spotify', 'juego', 'ocio', 'suscripción', 'café', 'bar', 'licor', 'regalo', 'comer'],
        'prestamos': ['préstamo', 'prestamo', 'crédito', 'credito', 'deuda', 'abono'],
        'trabajo': ['honorario', 'freelance', 'proyecto', 'consultoría', 'comisión', 'cliente', 'venta'],
        'sueldo': ['salario', 'sueldo', 'nómina', 'nomina'],
    }
    for cat, palabras in cats.items():
        for p in palabras:
            if p in concepto:
                return cat
    return 'otros'

def agregar_categoria(df):
    if 'categoria' not in df.columns:
        df['categoria'] = df['concepto'].apply(categorizar)
    else:
        mask = df['categoria'].isna() | (df['categoria'] == '')
        df.loc[mask, 'categoria'] = df.loc[mask, 'concepto'].apply(categorizar)
    return df

def resumen_por_periodo(df, periodo='mensual', año=None, mes=None):
    if 'categoria' not in df.columns:
        df = agregar_categoria(df)
    mask = pd.Series(True, index=df.index)
    if año:
        mask &= (df['año'] == año)
    if mes:
        mask &= (df['mes'] == mes)
    df_filtrado = df[mask].copy()
    total_ingresos = df_filtrado['ingreso'].sum()
    total_egresos = df_filtrado['egreso'].sum()
    balance = total_ingresos - total_egresos
    gastos_por_categoria = df_filtrado[df_filtrado['egreso'] > 0].groupby('categoria')['egreso'].sum().sort_values(ascending=False).to_dict()
    if periodo == 'semanal':
        df_evo = df_filtrado.copy()
        df_evo['periodo_label'] = df_evo['fecha'].dt.strftime('%d %b')
        evolucion = df_evo.groupby('periodo_label').agg({'ingreso': 'sum', 'egreso': 'sum'}).reset_index().to_dict('records')
    else:
        ultimos_12 = df[df['fecha'] >= df['fecha'].max() - pd.DateOffset(months=11)]
        ultimos_12['periodo_label'] = ultimos_12['fecha'].dt.strftime('%Y-%m')
        evolucion = ultimos_12.groupby('periodo_label').agg({'ingreso': 'sum', 'egreso': 'sum'}).reset_index().sort_values('periodo_label').to_dict('records')
    transacciones = df_filtrado.sort_values('fecha', ascending=False).head(50).to_dict('records')
    for t in transacciones:
        t['fecha'] = t['fecha'].strftime('%d/%m/%Y') if pd.notna(t['fecha']) else ''
    return {
        'total_ingresos': round(float(total_ingresos), 2),
        'total_egresos': round(float(total_egresos), 2),
        'balance': round(float(balance), 2),
        'gastos_por_categoria': {k: round(float(v), 2) for k, v in gastos_por_categoria.items()},
        'evolucion': [_clean_record(e) for e in evolucion],
        'transacciones': [_clean_record(t) for t in transacciones],
        'total_transacciones': int(len(df_filtrado)),
        'promedio_diario': round(float(total_egresos / max(len(df_filtrado['fecha'].dt.date.unique()), 1)), 2),
    }

def meses_disponibles(df):
    meses = df[['año', 'mes']].drop_duplicates().sort_values(['año', 'mes'])
    return [{'año': int(r['año']), 'mes': int(r['mes'])} for _, r in meses.iterrows()]
