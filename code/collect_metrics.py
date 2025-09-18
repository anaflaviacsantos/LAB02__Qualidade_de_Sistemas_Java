import pandas as pd
import os
import git
import subprocess
import shutil
import stat  


# Configurações de caminhos
CK_JAR_PATH = 'C:\\Users\\dtiDigital\\Documents\\Tools\\ck\\target\\ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar' # Ajuste se necessário
TEMP_CLONE_DIR = 'C:\\temp_clones' 
METRICS_OUTPUT_DIR = 'C:\\ck_collected_metrics' 

# Configuração de métricas e suas agregações
METRICS = {
'cbo': ['median', 'mean'],
'dit': ['median', 'mean'],
'lcom': ['median', 'mean'],
'loc': ['sum']
}


# Função de tratamento de erro para shutil.rmtree
# Ela é chamada quando rmtree falha
# Altera a permissão do arquivo para escrita e tenta novamente
def handle_remove_readonly(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)


# Função que clona um único repositório e coleta suas métricas
# Recebe a URL do repositório e clona para a pasta TEMP_CLONE_DIR
# Depois executa o CK e salva as métricas na pasta METRICS_OUTPUT_DIR
# Ao final apaga o repositório clonado
#   :param str repo_url: A URL do repositório a ser processado.
#   :param str clone_path: O caminho para o repositório clonado.
#   :param str output_path: O caminho para salvar as métricas coletadas.
def collectMetricsPerRepository(repo_url):
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    clone_path = os.path.join(TEMP_CLONE_DIR, repo_name)

    print(f"--- Processando: {repo_name} ---")
    
    if os.path.exists(clone_path):
        shutil.rmtree(clone_path, onexc=handle_remove_readonly)

    try:
        git.Repo.clone_from(
        repo_url, 
        clone_path, 
        depth=1,             # Pega apenas o último commit
        single_branch=True,  # Pega apenas a branch principal
        no_tags=True         # Ignora as tags de versão
        )
        print("Clonagem ok")
        
        repo_output_path = os.path.join(METRICS_OUTPUT_DIR, repo_name)
        os.makedirs(repo_output_path, exist_ok=True)

        command = ['java', '-jar', CK_JAR_PATH, clone_path, 'true', '0', 'false', repo_output_path]
        
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Análise ok")
        print(f"Métricas salvas")

    except (git.exc.GitCommandError, subprocess.CalledProcessError, Exception) as e:
        print(f"   ERRO ao processar {repo_name}: {e}")
        if isinstance(e, subprocess.CalledProcessError):
            print(f"   Detalhe do erro do CK: {e.stderr}")
        
    finally:
        if os.path.exists(clone_path):
            shutil.rmtree(clone_path, onexc=handle_remove_readonly)
            print("Exclusão ok")
            
    print(f"Finalizado: {repo_name}")


# Função que gerencia a coleta de métricas a partir do arquivo CSV de repositórios
# Recebe o caminho do CSV e um limite opcional de repositórios a processar
# Lê o CSV, itera sobre os repositórios e chama a função de coleta para cada um
# Salva os arquivos csv do CK
#   :param str csv_path: O caminho para o arquivo CSV contendo os repositórios.
#   :param int limit: O número máximo de repositórios a serem processados (opcional).
def runMetricsCollection(csv_path, limit=None):
    os.makedirs(TEMP_CLONE_DIR, exist_ok=True)
    os.makedirs(METRICS_OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(CK_JAR_PATH):
        print(f"Arquivo CK não encontrado em: {CK_JAR_PATH}")
        return
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Arquivo CSV não encontrado em: {csv_path}")
        return

    if limit is not None:
        df_to_process = df.head(limit)
    else:
        df_to_process = df

    for index, row in df_to_process.iterrows():
        repo_url = row['url']
        collectMetricsPerRepository(repo_url)

    print("Coleta finalizada com sucesso")


# Função que agrega os arquivos CSV do CK em um único arquivo CSV
# Percorre a pasta METRICS_OUTPUT_DIR, lê os arquivos '...class.csv'
# Aplica as agregações configuradas em METRICS
# Salva o resultado em output_csv_path
#   :param str base_dir: O caminho para a pasta que contém os arquivos do CK
#   :param str output_csv_path: O caminho onde o arquivo CSV final será salvo.
def saveCKMetrics(base_dir: str, output_csv_path: str):
    all_results = []

    class_files = [f for f in os.listdir(base_dir) if f.endswith('class.csv')]

    for filename in class_files:
        repo_name = filename.removesuffix('class.csv')
        full_path = os.path.join(base_dir, filename)
        
        print(f"Processando: {repo_name}")
        
        try:
            class_df = pd.read_csv(full_path)
            if class_df.empty:
                print(f"Arquivo {filename} vazio")
                continue

            repo_metrics = {'repository': repo_name}
            
            for metric, agg_methods_list in METRICS.items():
                if metric not in class_df.columns:
                    print(f"  -> Aviso: Coluna '{metric}' não encontrada em {filename}")
                    continue
                
                for agg_method in agg_methods_list:
                    new_column_name = f'{metric}_{agg_method}'
                    
                    if agg_method == 'median':
                        repo_metrics[new_column_name] = class_df[metric].median()
                    elif agg_method == 'mean':
                        repo_metrics[new_column_name] = class_df[metric].mean()
                    elif agg_method == 'sum':
                        repo_metrics[new_column_name] = class_df[metric].sum()
            
            all_results.append(repo_metrics)

        except Exception as e:
            print(f"  -> ERRO INESPERADO ao processar {filename}: {e}")
            continue

    if not all_results:
        print("Nenhum dado foi processado")
        return

    final_df = pd.DataFrame(all_results)
    final_df.to_csv(output_csv_path, index=False)

    print(f"Concluído com sucesso")
    
    