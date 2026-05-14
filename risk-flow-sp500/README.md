# Risk-Flow S&P 500

Proyecto de Simulacion Monte Carlo Multidimensional para Gestion de Riesgo de Portafolio.

## Descripcion

Este proyecto implementa un motor de riesgo cuantitativo completo que descarga datos historicos y de perfil de acciones del S&P 500 via Financial Modeling Prep (FMP) API, procesa y limpia los datos en una arquitectura Medallion (Bronze, Silver, Gold), simula miles de escenarios futuros utilizando el Movimiento Browniano Geometrico (GBM) correlacionado, y calcula metricas de riesgo clave como Value at Risk (VaR) y Conditional Value at Risk (CVaR). Los resultados se presentan en un frontend interactivo escrito en HTML, CSS y JavaScript puro.

## Estructura del Proyecto (Medallion Architecture)

- **Bronze Layer (`data/bronze/`)**: Almacena respuestas JSON crudas directamente de la API.
- **Silver Layer (`data/silver/`)**: Almacena datos limpios y normalizados (precios ajustados, retornos logaritmicos).
- **Gold Layer (`data/gold/`)**: Almacena features calculadas (covarianzas, correlaciones, simulaciones, metricas de riesgo).

## Modelo Matematico

### Movimiento Browniano Geometrico (GBM) Correlacionado

El precio futuro de cada activo i en el horizonte h se modela mediante la siguiente ecuacion diferencial estocastica discretizada:

`S_{i,h}^{(s)} = S_{i,0} * exp( (mu_i - sigma_i^2 / 2) * dt + sigma_i * sqrt(dt) * X_{i,s} )`

Donde:
- `S_{i,0}` es el ultimo precio conocido.
- `mu_i` es el retorno esperado (drift), el cual asumimos nulo (0.0) para horizontes de corto plazo.
- `sigma_i` es la volatilidad anualizada historica.
- `dt` es la fraccion de ano correspondiente al horizonte h (`h / 252`).
- `X_{i,s}` es un vector de choques correlacionados.

Para generar los choques correlacionados, se utiliza la factorizacion de Cholesky de la matriz de covarianza empirica (con correccion de Ledoit-Wolf en caso de no ser Semidefinida Positiva).

### Metricas de Riesgo

- **Value at Risk (VaR_alpha)**: El cuantil de las perdidas simuladas. Representa el nivel de perdida tal que existe una probabilidad alpha de excederlo.
- **Conditional Value at Risk (CVaR_alpha)**: Tambien conocido como Expected Shortfall, es el promedio de las perdidas condicionadas a que dichas perdidas excedan el VaR_alpha.

## Limitaciones del Modelo

1. El modelo asume volatilidad constante (homocedasticidad). En la realidad, los mercados exhiben agrupamiento de volatilidad (efecto GARCH).
2. Se asume que los retornos siguen una distribucion gaussiana. Esto subestima las colas gordas de los mercados financieros; los eventos extremos ocurren con mayor frecuencia de la modelada.
3. El modelo no captura saltos (jumps) abruptos de precios debidos a noticias inesperadas, reportes de ganancias o shocks macroeconomicos.
4. Las correlaciones se asumen constantes y calibradas estaticamente con un ano de datos. En tiempos de crisis, las correlaciones tienden a incrementarse significativamente (contagio).
5. Se asume un drift nulo (0.0). Para horizontes de gestion de riesgo de corto plazo esto es adecuado, pero pierde precision en horizontes largos.
6. Los datos tienen un delay y son de frecuencia diaria (EOD). Este modelo esta disenado para gestion de riesgo tactica, no para operaciones intradiarias o HFT.
7. Las llamadas a la API de FMP en la version gratuita pueden estar limitadas a 250 peticiones diarias y ciertos endpoints pueden restringir retiros de datos mas profundos o masivos.
8. El backtesting tipo rolling window consume una porcion de datos. Si la ventana de datos totales es pequena, el poder estadistico del test de Kupiec disminuye.

## Instrucciones de Ejecucion

### Prerequisitos

- Python 3.10 o superior.
- API Key de Financial Modeling Prep.

### Instalacion

1. Clonar el repositorio.
2. Instalar las dependencias en un entorno virtual:
   `pip install -r requirements.txt`
3. Crear un archivo `.env` en la raiz del proyecto con el siguiente contenido:
   ```
   API_KEY=tu_api_key_aqui
   BASE_URL=https://financialmodelingprep.com/stable
   ```

### Ejecucion del Pipeline

Ejecutar los scripts secuencialmente:

1. **Extraccion de Datos**:
   `python -m src.fetch_data`
2. **Limpieza de Datos**:
   `python -m src.clean_data`
3. **Generacion de Features**:
   `python -m src.features`
4. **Simulacion Monte Carlo**:
   `python -m src.simulation`
5. **Calculo de Metricas de Riesgo**:
   `python -m src.risk_metrics`
6. **Generacion de Datos para el Frontend**:
   `python scripts/generate_frontend_data.py`

*(Opcional)* Existen cuadernos de Jupyter en la carpeta `notebooks/` para ejecutar y visualizar cada fase interactiva. Ejecutar el script `python scripts/generate_notebooks.py` generara estos cuadernos a partir de plantillas programaticas si no existen.

### Lanzar el Frontend

Dado que la aplicacion web realiza un `fetch()` a un archivo JSON local, es posible que el navegador bloquee la peticion por politicas de CORS al abrir directamente el archivo `index.html`. Para visualizarlo correctamente:

1. Iniciar un servidor HTTP local en el directorio del proyecto:
   `python -m http.server 8000`
2. Abrir en un navegador web: `http://localhost:8000/frontend/`
