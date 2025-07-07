# Projeto Text-to-SQL

Este projeto é uma ferramenta interativa que permite aos usuários consultar bancos de dados MySQL e PostgreSQL usando linguagem natural, convertendo as perguntas em consultas SQL por meio de um modelo de linguagem grande (LLM) do Google Gemini. A aplicação é construída com Streamlit para a interface do usuário e utiliza a biblioteca LangChain para a orquestração do Text-to-SQL.

## Funcionalidades

* **Conexão Flexível:** Conecta-se a bancos de dados MySQL e PostgreSQL.
* **Inspeção de Schema:** Carrega automaticamente a lista de tabelas e, opcionalmente, amostras de linhas para ajudar o LLM a entender a estrutura do banco de dados.
* **Interface Intuitiva:** Apresenta uma interface amigável construída com Streamlit para inserção de perguntas em linguagem natural.
* **Geração de SQL:** Converte perguntas em linguagem natural para consultas SQL válidas, utilizando um modelo Gemini via LangChain.
* **Visualização de Resultados:** Exibe os resultados das consultas SQL em uma tabela formatada (para `SELECT`s) ou informa o sucesso da execução para comandos de modificação.
* **Formatação e Limpeza de SQL:** O SQL gerado pelo LLM é limpo e formatado para melhor legibilidade.

## Tecnologias Utilizadas

* **Python:** Linguagem de programação principal.
* **Streamlit:** Para construção da interface de usuário interativa.
* **`mysql-connector-python`:** Driver para conexão com bancos de dados MySQL.
* **`psycopg2-binary`:** Driver para conexão com bancos de dados PostgreSQL.
* **SQLAlchemy:** Toolkit SQL e Mapeador Objeto-Relacional (ORM) utilizado pela LangChain para abstração do banco de dados.
* **Pandas:** Para manipulação e exibição tabular dos resultados das consultas.
* **LangChain:** Framework para desenvolvimento de aplicações alimentadas por LLMs, especificamente:
    * `langchain-core`
    * `langchain-community`
    * `langchain-google-genai` (para integração com modelos Google Gemini)

## Pré-requisitos

Antes de executar o projeto, certifique-se de ter:

* Python 3.8 ou superior instalado.
* Acesso a um banco de dados MySQL ou PostgreSQL.
* Uma chave de API do Google Gemini.

## Instalação

1.  **Clone o repositório:**

    ```bash
    git clone <URL_DO_SEU_REPOSITORIO>
    cd <nome_do_seu_repositorio>
    ```

2.  **Crie e ative um ambiente virtual (recomendado):**

    ```bash
    python -m venv venv
    # No Windows
    .\venv\Scripts\activate
    # No macOS/Linux
    source venv/bin/activate
    ```

3.  **Instale as dependências:**

    ```bash
    pip install -r requirements.txt
    ```

## Configuração da Google API Key

A ferramenta requer uma chave de API do Google Gemini para funcionar. Você pode obter uma em [Google AI Studio](https://ai.google.dev/).

Defina sua chave de API como uma variável de ambiente:

* **No Windows (CMD):**

    ```bash
    set GOOGLE_API_KEY="SUA_CHAVE_AQUI"
    ```

* **No Windows (PowerShell):**

    ```bash
    $env:GOOGLE_API_KEY="SUA_CHAVE_AQUI"
    ```

* **No macOS/Linux:**

    ```bash
    export GOOGLE_API_KEY="SUA_CHAVE_AQUI"
    ```

Alternativamente, você pode colar a chave diretamente no campo "Google API Key" na barra lateral do aplicativo Streamlit.

## Como Executar

1.  Certifique-se de que seu ambiente virtual esteja ativado.
2.  Execute o aplicativo Streamlit a partir do diretório raiz do projeto:

    ```bash
    streamlit run text_to_sql.py
    ```

3.  O aplicativo será aberto automaticamente no seu navegador web padrão (geralmente `http://localhost:8501`).

## Uso

1.  **Na barra lateral:**
    * Insira sua **Google API Key**.
    * Selecione o **Tipo de Banco de Dados** (MySQL ou PostgreSQL).
    * Preencha os detalhes de conexão: **Host**, **Usuário**, **Senha** e **Nome do Banco de Dados**.
    * Clique em "Conectar ao Banco".
    * Após a conexão bem-sucedida, as tabelas detectadas no schema serão listadas.

2.  **Na área principal:**
    * Digite sua pergunta em linguagem natural no campo "Sua pergunta:".
    * Clique em "Gerar SQL". O SQL gerado será exibido.
    * Marque a caixa "Confirmar e Executar SQL" para executar a consulta no banco de dados.
    * Os resultados da consulta serão exibidos abaixo.
