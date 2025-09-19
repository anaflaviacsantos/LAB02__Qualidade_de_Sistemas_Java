import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
import numpy as np

# Configurações
DATASET_PATH = "final_dataset.csv"
PROCESS_METRICS = {
'RQ01_Popularidade': 'stargazers',
'RQ02_Maturidade': 'age_years',
'RQ03_Atividade': 'releases',
'RQ04_Tamanho': 'loc_sum'
}
QUALITY_METRICS = {
'CBO': 'cbo_median',
'DIT': 'dit_median',
'LCOM': 'lcom_median',
}

# Função para gerar gráficos de dispersão e calcular correlações
# Gera um gráfico para cada par de métricas (Processo vs. Qualidade)
# Salva os gráficos na pasta especificada
#  :param str output_dir: O diretório onde os gráficos serão salvos.
def generateGraphs(output_dir):
    try:
        df = pd.read_csv(DATASET_PATH)
        print(f"Dataset '{DATASET_PATH}' carregado com sucesso. {len(df)} linhas encontradas.")
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{DATASET_PATH}' não encontrado. Verifique o nome e o caminho do arquivo.")
        return

    metrics_to_check = list(QUALITY_METRICS.values()) + list(PROCESS_METRICS.values())
    df_clean = df.dropna(subset=metrics_to_check)
    print(f"Removidas linhas com dados faltantes. {len(df_clean)} linhas restantes para análise.")

    os.makedirs(output_dir, exist_ok=True)
    print(f"Gráficos serão salvos na pasta: '{output_dir}'")

    for rq_name, process_metric_col in PROCESS_METRICS.items():
        for quality_name, quality_metric_col in QUALITY_METRICS.items():
            
            print(f"Gerando gráfico para: {rq_name} vs {quality_name}...")
            
            x_data = df_clean[process_metric_col]
            y_data = df_clean[quality_metric_col]

            rho, p_value = spearmanr(x_data, y_data)

            plt.figure(figsize=(10, 6)) 
            sns.regplot(x=x_data, y=y_data, 
                        scatter_kws={'alpha':0.3, 's':15}, 
                        line_kws={'color':'red', 'linewidth':2}) 

            title = (f'{rq_name}: {process_metric_col.replace("_", " ").title()} vs. {quality_name}\n'
                    f'Correlação de Spearman (ρ): {rho:.3f} | p-valor: {p_value:.3f}')
            
            plt.title(title, fontsize=14)
            plt.xlabel(process_metric_col.replace("_", " ").title(), fontsize=12)
            plt.ylabel(f'{quality_name} ({quality_metric_col})', fontsize=12)
            plt.grid(True, linestyle='--', alpha=0.6)

            if process_metric_col in ['stargazers', 'loc_sum', 'releases']:
                if x_data.min() > 0: 
                    plt.xscale('log')

            
            filename = f'{rq_name}_{quality_name}.png'
            filepath = os.path.join(output_dir, filename)
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close() 



# Função para gerar estatísticas descritivas das métricas no dataset final
# Calcula média, mediana, desvio padrão, mínimo e máximo
# Salva os resultados em um arquivo CSV
#   :param str output_csv: O caminho onde o arquivo CSV com as estatísticas será salvo.
def generateStats(output_csv):
    try:
        df = pd.read_csv(DATASET_PATH)
        print(f"Dataset '{DATASET_PATH}' carregado com sucesso.")
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{DATASET_PATH}' não encontrado.")
        return

    columns = ['stargazers','age_years','releases','loc_sum','cbo_median','dit_median','lcom_median']

    df_clean = df.dropna(subset=columns)
    print(f"{len(df_clean)} linhas serão usadas para a análise estatística.")

    df_subset = df_clean[columns]

    stats_df = df_subset.describe()

    stats_df = stats_df.rename(index={'50%': 'median'})

    final_stats = stats_df.loc[['mean', 'median', 'std', 'min', 'max']]

    print("\n" + "="*60)
    print("Estatísticas Descritivas das Métricas Analisadas:")
    print(final_stats)
    print("="*60)

    try:
        final_stats.to_csv(output_csv)
        print(f"\nTabela de estatísticas salva com sucesso em: '{output_csv}'")
    except Exception as e:
        print(f"Não foi possível salvar o arquivo de estatísticas. Erro: {e}")
