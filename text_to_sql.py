import streamlit as st
import mysql.connector
import psycopg2
# Usado pela biblioteca LangChain para se conectar com o banco de dados.
from sqlalchemy import create_engine
# Ferramenta da LangChain que se conecta ao banco de dados e extrai informações sobre schema (tabelas, colunas).
from langchain_community.utilities import SQLDatabase
# Classe da LangChain para interagir com os modelos de linguagem da Google, como o Gemini.
from langchain_google_genai import ChatGoogleGenerativeAI
# Função da LangChain que constrói a "cadeia" responsável por converter texto em SQL.
from langchain.chains import create_sql_query_chain
# Lógica de Prompt
from langchain_core.prompts import PromptTemplate
# Biblioteca para manipulação de dados, usada para exibir os resultados em uma tabela formatada.
import pandas as pd
# Módulo do Python para interagir com o sistema operacional, usado para buscar a chave da API do ambiente.
import os
# Módulo de expressões regulares, essencial para limpar e formatar a saída de texto da IA.
import re

# Funções de Conexão com o Banco de Dados 
def connect_to_mysql(host, user, password, database):
    """
    Tenta estabelecer uma conexão com um banco de dados MySQL.
    Retorna o objeto de conexão se bem-sucedido, ou None em caso de falha.
    """
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        return conn
    except mysql.connector.Error as err:
        # Exibe uma mensagem de erro no Streamlit se a conexão falhar.
        st.error(f"Falha ao conectar ao MySQL: {err}")
        return None

def connect_to_postgresql(host, user, password, database, port=5432):
    """
    Tenta estabelecer uma conexão com um banco de dados PostgreSQL.
    Retorna o objeto de conexão se bem-sucedido, ou None em caso de falha.
    """
    try:
        conn = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )
        return conn
    except psycopg2.Error as err:
        # Exibe uma mensagem de erro no Streamlit se a conexão falhar.
        st.error(f"Falha ao conectar ao PostgreSQL: {err}")
        return None

# Inicialização do Motor Text-to-SQL
@st.cache_resource(show_spinner="Inicializando LLM...")
def initialize_text_to_sql_gemini(_db_uri, google_api_key, db_dialect):
    """
    Prepara e inicializa a cadeia Text-to-SQL usando a API do Google Gemini.
    Esta função é cacheada pelo Streamlit para evitar recargas desnecessárias do modelo.
    """
    try:
        # Cria um objeto SQLDatabase da LangChain a partir da URI do banco de dados.
        # sample_rows_in_table_info=5 ajuda o LLM a entender o conteúdo das tabelas.
        db = SQLDatabase.from_uri(_db_uri, sample_rows_in_table_info=5)
        
        # Inicializa o modelo Gemini-1.5-flash-latest com a chave da API.
        # temperature=0.0 é usado para tornar as respostas do LLM mais determinísticas e menos criativas.
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", google_api_key=google_api_key, temperature=0.0)

        # INÍCIO DA LÓGICA DE PROMPT
        PROMPT_TEMPLATE = """Você é um tradutor de linguagem natural para SQL. Sua tarefa é gerar uma consulta SQL para responder a uma pergunta do usuário, com base no schema do banco de dados fornecido.

**Instruções Cruciais:**
1.  Gere a consulta SQL no dialeto **{dialect}**.
2.  A consulta DEVE ser funcional e sintaticamente correta para o dialeto especificado.
3.  **Certifique-se de que todas as condições de JOIN sejam válidas e baseadas em colunas existentes em AMBAS as tabelas unidas.**
4.  **Sempre utilize aliases (AS) para colunas de mesmo nome que venham de tabelas diferentes, para evitar duplicidade no resultado (ex: SELECT t1.nome AS nome_tabela1, t2.nome AS nome_tabela2).**
5.  **NÃO** inclua explicações, comentários, formatação markdown (como ```sql) ou qualquer texto além da consulta SQL pura. Responda **APENAS** com a consulta SQL.
6.  Para consultas que retornam várias linhas (SELECT), inclua sempre a cláusula LIMIT {top_k} para limitar o número de resultados.
7.  Certifique-se de que todas as tabelas e colunas referenciadas existam no schema fornecido.

**Schema da Tabela:**
{table_info}

**Pergunta do Usuário:**
{input}

**Consulta SQL:**
"""
        
        # Cria um objeto PromptTemplate a partir do template definido, especificando as variáveis de entrada.
        prompt = PromptTemplate(
            input_variables=["input", "table_info", "dialect", "top_k"], 
            template=PROMPT_TEMPLATE
        )
        # FIM DA LÓGICA DE PROMPT
        
        # Obtém os nomes das tabelas que o LLM pode usar, a partir do objeto SQLDatabase.
        usable_tables = db.get_usable_table_names()
        
        # Cria a cadeia de Text-to-SQL usando o LLM, o objeto SQLDatabase e o prompt customizado.
        sql_query_chain = create_sql_query_chain(llm, db, prompt=prompt)
        
        return sql_query_chain, db, usable_tables
    except Exception as e:
        # Em caso de erro na inicialização, exibe mensagens de erro e retorna None.
        st.error(f"ERRO FATAL: Ao inicializar Text-to-SQL: {e}")
        st.error("Verifique se sua GOOGLE_API_KEY está correta e se a URI do banco está acessível.")
        return None, None, []

# Função de Execução e Exibição de Resultados
def execute_and_display_results_st(cursor, sql_query):
    """
    Executa a consulta SQL fornecida no banco de dados e exibe os resultados no Streamlit.
    Lida com consultas SELECT (exibindo dados em DataFrame) e outras consultas (informando sucesso/linhas afetadas).
    """
    if not sql_query or not sql_query.strip():
        st.warning("Nenhuma consulta SQL para executar.")
        return
    
    # Remove o ponto e vírgula
    sql_query = sql_query.rstrip(';')
    
    try:
        cursor.execute(sql_query) # Executa a consulta SQL.
        if cursor.description: # Verifica se a consulta retornou resultados (geralmente SELECT).
            column_names = [desc[0] for desc in cursor.description] # Obtém os nomes das colunas.
            results = cursor.fetchall() # Busca todos os resultados.
            if results:
                st.success("Resultados da Consulta:")
                df = pd.DataFrame(results, columns=column_names) # Cria um dataframe do pandas para exibição formatada.
                st.dataframe(df) # Exibe o dataframe.
            else:
                st.info("A consulta foi executada com sucesso, mas não retornou resultados.")
        else: # Se não houver descrição, geralmente é uma consulta de modificação (INSERT, UPDATE, DELETE).
            if hasattr(cursor, 'rowcount') and cursor.rowcount is not None and cursor.rowcount > -1:
                 st.success(f"Comando SQL executado com sucesso. {cursor.rowcount} linha(s) afetada(s).")
            else:
                st.success("Comando SQL executado com sucesso (sem resultados para exibir ou número de linhas afetadas indisponível).")
    except (mysql.connector.Error, psycopg2.Error) as err:
        # Captura erros específicos do banco de dados.
        st.error(f"ERRO ao executar a consulta SQL: {err}")
        st.error(f"SQL com problema: {sql_query}")
        try:
            # Tenta fazer rollback da transação em caso de erro para manter a consistência.
            if 'conn' in st.session_state and st.session_state.conn:
                st.session_state.conn.rollback()
                st.warning("A transação foi revertida (rollback) devido ao erro.")
        except (mysql.connector.Error, psycopg2.Error) as rb_err:
            st.error(f"Falha adicional ao tentar reverter a transação: {rb_err}")
    except Exception as e:
        # Captura outros erros inesperados.
        st.error(f"ERRO inesperado durante a execução da query: {e}")
        st.error(f"SQL com problema: {sql_query}")

# Função de formatação de SQL
def format_sql_with_regex(sql_query: str) -> str:
    """
    Formata uma query SQL usando expressões regulares para melhorar a legibilidade básica,
    adicionando quebras de linha antes de cláusulas SQL comuns.
    """
    if not sql_query:
        return ""
    
    # Adiciona quebra de linha antes das principais cláusulas SQL.
    # A flag re.IGNORECASE torna a busca insensível a maiúsculas/minúsculas.
    # O \b garante que estamos buscando palavras inteiras (ex: não vai quebrar a linha em 'GROUPING').
    formatted_query = re.sub(r'\b(FROM|WHERE|GROUP BY|ORDER BY|LEFT JOIN|RIGHT JOIN|INNER JOIN|ON|HAVING|LIMIT)\b', 
                             r'\n\1', 
                             sql_query, 
                             flags=re.IGNORECASE)
    
    # Remove múltiplos espaços em branco e limpa as linhas para um resultado final limpo.
    lines = [line.strip() for line in formatted_query.split('\n')]
    return '\n'.join(filter(None, lines))

# Função de Limpeza de SQL
def clean_sql_query(full_llm_output: str) -> str:
    """
    Limpa e extrai a consulta SQL da resposta bruta do LLM.
    Remove blocos de código Markdown (```sql) e espaços em branco extras.
    """
    if not isinstance(full_llm_output, str) or not full_llm_output.strip():
        return ""
    query = full_llm_output.strip()
    # Procura por um bloco de código SQL delimitado por ```sql.
    sql_block_match = re.search(r"```sql\s*(.*?)\s*```", query, re.DOTALL | re.IGNORECASE)
    if sql_block_match:
        # Se encontrado, extrai apenas o conteúdo dentro do bloco.
        query = sql_block_match.group(1).strip()

    # Retorna a query limpa, removendo quaisquer espaços em branco restantes nas extremidades.
    return query.strip()

# Função de Limpeza de Estado e Cache
def full_disconnect():
    """
    Fecha a conexão ativa com o banco de dados e limpa completamente
    todo o estado da sessão do Streamlit e o cache de recursos,
    garantindo um reset completo da aplicação.
    """
    if 'conn' in st.session_state and st.session_state.conn:
        try:
            st.session_state.conn.close() # Tenta fechar a conexão do banco de dados.
        except Exception as e:
            st.warning(f"Erro ao fechar conexão: {e}")
    # Lista de chaves a serem removidas do estado da sessão.
    keys_to_delete = [
        'db_connected', 'conn', 'cursor', 'sql_chain', 'db_langchain',
        'db_uri', 'usable_tables', 'generated_sql', 'db_type', 'db_host',
        'db_user', 'db_name', 'db_port', 'db_password'
    ]
    # Itera sobre as chaves e as remove do estado da sessão se existirem.
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]
    # Limpa o cache de recursos do streamlit, que armazena funções como initialize_text_to_sql_gemini.
    st.cache_resource.clear()

# Interface Gráfica do Streamlit
def run_streamlit_app():
    """
    Define e executa a interface do usuário da aplicação Streamlit.
    Esta é a função principal que organiza os componentes da UI,
    lógica de conexão, interação com o LLM e exibição de resultados.
    """
    st.set_page_config(page_title="Text-to-SQL", layout="wide")
    st.title("Text-to-SQL")

    # Inicializa o estado da sessão se ainda não estiver definido.
    if 'db_connected' not in st.session_state:
        st.session_state.db_connected = False
        st.session_state.google_api_key = os.getenv("GOOGLE_API_KEY", "") # Carrega a API Key do ambiente.

    with st.sidebar: # Conteúdo da barra lateral.
        st.header("Configurações")
        st.session_state.google_api_key = st.text_input(
            "Google API Key", 
            type="password", 
            value=st.session_state.get("google_api_key", ""),
        )
        if not st.session_state.google_api_key:
            st.warning("Insira a Google API Key para continuar.")
        
        st.subheader("Conexão com Banco de Dados")
        # Seleção do tipo de banco de dados (MySQL ou PostgreSQL).
        db_type = st.selectbox("Tipo de Banco de Dados", ["mysql", "postgres"], index=["mysql", "postgres"].index(st.session_state.get("db_type", "mysql")))
        
        # Campos de entrada para as credenciais do banco de dados.
        if db_type == "mysql":
                host = st.text_input("Host", value=st.session_state.get("db_host", "localhost"))
                user = st.text_input("Usuário", value=st.session_state.get("db_user", "root"))
                port_val = "3306" # Porta padrão para MySQL.

        elif db_type == "postgres":
            host = st.text_input("Host", value=st.session_state.get("db_host", "localhost"))
            user = st.text_input("Usuário", value=st.session_state.get("db_user", "postgres"))
            port_val = "5432" # Porta padrão para PostgreSQL.

        password_input = st.text_input("Senha", type="password", value=st.session_state.get("db_password", ""))
        dbname = st.text_input("Nome do Banco de Dados", value=st.session_state.get("db_name", ""))

        col1, col2 = st.columns(2) # Cria duas colunas para os botões Conectar/Desconectar.
        with col1:
            # Botão de conexão. Desabilitado se a API Key não for fornecida.
            if st.button("Conectar ao Banco", disabled=not st.session_state.google_api_key):
                if st.session_state.db_connected:
                    full_disconnect() # Desconecta se já houver uma conexão ativa.
                    st.info("Conexão anterior fechada. Tentando nova conexão...")
                
                conn_attempt = None
                db_uri_attempt = ""
                # Tenta conectar ao banco de dados com base no tipo selecionado.
                if db_type == "mysql":
                    conn_attempt = connect_to_mysql(host, user, password_input, dbname)
                    if conn_attempt:
                        db_uri_attempt = f"mysql+mysqlconnector://{user}:{password_input}@{host}/{dbname}"
                elif db_type == "postgres":
                    conn_attempt = connect_to_postgresql(host, user, password_input, dbname, port_val)
                    if conn_attempt:
                        db_uri_attempt = f"postgresql+psycopg2://{user}:{password_input}@{host}:{port_val}/{dbname}"
                
                if conn_attempt:
                    # Armazena os detalhes da conexão no estado da sessão.
                    st.session_state.conn = conn_attempt
                    st.session_state.cursor = conn_attempt.cursor()
                    st.session_state.db_uri = db_uri_attempt
                    st.session_state.db_connected = True
                    st.session_state.db_type = db_type
                    st.session_state.db_host = host
                    st.session_state.db_user = user
                    st.session_state.db_name = dbname
                    st.session_state.db_password = password_input
                    if db_type == "postgres":
                        st.session_state.db_port = port_val
                    st.success(f"Conectado ao {db_type.capitalize()} com sucesso")
                    
                    # Inicializa o motor text-to-SQL após a conexão bem-sucedida.
                    sql_chain_init, db_langchain_init, usable_tables_init = initialize_text_to_sql_gemini(
                        st.session_state.db_uri, st.session_state.google_api_key, db_type
                    )
                    
                    if sql_chain_init and db_langchain_init:
                        # Armazena os componentes da langchain no estado da sessão.
                        st.session_state.sql_chain = sql_chain_init
                        st.session_state.db_langchain = db_langchain_init
                        st.session_state.usable_tables = usable_tables_init
                    else:
                        st.error("Falha ao inicializar o motor Text-to-SQL. Desconectando.")
                        full_disconnect() # Desconecta se o motor LLM não puder ser inicializado.
                    st.rerun()
        with col2:
            # Botão de desconexão.
            if st.session_state.db_connected and st.button("Desconectar"):
                full_disconnect() # Chama a função de desconexão completa.
                st.info("Desconectado do banco de dados.")
                st.rerun() # Reinicia a aplicação.

        # Exibe as tabelas detectadas no schema do banco de dados.
        if st.session_state.db_connected and st.session_state.get("usable_tables"):
             with st.expander("Tabelas Detectadas no Schema", expanded=True):
                if st.session_state.usable_tables:
                    for table_name in st.session_state.usable_tables:
                        st.markdown(f"- `{table_name}`")
                else:
                    st.markdown("Nenhuma tabela encontrada ou schema não carregado.")

    # Lógica principal da aplicação.
    if not st.session_state.google_api_key:
        st.info("Configure sua Google API Key na barra lateral para usar a ferramenta.")
    elif not st.session_state.db_connected or not st.session_state.get('sql_chain'):
        st.info("Conecte-se a um banco de dados.")
    else:
        st.subheader("Faça sua pergunta")
        natural_query = st.text_area("Sua pergunta:", height=100, key="natural_query_input") # Campo de entrada para a pergunta em linguagem natural.
        if st.button("Gerar SQL", key="generate_sql_button"):
            if natural_query:
                with st.spinner("Gerando consulta SQL..."):
                    try:
                        
                        # Prepara o dicionário de entrada para a cadeia da LangChain.
                        chain_input = {
                            "question": natural_query,
                            "input": natural_query,
                            "dialect": st.session_state.db_langchain.dialect,
                            "top_k": 100
                        }
                        
                        # Invoca a cadeia text-to-SQL para gerar a consulta.
                        response_from_llm = st.session_state.sql_chain.invoke(chain_input)
                        
                        raw_output_for_cleaning = ""
                        # Extrai a string de resposta do LLM, que pode vir em diferentes formatos.
                        if isinstance(response_from_llm, dict) and 'result' in response_from_llm:
                            raw_output_for_cleaning = response_from_llm['result']
                        elif isinstance(response_from_llm, str):
                            raw_output_for_cleaning = response_from_llm
                        else:
                            st.warning(f"Resposta inesperada do LLM: {type(response_from_llm)}")
                            st.session_state.generated_sql = ""
                            st.stop()
                        
                        # Limpa e formata a consulta SQL gerada.
                        cleaned_sql = clean_sql_query(raw_output_for_cleaning)
                        formatted_sql = format_sql_with_regex(cleaned_sql)
                        
                        st.session_state.generated_sql = formatted_sql # Armazena o SQL gerado no estado da sessão.
                        
                    except Exception as e:
                        st.error(f"ERRO GERAL durante o processamento da pergunta: {e}")
                        st.session_state.generated_sql = ""
            else:
                st.warning("Por favor, insira uma pergunta.")

        # Exibe o SQL gerado e oferece a opção de executá-lo.
        if st.session_state.get("generated_sql"):
            st.subheader("SQL Gerado")
            st.code(st.session_state.generated_sql, language="sql") # Exibe o SQL em um bloco de código.
            if st.checkbox("Confirmar e Executar SQL", key="confirm_execute_sql"):
                if st.session_state.generated_sql: 
                    # Executa e exibe os resultados da consulta SQL.
                    execute_and_display_results_st(st.session_state.cursor, st.session_state.generated_sql)
                    
                    # Verifica se a query é de modificação (INSERT, UPDATE, DELETE, etc.) para realizar commit.
                    is_modifying_query = any(
                        keyword in st.session_state.generated_sql.upper() 
                        for keyword in ["INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"]
                    )
                    if is_modifying_query:
                        try:
                            st.session_state.conn.commit() # Realiza commit para salvar as alterações no banco.
                            st.success("Alterações foram enviadas para o banco de dados.")
                        except (mysql.connector.Error, psycopg2.Error) as commit_err:
                            st.error(f"ERRO ao enviar alterações: {commit_err}")
                            if st.session_state.conn: 
                                try:
                                    st.session_state.conn.rollback() # Realiza rollback em caso de erro no commit.
                                    st.warning("Rollback realizado devido a erro no envio.")
                                except Exception as rb_err:
                                    st.error(f"Erro também ao tentar rollback: {rb_err}")
                else:
                    st.warning("Nenhum SQL válido para executar.")
        elif st.session_state.get("generated_sql") == "": 
            pass
        
    st.markdown("---")

# Ponto de entrada do script.
if __name__ == "__main__":
    run_streamlit_app()