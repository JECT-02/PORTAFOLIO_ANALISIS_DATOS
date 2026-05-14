import nbformat as nbf
from pathlib import Path

def create_notebook(filename: str, cells: list[tuple[str, str]]):
    nb = nbf.v4.new_notebook()
    nb_cells = []
    for cell_type, content in cells:
        if cell_type == "markdown":
            nb_cells.append(nbf.v4.new_markdown_cell(content))
        elif cell_type == "code":
            nb_cells.append(nbf.v4.new_code_cell(content))
    nb['cells'] = nb_cells
    
    with open(f"notebooks/{filename}", 'w') as f:
        nbf.write(nb, f)

# 01 Data Exploration
cells_01 = [
    ("markdown", "# 01 Data Exploration\n\nExploracion de datos bronze y visualizacion inicial."),
    ("code", "import json\nimport pandas as pd\nimport matplotlib.pyplot as plt\nfrom pathlib import Path\n\nplt.style.use('dark_background')\nbronze_dir = Path('../data/bronze')"),
    ("code", "info_files = sorted(bronze_dir.glob('stock_info_*.json'))\nwith open(info_files[-1], 'r') as f:\n    info = json.load(f)\ninfo_df = pd.DataFrame(info)\nprint('Shape:', info_df.shape)\ninfo_df.head()"),
    ("code", "info_df['sector'].value_counts().plot(kind='bar', figsize=(10,5), title='Distribucion por Sector')\nplt.show()"),
    ("code", "hist_files = list((bronze_dir / 'historical').glob('*.json'))\nprint(f'Total historical files: {len(hist_files)}')"),
]

# 02 Cleaning Pipeline
cells_02 = [
    ("markdown", "# 02 Cleaning Pipeline\n\nLimpieza de datos de bronze a silver."),
    ("code", "import sys\nsys.path.append('..')\nimport pandas as pd\nfrom src.clean_data import run_clean_pipeline\nfrom pathlib import Path\n\nsilver_dir = Path('../data/silver')"),
    ("code", "run_clean_pipeline()"),
    ("code", "prices = pd.read_parquet(silver_dir / 'prices.parquet')\nprices.head()"),
    ("code", "returns = pd.read_parquet(silver_dir / 'returns.parquet')\nreturns.head()"),
]

# 03 Feature Engineering
cells_03 = [
    ("markdown", "# 03 Feature Engineering\n\nCalculo de covarianza, correlacion, volatilidad y matriz SDP."),
    ("code", "import sys\nsys.path.append('..')\nimport pandas as pd\nimport seaborn as sns\nimport matplotlib.pyplot as plt\nfrom src.features import run_feature_pipeline\nfrom pathlib import Path\n\nplt.style.use('dark_background')\ngold_dir = Path('../data/gold')"),
    ("code", "run_feature_pipeline()"),
    ("code", "corr = pd.read_csv(gold_dir / 'correlation_matrix.csv', index_col=0)\nplt.figure(figsize=(10,8))\nsns.heatmap(corr, cmap='coolwarm', center=0)\nplt.title('Matriz de Correlacion')\nplt.show()"),
]

# 04 Monte Carlo Simulation
cells_04 = [
    ("markdown", "# 04 Monte Carlo Simulation\n\nSimulacion GBM multidimensional."),
    ("code", "import sys\nsys.path.append('..')\nimport pandas as pd\nimport matplotlib.pyplot as plt\nfrom src.simulation import run_simulation_pipeline\nfrom pathlib import Path\n\nplt.style.use('dark_background')\ngold_dir = Path('../data/gold')"),
    ("code", "run_simulation_pipeline()"),
    ("code", "sim_returns = pd.read_csv(gold_dir / 'simulated_returns_20d.csv')\nsim_returns['portfolio_return'].hist(bins=50, figsize=(10,5))\nplt.title('Distribucion de Retornos Simulados (20d)')\nplt.show()"),
]

# 05 Risk Metrics
cells_05 = [
    ("markdown", "# 05 Risk Metrics\n\nCalculo de VaR y CVaR."),
    ("code", "import sys\nsys.path.append('..')\nimport pandas as pd\nimport matplotlib.pyplot as plt\nfrom src.risk_metrics import run_risk_metrics_pipeline\nfrom pathlib import Path\n\nplt.style.use('dark_background')\ngold_dir = Path('../data/gold')"),
    ("code", "run_risk_metrics_pipeline()"),
    ("code", "metrics = pd.read_csv(gold_dir / 'risk_metrics_all.csv')\nmetrics"),
]

# 06 Backtesting
cells_06 = [
    ("markdown", "# 06 Backtesting\n\nBacktesting rolling window y test de Kupiec."),
    ("code", "import pandas as pd\nfrom pathlib import Path\n\ngold_dir = Path('../data/gold')"),
    ("code", "bt_results = pd.read_csv(gold_dir / 'backtest_results.csv')\nbt_results"),
]

create_notebook("01_data_exploration.ipynb", cells_01)
create_notebook("02_cleaning_pipeline.ipynb", cells_02)
create_notebook("03_feature_engineering.ipynb", cells_03)
create_notebook("04_monte_carlo_simulation.ipynb", cells_04)
create_notebook("05_risk_metrics.ipynb", cells_05)
create_notebook("06_backtesting.ipynb", cells_06)

print("Notebooks created successfully.")
