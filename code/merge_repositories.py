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
        # 1. Carregar os dois DataFrames
        print(f"Carregando dados do GitHub de: {github_csv_path}")
        github_df = pd.read_csv(github_csv_path)
        
        print(f"Carregando métricas do CK de: {ck_csv_path}")
        ck_df = pd.read_csv(ck_csv_path)
        
        print("\n--- Informações Iniciais ---")
        print(f"Dados do GitHub: {github_df.shape[0]} linhas")
        print(f"Métricas do CK: {ck_df.shape[0]} linhas")
        
        # 2. Preparar a chave de junção no DataFrame do GitHub
        # A coluna 'name' está no formato 'owner/repo_name'.
        # A coluna 'repository' do CK tem apenas 'repo_name'.
        # Criamos uma chave comum para o merge.
        github_df['repo_key'] = github_df['name'].str.split('/').str[-1]
        
        # 3. Realizar a junção (merge)
        print("\nJuntando os dois conjuntos de dados...")
        # 'left' merge mantém todos os repositórios da lista do GitHub.
        # Se um repo não tiver métricas do CK, os valores ficarão como NaN.
        merged_df = pd.merge(
            left=github_df,
            right=ck_df,
            left_on='repo_key',
            right_on='repository',
            how='left'
        )
        
        # 4. Processamento Pós-Junção
        
        # a) Calcular a idade do repositório (Maturidade)
        # Converte a coluna 'createdAt' para formato de data
        merged_df['createdAt'] = pd.to_datetime(merged_df['createdAt'], errors='coerce')
        # Calcula a diferença em dias até hoje e converte para anos
        today = pd.Timestamp.now(tz='UTC')
        merged_df['age_years'] = (today - merged_df['createdAt']).dt.days / 365.25
        
        # b) Limpeza final
        # Remove colunas auxiliares e renomeia para clareza
        merged_df = merged_df.drop(columns=['repo_key', 'repository'])
        
        print("\n--- Resultado da Junção e Processamento ---")
        missing_ck_count = merged_df['cbo_median'].isnull().sum()
        if missing_ck_count > 0:
            print(f"Aviso: {missing_ck_count} repositórios não tiveram métricas do CK correspondentes.")
        
        # 5. Salvar o dataset final
        merged_df.to_csv(output_csv_path, index=False)
        
        print("\n" + "="*50)
        print(f"Dataset final criado com sucesso!")
        print(f"Arquivo salvo em: {output_csv_path}")
        print("\nAmostra do dataset final pronto para análise:")
        # Mostra colunas importantes
        cols_to_show = ['name', 'stargazers', 'releases', 'age_years', 'cbo_median', 'lcom_median', 'loc_sum']
        print(merged_df[cols_to_show].head())
        print("\nResumo do arquivo final:")
        merged_df.info()
        print("="*50)

    except FileNotFoundError as e:
        print(f"ERRO: Arquivo não encontrado. Verifique os caminhos. Detalhe: {e}")
    except Exception as e:
        print(f"ERRO INESPERADO: {e}")

    # --- COMO USAR O SCRIPT ---
if __name__ == "__main__":
    # 1. Verifique se os nomes dos arquivos estão corretos
    GITHUB_DATA_FILE = "collected_repos.csv"
    CK_METRICS_FILE = "ck_metrics.csv" # O arquivo que geramos na etapa anterior

    # 2. Nome do arquivo de saída final
    FINAL_DATASET_FILE = "full_dataset.csv"

    # Chama a função para criar o dataset completo
    createDataset(
        github_csv_path=GITHUB_DATA_FILE,
        ck_csv_path=CK_METRICS_FILE,
        output_csv_path=FINAL_DATASET_FILE
    )