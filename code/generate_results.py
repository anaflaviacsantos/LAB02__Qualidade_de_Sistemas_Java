import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
import numpy as np

# --- CONFIGURAÇÃO ---
# Caminho para o seu dataset final
DATASET_PATH = "final_dataset.csv"


# Mapeamento das Questões de Pesquisa para as colunas do dataset
PROCESS_METRICS = {
'RQ01_Popularidade': 'stargazers',
'RQ02_Maturidade': 'age_years',
'RQ03_Atividade': 'releases',
'RQ04_Tamanho': 'loc_sum'
}

# Métricas de qualidade que vamos analisar
QUALITY_METRICS = {
'CBO': 'cbo_median',
'DIT': 'dit_median',
'LCOM': 'lcom_median',
}
# --------------------

def generateGraphs(output_dir):
    """
    Função principal para carregar os dados, gerar e salvar todos os gráficos de análise.
    """
    # 1. Carregar o dataset
    try:
        df = pd.read_csv(DATASET_PATH)
        print(f"Dataset '{DATASET_PATH}' carregado com sucesso. {len(df)} linhas encontradas.")
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{DATASET_PATH}' não encontrado. Verifique o nome e o caminho do arquivo.")
        return

    # 2. Preparar os dados
    # Remove linhas onde não há métricas de qualidade (repositórios que falharam na análise do CK)
    # Isso é crucial para a análise estatística não dar erro.
    metrics_to_check = list(QUALITY_METRICS.values()) + list(PROCESS_METRICS.values())
    df_clean = df.dropna(subset=metrics_to_check)
    print(f"Removidas linhas com dados faltantes. {len(df_clean)} linhas restantes para análise.")

    # Cria a pasta de saída se ela não existir
    os.makedirs(output_dir, exist_ok=True)
    print(f"Gráficos serão salvos na pasta: '{output_dir}'")

    # 3. Gerar um gráfico para cada par de métricas (Processo vs. Qualidade)
    for rq_name, process_metric_col in PROCESS_METRICS.items():
        for quality_name, quality_metric_col in QUALITY_METRICS.items():
            
            print(f"Gerando gráfico para: {rq_name} vs {quality_name}...")
            
            # Pega os dados das duas colunas que vamos analisar
            x_data = df_clean[process_metric_col]
            y_data = df_clean[quality_metric_col]

            # 4. Calcular a Correlação de Spearman (para o ponto bônus)
            # rho: o coeficiente de correlação (-1 a 1)
            # p: o p-valor (se < 0.05, a correlação é estatisticamente significante)
            rho, p_value = spearmanr(x_data, y_data)

            # 5. Criar o Gráfico de Dispersão (Scatter Plot)
            plt.figure(figsize=(10, 6))
            
            # Usamos regplot para já incluir uma linha de tendência, que ajuda a visualizar a relação
            sns.regplot(x=x_data, y=y_data, 
                        scatter_kws={'alpha':0.3, 's':15}, # Deixa os pontos mais transparentes
                        line_kws={'color':'red', 'linewidth':2}) # Linha de tendência vermelha

            # 6. Configurar Título e Rótulos
            title = (f'{rq_name}: {process_metric_col.replace("_", " ").title()} vs. {quality_name}\n'
                    f'Correlação de Spearman (ρ): {rho:.3f} | p-valor: {p_value:.3f}')
            
            plt.title(title, fontsize=14)
            plt.xlabel(process_metric_col.replace("_", " ").title(), fontsize=12)
            plt.ylabel(f'{quality_name} ({quality_metric_col})', fontsize=12)
            plt.grid(True, linestyle='--', alpha=0.6)

            # Nota sobre escala logarítmica:
            # Para métricas como 'stargazers' e 'loc_sum', a distribuição é muito desigual.
            # Uma escala logarítmica pode ajudar a visualizar melhor os dados.
            if process_metric_col in ['stargazers', 'loc_sum', 'releases']:
                if x_data.min() > 0: # Log não funciona com zero ou valores negativos
                    plt.xscale('log')

            # 7. Salvar o gráfico
            filename = f'{rq_name}_{quality_name}.png'
            filepath = os.path.join(output_dir, filename)
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close() # Fecha a figura para liberar memória

    print("\n" + "="*50)
    print("Análise concluída! Todos os gráficos foram salvos com sucesso.")
    print("="*50)


def generateStats(output_csv):
    """
    Carrega o dataset final e calcula as estatísticas descritivas
    (média, mediana, desvio padrão, etc.) para as colunas de interesse.
    """
    try:
        df = pd.read_csv(DATASET_PATH)
        print(f"Dataset '{DATASET_PATH}' carregado com sucesso.")
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{DATASET_PATH}' não encontrado.")
        return

    columns = ['stargazers','age_years','releases','loc_sum','cbo_median','dit_median','lcom_median']

    # Limpa os dados da mesma forma que no script de gráficos para garantir consistência
    df_clean = df.dropna(subset=columns)
    print(f"{len(df_clean)} linhas serão usadas para a análise estatística.")

    # Seleciona apenas as colunas de interesse
    df_subset = df_clean[columns]

    # Usa a função .describe() do pandas, que já calcula tudo que precisamos e mais!
    stats_df = df_subset.describe()

    # A função .describe() já inclui média (mean), desvio padrão (std) e mediana (50%).
    # Vamos apenas renomear o índice '50%' para 'median' para ficar mais claro.
    stats_df = stats_df.rename(index={'50%': 'median'})

    # Seleciona apenas as linhas que você pediu (e algumas extras úteis)
    final_stats = stats_df.loc[['mean', 'median', 'std', 'min', 'max']]

    print("\n" + "="*60)
    print("Estatísticas Descritivas das Métricas Analisadas:")
    print(final_stats)
    print("="*60)

    # Salva a tabela de estatísticas em um arquivo CSV para usar no seu relatório
    try:
        final_stats.to_csv(output_csv)
        print(f"\nTabela de estatísticas salva com sucesso em: '{output_csv}'")
    except Exception as e:
        print(f"Não foi possível salvar o arquivo de estatísticas. Erro: {e}")
