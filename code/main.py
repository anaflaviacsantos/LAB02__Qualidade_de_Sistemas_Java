import os
import requests
from dotenv import load_dotenv
import csv
import collect_metrics
import merge_repositories
import generate_results

# Carrega o token do GitHub a partir de uma variável de ambiente para maior proteção
load_dotenv()
ACCESS_TOKEN = os.getenv('GITHUB_TOKEN')
if not ACCESS_TOKEN:
    raise ValueError("Token do GitHub não encontrado")

# Configurações da API
API_URL = 'https://api.github.com/graphql'
REQUEST_HEADERS = {"Authorization" : f"token {ACCESS_TOKEN}"}
QUERY = """
query ($searchQuery: String!, $reposPerPage: Int!, $cursor: String) {
  search(query: $searchQuery, type: REPOSITORY, first: $reposPerPage, after: $cursor) {
    repositoryCount
    edges {
      node {
        ... on Repository {
          nameWithOwner
          primaryLanguage {
            name
          }
          url
          stargazerCount
          createdAt
          releases {
            totalCount
          }
        }
      }
    }
    pageInfo {
      endCursor
      hasNextPage
    }
  }
}
"""

# Função para obter uma página de repositórios 
# Esta função atua como a camada de comunicação com a API. 
# Monta o payload da requisição com as variáveis necessárias e trata a resposta. 
# Retorna os dados em formato JSON ou lança uma exceção em caso de falha.
#   :param str query: A string de busca para a API.
#   :param int repos_per_page: O número de repositórios a serem buscados nesta página.
#   :param str or None cursor: O cursor da página anterior para continuar a paginação.
def getRepositories(query, repos_per_page, cursor):
    
    variables = {
        "searchQuery": query,
        "reposPerPage": repos_per_page,
        "cursor": cursor
    }
    payload = {"query": QUERY, "variables": variables}
    
    response = requests.post(url=API_URL, headers=REQUEST_HEADERS, json=payload)
    
    if response.status_code == 200:
        json_response = response.json()
        if "errors" in json_response:
            raise Exception(f"Erro na resposta da API: {json_response['errors']}")
        return json_response
    else:
        raise Exception(f"Falha na requisição: Status {response.status_code}\n{response.text}")


# Função que utiliza a função getRepositories para obter os repositórios e extrair as informações desejadas usando paginação
# Cria um loop que continua enquanto o número de repositórios coletados for menor que o número total de repositórios
# Coleta os repositórios em páginas com 20 repositórios por página 
# Para cada repositório coletado suas informações são escritas em formato json
# O loop continua até não haver uma nova página com mais 20 repositórios para serem lidas
# Retorna o dicionário com o número total de repositórios coletados
#   :param int num_repos: O número total de repositórios que devem ser coletados.

def getInformation(num_repos):
    
    collected_repos = []
    cursor = None  
    repos_per_page = 10
    query = "language:java stars:>1 sort:stars-desc"


    while len(collected_repos) < num_repos:
        json_response = getRepositories(query, repos_per_page, cursor)
        
        edges = json_response["data"]["search"]["edges"]
        page_info = json_response["data"]["search"]["pageInfo"]
        
        for edge in edges:
            if len(collected_repos) >= num_repos:
                break
            
            node = edge["node"]
            
            this_repo = {
                'name': node["nameWithOwner"],
                'url': node["url"],
                'stargazers': node["stargazerCount"],
                'createdAt': node["createdAt"],
                'releases': node["releases"]["totalCount"],
                'primaryLanguage': node["primaryLanguage"]["name"] if node["primaryLanguage"] else None
            }
            collected_repos.append(this_repo)


        if page_info["hasNextPage"]:
            cursor = page_info["endCursor"]
        else:
            break 
            
    return collected_repos


# Função para salvar os dados coletados em um arquivo CSV
# Esta função recebe uma lista de dicionários contendo as informações dos repositórios e o nome do arquivo CSV a ser criado.
# Usa a biblioteca csv do Python para escrever os dados no arquivo.
#   :param list repo_list: A lista de dicionários contendo os dados dos repositórios.
#   :param str filename: O nome do arquivo CSV a ser criado.
def saveToCSV(repo_list, filename='collected_repos.csv'):

    headers = repo_list[0].keys()

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            
            writer.writeheader()
            writer.writerows(repo_list)

    except IOError as e:
        print(f"\nOcorreu um erro ao salvar o arquivo CSV: {e}")


if __name__ == '__main__':
    # try:
    #     num_repositories = 1000 
    #     collected_repos = getInformation(num_repositories)
  
    #     if collected_repos:
    #         saveToCSV(collected_repos, f'collected_repos.csv')

    # except Exception as e:
    #     print(f"\nO script falhou: {e}")
        
    collect_metrics.runMetricsCollection(csv_path='collected_repos.csv')

    # CK_csv_path = 'C:\\Users\\dtiDigital\\Desktop\\ck_collected_metrics'
    
    # collect_metrics.saveCKMetrics(
    #     CK_csv_path,
    #     'ck_metrics.csv'
    # )
    
    # merge_repositories.createDataset(
    #     'collected_repos.csv',
    #     'ck_metrics.csv',
    #     'final_dataset.csv'
    # )
    
    #generate_results.generateGraphs('results')
    #generate_results.generateStats('results/stats.csv')

