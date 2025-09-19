import pandas as pd
from datetime import datetime

def createDataset(github_csv_path: str, ck_csv_path: str, output_csv_path: str):
    """
    Junta os dados do GitHub com as métricas do CK e calcula métricas derivadas
    como a idade do repositório, criando um dataset final pronto para análise.

    Args:
        github_csv_path (str): Caminho para o arquivo com dados do GitHub (collected_repos.csv).
        ck_csv_path (str): Caminho para o arquivo com métricas agregadas do CK (ck_metrics.csv).
        output_csv_path (str): Caminho para salvar o arquivo CSV final combinado.
    """
    try:
        print(f"Carregando dados do GitHub de: {github_csv_path}")
        github_df = pd.read_csv(github_csv_path)
        
        print(f"Carregando métricas do CK de: {ck_csv_path}")
        ck_df = pd.read_csv(ck_csv_path)
        
        print("\n--- Informações Iniciais ---")
        print(f"Dados do GitHub: {github_df.shape[0]} linhas")
        print(f"Métricas do CK: {ck_df.shape[0]} linhas")
        
        github_df['repo_key'] = github_df['name'].str.split('/').str[-1]
        
        print("\nJuntando os dois conjuntos de dados...")
        merged_df = pd.merge(
            left=github_df,
            right=ck_df,
            left_on='repo_key',
            right_on='repository',
            how='left'
        )
        
        merged_df['createdAt'] = pd.to_datetime(merged_df['createdAt'], errors='coerce')
        today = pd.Timestamp.now(tz='UTC')
        merged_df['age_years'] = (today - merged_df['createdAt']).dt.days / 365.25
        
        merged_df = merged_df.drop(columns=['repo_key', 'repository'])
        
        print("\n--- Resultado da Junção e Processamento ---")
        missing_ck_count = merged_df['cbo_median'].isnull().sum()
        if missing_ck_count > 0:
            print(f"Aviso: {missing_ck_count} repositórios não tiveram métricas do CK correspondentes.")
        
        merged_df.to_csv(output_csv_path, index=False)
        
        print("\n" + "="*50)
        print(f"Dataset final criado com sucesso!")
        print(f"Arquivo salvo em: {output_csv_path}")
        print("\nAmostra do dataset final pronto para análise:")
        cols_to_show = ['name', 'stargazers', 'releases', 'age_years', 'cbo_median', 'lcom_median', 'loc_sum']
        print(merged_df[cols_to_show].head())
        print("\nResumo do arquivo final:")
        merged_df.info()
        print("="*50)

    except FileNotFoundError as e:
        print(f"ERRO: Arquivo não encontrado. Verifique os caminhos. Detalhe: {e}")
    except Exception as e:
        print(f"ERRO INESPERADO: {e}")

    