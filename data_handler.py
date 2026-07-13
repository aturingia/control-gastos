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
    df['id'] = range(len(df))
    return df.dropna(subset=['fecha'])

CATEGORIAS = [
    'viáticos', 'despensas', 'servicios', 'suntuarios', 'prestamos',
    'trabajo', 'sueldo', 'refacciones', 'alquiler', 'e-commerce',
    'insumos', 'otros',
]

def categorizar(concepto):
    concepto = concepto.lower()
    cats = {
        'viáticos': ['viático', 'viaje', 'gasolina', 'taxi', 'vuelo', 'hotel', 'hospedaje', 'transporte', 'uber', 'combustible', 'estacionamiento', 'peaje'],
        'despensas': ['super', 'mercado', 'despensa', 'abarrote', 'fruta', 'verdura', 'carne', 'comida'],
        'servicios': ['agua', 'luz', 'gas', 'internet', 'teléfono', 'mantenimiento', 'seguro'],
        'suntuarios': ['restaurante', 'cine', 'netflix', 'spotify', 'juego', 'ocio', 'suscripción', 'café', 'bar', 'licor', 'regalo', 'comer'],
        'prestamos': ['préstamo', 'prestamo', 'crédito', 'credito', 'deuda', 'abono'],
        'trabajo': ['honorario', 'freelance', 'proyecto', 'consultoría', 'comisión', 'cliente', 'venta'],
        'sueldo': ['salario', 'sueldo', 'nómina', 'nomina'],
        'refacciones': ['refacción', 'refaccion', 'repuesto', 'taller', 'mecánico', 'mecanico', 'llanta', 'reparación', 'reparacion'],
        'alquiler': ['renta', 'alquiler'],
        'e-commerce': ['ecommerce', 'e-commerce', 'amazon', 'mercado libre', 'mercadolibre', 'shop', 'tienda', 'compra', 'envío', 'envio', 'pedido', 'aliexpress', 'ebay'],
        'insumos': ['insumo', 'material', 'papelería', 'papeleria', 'oficina', 'suministro', 'consumible', 'tinta', 'toner', 'utensilio'],
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

def exportar_csv(df):
    cols = ['fecha', 'concepto', 'ingreso', 'egreso', 'categoria']
    out = df[cols].copy()
    out['fecha'] = out['fecha'].dt.strftime('%d/%m/%Y')
    return out.to_csv(index=False, encoding='utf-8-sig')

def add_transaccion(df, fecha, concepto, ingreso, egreso, categoria=None):
    new_id = int(df['id'].max() + 1) if len(df) else 0
    parsed = pd.to_datetime(fecha, dayfirst=True, errors='coerce')
    if pd.isna(parsed):
        raise ValueError('Fecha inválida')
    cat = categoria if categoria else categorizar(concepto)
    row = {
        'id': new_id,
        'fecha': parsed,
        'concepto': concepto,
        'ingreso': float(ingreso),
        'egreso': float(egreso),
        'categoria': cat,
        'monto': float(ingreso) - float(egreso),
        'mes': parsed.month,
        'año': parsed.year,
        'semana': parsed.isocalendar().week,
    }
    new_df = pd.DataFrame([row])
    return pd.concat([df, new_df], ignore_index=True)

def update_transaccion(df, id, fecha, concepto, ingreso, egreso, categoria=None):
    df = df.copy()
    mask = df['id'] == id
    if not mask.any():
        raise ValueError(f'Transacción con id {id} no encontrada')
    parsed = pd.to_datetime(fecha, dayfirst=True, errors='coerce')
    if pd.isna(parsed):
        raise ValueError('Fecha inválida')
    cat = categoria if categoria else categorizar(concepto)
    df.loc[mask, 'fecha'] = parsed
    df.loc[mask, 'concepto'] = concepto
    df.loc[mask, 'ingreso'] = float(ingreso)
    df.loc[mask, 'egreso'] = float(egreso)
    df.loc[mask, 'categoria'] = cat
    df.loc[mask, 'monto'] = float(ingreso) - float(egreso)
    df.loc[mask, 'mes'] = parsed.month
    df.loc[mask, 'año'] = parsed.year
    df.loc[mask, 'semana'] = parsed.isocalendar().week
    return df

def delete_transaccion(df, id):
    df = df[df['id'] != id].copy()
    df.reset_index(drop=True, inplace=True)
    return df
