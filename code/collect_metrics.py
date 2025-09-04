import pandas as pd
import os
import git
import subprocess
import shutil
import stat  


# Configurações
CK_JAR_PATH = 'C:\\Users\\dtiDigital\\Documents\\Tools\\ck\\target\\ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar' # Ajuste se necessário
TEMP_CLONE_DIR = 'temp_repo_cloned' # Nome da pasta temporária corrigido
METRICS_OUTPUT_DIR = 'ck_collected_metrics' # Nome da pasta de métricas corrigido


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

    try:
        git.Repo.clone_from(repo_url, clone_path)
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
            shutil.rmtree(clone_path, onerror=handle_remove_readonly)
            print("Exclusão ok")
            
    print(f"Finalizado: {repo_name}")

# Função que gerencia a coleta de métricas a partir do arquivo CSV de repositórios
# Recebe o caminho do CSV e um limite opcional de repositórios a processar
# Lê o CSV, itera sobre os repositórios e chama a função de coleta para cada um
# Salva os arquivos csv do CK
#   :param str csv_path: O caminho para o arquivo CSV contendo os repositórios.
#   :param int limit: O número máximo de repositórios a serem processados (opcional).
def run_metrics_collection(csv_path, limit=None):
    os.makedirs(TEMP_CLONE_DIR, exist_ok=True)
    os.makedirs(METRICS_OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(CK_JAR_PATH):
        print(f"ERRO CRÍTICO: Arquivo CK não encontrado em: {CK_JAR_PATH}")
        return
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"ERRO CRÍTICO: Arquivo CSV não encontrado em: {csv_path}")
        return

    if limit is not None:
        df_to_process = df.head(limit)
    else:
        df_to_process = df

    for index, row in df_to_process.iterrows():
        repo_url = row['url']
        collectMetricsPerRepository(repo_url)

    print("Coleta finalizada com sucesso")


   