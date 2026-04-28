# Auditoría de Fugitividad de Margen y Optimización de Inventario Crítico

## Objetivo
Identificar qué productos y categorías están destruyendo el flujo de caja de la empresa mediante el análisis de la **Edad del Inventario** y la **Rentabilidad Real Post-Retorno**.

## Dataset
- **Fuente:** BigQuery público — `bigquery-public-data.thelook_ecommerce`
- **Tablas principales:** `order_items`, `products`, `inventory_items`, `orders`
- **Documentación completa:** [`DB_documentation/documentacion.md`](DB_documentation/documentacion.md)

## Estructura del Proyecto

```
OPTIMIZACION-INVENTARIO/
│
├── .env                          # Variables de entorno (PROJECT_ID, credenciales)
├── claves/                       # JSON de servicio de Google Cloud (NO subir a git)
├── DB_documentation/             # Documentación del dataset y diagrama ERD
│   ├── documentacion.md
│   └── erd_thelook.html
│
├── notebooks/
│   ├── 01_extraccion.ipynb       # Conexión a BigQuery y extracción del dataset maestro
│   ├── 02_limpieza.ipynb         # Limpieza, imputación y feature engineering
│   ├── 03_analisis_outliers.ipynb # Detección de outliers (IQR precios, Z-Score inventario)
│   ├── 04_analisis_estadistico.ipynb # Correlación, T-Test, ANOVA
│   └── 05_segmentacion_accion.ipynb  # Cuadrante de Acción de Inventario + conclusiones
│
├── data/                         # Datos intermedios exportados (CSV/Parquet)
│   └── .gitkeep
│
├── outputs/                      # Gráficos y tablas exportadas
│   └── .gitkeep
│
└── README.md                     # Este archivo
```

## Fases del Proyecto

### Fase 1 — Extracción (`01_extraccion.ipynb`)
- Conexión a BigQuery con credenciales de servicio
- Query maestro: JOIN de `order_items` + `products` + `inventory_items`
- Exportación del dataset maestro a `data/`

### Fase 2 — Limpieza (`02_limpieza.ipynb`)
- Imputación lógica de fechas (`shipped_at`, `returned_at`)
- Cálculo de `inventory_age` (días en almacén)
- Cálculo de margen de contribución: `sale_price - cost`
- Exportación del dataset limpio

### Fase 3 — Análisis de Outliers (`03_analisis_outliers.ipynb`)
- **IQR sobre `sale_price`** agrupado por categoría → detectar ventas por debajo del costo
- **Z-Score sobre `inventory_age`** → identificar "Stock Zombie" (Z > 3)
- Visualizaciones: boxplots, distribuciones

### Fase 4 — Análisis Estadístico (`04_analisis_estadistico.ipynb`)
- Correlación de Pearson: descuento vs velocidad de venta
- T-Test: tasa de devolución en envío lento vs envío normal
- Interpretación de p-valores y significancia

### Fase 5 — Segmentación y Acción (`05_segmentacion_accion.ipynb`)
- Cuadrante de Acción de Inventario:
  - **Estrellas:** Alta rotación + Margen > 20%
  - **Drenaje de Caja:** Alta rotación + Tasa de Retorno > 15%
  - **Stock Zombie:** Z-score > 2 en edad + Margen bajo
  - **Errores de Precio:** `sale_price` < `cost`
- Recomendaciones tácticas por segmento
- Conclusiones finales

## Tecnologías
- Python 3.12
- BigQuery (google-cloud-bigquery)
- Pandas, NumPy, SciPy
- Matplotlib, Seaborn
