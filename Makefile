.PHONY: all setup run clean help

# Variáveis
PYTHON = python3
PIP = $(PYTHON) -m pip
VENV_DIR = venv
STREAMLIT = $(VENV_DIR)/bin/streamlit
REQUIREMENTS_FILE = requirements.txt
APP_FILE = text_to_sql.py

all: help

# Configura o ambiente virtual e instala as dependências
setup:
	@echo "Criando e ativando o ambiente virtual..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Ativando o ambiente virtual..."
	. $(VENV_DIR)/bin/activate || cmd /c "$(VENV_DIR)\Scripts\activate.bat"
	@echo "Instalando dependências..."
	$(VENV_DIR)/bin/pip install -r $(REQUIREMENTS_FILE)
	@echo "Configuração concluída. Para executar, use 'make run'."

# Executa o aplicativo Streamlit
run:
	@echo "Verificando ambiente virtual..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Ambiente virtual não encontrado. Execute 'make setup' primeiro."; \
		exit 1; \
	fi
	@echo "Iniciando o aplicativo Streamlit..."
	. $(VENV_DIR)/bin/activate || cmd /c "$(VENV_DIR)\Scripts\activate.bat"
	$(STREAMLIT) run $(APP_FILE)

# Limpa o ambiente virtual e outros arquivos gerados
clean:
	@echo "Limpando ambiente virtual e arquivos gerados..."
	rm -rf $(VENV_DIR)
	find . -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.log" -delete
	find . -name ".pytest_cache" -exec rm -rf {} +
	rm -f *.db # Se houver arquivos .db gerados localmente

# Exibe as opções de ajuda
help:
	@echo "Uso:"
	@echo "  make setup     - Cria o ambiente virtual e instala as dependências."
	@echo "  make run       - Inicia o aplicativo Streamlit."
	@echo "  make clean     - Remove o ambiente virtual e arquivos de cache/log."
	@echo "  make help      - Exibe esta mensagem de ajuda."