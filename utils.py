from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import sys
import subprocess
import requests
import shutil 
from datetime import datetime
from dotenv import load_dotenv
import pyautogui

from datetime import datetime

# Gera o nome do arquivo de log com data e hora do momento da execução
log_filename = datetime.now().strftime("testeAutomatico,%d-%m.%H-%M.log")

def log_message(message):
    """
    Registra uma mensagem no log e imprime no console sem erros de codificação.
    """

    # Substituir emojis por texto alternativo caso a codificação falhe
    replacements = {
        "✅": "[OK]",
        "⚠️": "[ALERTA]",
        "❌": "[ERRO]",
        "⏳": "[AGUARDANDO]",
        "🚀": "[INICIANDO]",
        "🔍": "[VERIFICANDO]",
        "🔧": "[CONFIGURANDO]"
    }

    for emoji, replacement in replacements.items():
        message = message.replace(emoji, replacement)

    # Força a saída no console para UTF-8
    try:
        print(message.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
    except UnicodeEncodeError:
        print(message.encode("utf-8", "ignore").decode("utf-8"))  # Se der erro, ignora caracteres inválidos

    # Salvar no arquivo de log com UTF-8 para evitar erros ao ler depois
    with open("log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(message + "\n")


def fill_field(driver, identifier, identifier_type, value, action_name="", timeout=20):
    """
    Localiza um campo de input e preenche com um valor.

    Parâmetros:
    - driver (WebDriver): Instância do Selenium WebDriver.
    - identifier (str): Identificador do campo (exemplo: ID ou XPath).
    - identifier_type (str): Tipo do identificador ('id', 'xpath', 'class_name', etc.).
    - value (str): Texto a ser inserido no campo.
    - action_name (str, opcional): Nome da ação para fins de log.
    - timeout (int, opcional): Tempo máximo de espera pelo elemento (padrão: 20 segundos).

    Retorno:
    - Nenhum. Apenas preenche o campo de input.
    """

    start_time = time.time()  # Marca o tempo de início da execução

    try:
        # Verifica se o valor passado é uma string
        if not isinstance(value, str):
            raise ValueError(f"❌ Esperado um valor de texto (string), mas recebeu {type(value).__name__}")

        # Dicionário para mapear os tipos de identificadores do Selenium
        by_type = {
            'id': By.ID,
            'xpath': By.XPATH,
            'class_name': By.CLASS_NAME,
            'css_selector': By.CSS_SELECTOR,
            'link_text': By.LINK_TEXT,
        }

        # Verifica se o tipo de identificador fornecido é válido
        if identifier_type not in by_type:
            raise ValueError(f"❌ Tipo de identificador '{identifier_type}' não é suportado.")

        wait = WebDriverWait(driver, timeout)  # Define o tempo máximo de espera

        # Aguarda até que o campo esteja presente na página
        element = wait.until(EC.presence_of_element_located((by_type[identifier_type], identifier)))

        # Aguarda até que o campo esteja clicável
        wait.until(EC.element_to_be_clickable((by_type[identifier_type], identifier)))

        # Limpa o campo antes de inserir um novo valor
        element.clear()
        time.sleep(1)  # Pequeno atraso para garantir que o campo esteja pronto

        # Insere o texto no campo de input
        element.send_keys(value)

    except TimeoutException:
        log_message(f"❌ Erro: O elemento com {identifier_type} '{identifier}' não foi encontrado após {timeout} segundos.")

    except NoSuchElementException:
        log_message(f"❌ Erro: O elemento com {identifier_type} '{identifier}' não foi encontrado.")

    except ValueError as ve:
        log_message(f"❌ Erro de valor: {ve}")

    except Exception as e:
        log_message(f"❌ Ocorreu um erro inesperado: {e}")

    finally:
        execution_time = time.time() - start_time
        log_message(f"⏳ Ação '{action_name}' concluída em {execution_time:.2f} segundos.")


def click_element(driver, identifier, identifier_type, action_name="", timeout=20):
    """
    Localiza um elemento na página e realiza um clique, baseado no tipo de identificador.

    Parâmetros:
    - driver (WebDriver): Instância do Selenium WebDriver.
    - identifier (str): O valor do identificador do elemento (ex: ID ou XPath).
    - identifier_type (str): O tipo do identificador ('id', 'xpath', 'class_name', etc.).
    - action_name (str, opcional): Nome da ação para log.
    - timeout (int, opcional): Tempo máximo de espera pelo elemento (padrão: 20 segundos).

    Retorno:
    - Nenhum. Apenas realiza o clique no elemento.
    """

    start_time = time.time()  # Marca o início da execução

    try:
        wait = WebDriverWait(driver, timeout)  # Configura tempo máximo de espera para encontrar o elemento

        # Dicionário para mapear os tipos de identificadores do Selenium
        by_type = {
            'id': By.ID,
            'xpath': By.XPATH,
            'class_name': By.CLASS_NAME,
            'css_selector': By.CSS_SELECTOR,
            'link_text': By.LINK_TEXT,
        }

        # Verifica se o tipo de identificador fornecido é válido
        if identifier_type not in by_type:
            raise ValueError(f"❌ Tipo de identificador '{identifier_type}' não é suportado.")

        # Aguarda até que o elemento esteja clicável na página
        element = wait.until(EC.element_to_be_clickable((by_type[identifier_type], identifier)))

        time.sleep(1)  # Pequeno delay para garantir que o elemento esteja pronto para interação
        element.click()  # Realiza o clique no elemento

    except TimeoutException:
        # Se o tempo limite for atingido e o elemento não for encontrado
        log_message(f"❌ Erro: O elemento com {identifier_type} '{identifier}' não foi encontrado após {timeout} segundos.")

    except NoSuchElementException:
        # Se o elemento não existir na página
        log_message(f"❌ Erro: O elemento com {identifier_type} '{identifier}' não foi encontrado.")

    except Exception as e:
        # Captura qualquer erro inesperado
        log_message(f"❌ Erro inesperado: {e}")

    finally:
        # Calcula e exibe o tempo total da execução
        execution_time = time.time() - start_time
        log_message(f"⏳ Ação '{action_name}' concluída em {execution_time:.2f} segundos.")


def get_file_path(folder_name):
    """
    Retorna o caminho absoluto da pasta especificada, considerando o ambiente de execução.

    Parâmetros:
    - folder_name (str): Nome da pasta a ser localizada.

    Retorno:
    - (str) Caminho absoluto da pasta especificada.
    """

    # Determina o diretório base dependendo do ambiente de execução
    if getattr(sys, 'frozen', False):  # Se for um executável criado com PyInstaller
        base_path = os.path.dirname(sys.executable)  # Diretório do executável
        folder_path = os.path.join(base_path, "_internal", "arquivos", folder_name)  # Caminho no executável
    else:  # Se estiver rodando como script Python normal
        base_path = os.path.dirname(os.path.abspath(__file__))  # Diretório do script
        folder_path = os.path.join(base_path, "arquivos", folder_name)  # Caminho no ambiente de desenvolvimento
    
    # Verifica se a pasta existe e exibe uma mensagem
    if os.path.exists(folder_path):
        log_message(f"✅ Pasta '{folder_name}' encontrada em: {folder_path}")
    else:
        log_message(f"⚠️ Aviso: Pasta '{folder_name}' não encontrada em {folder_path}")

    return folder_path  # Retorna o caminho absoluto da pasta

def load_env_file():
    """
    Carrega o arquivo .env corretamente, seja no ambiente de desenvolvimento ou no executável.

    Retorno:
    - Nenhum retorno, apenas carrega as variáveis do .env para o ambiente do sistema.
    """

    # Determina o diretório base conforme o ambiente de execução
    if getattr(sys, 'frozen', False):  # Se estiver rodando como executável do PyInstaller
        base_path = os.path.dirname(sys.executable)  # Obtém o diretório do executável
        # Define o caminho do arquivo .env dentro da pasta _internal
        env_path = os.path.join(base_path, "_internal", ".env")
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))  # Obtém o diretório do script Python
        # Define o caminho do arquivo .env no ambiente de desenvolvimento
        env_path = os.path.join(base_path, ".env")

    # Verifica se o arquivo .env existe antes de carregá-lo
    if os.path.exists(env_path):
        log_message(f"✅ Arquivo .env carregado de: {env_path}")
        load_dotenv(env_path)  # Carrega as variáveis do .env para o ambiente
    else:
        log_message("⚠️ Aviso: Arquivo .env não encontrado. Verifique o caminho.")

def send_files(driver,folder_name, action_name=""):
    """
    Envia arquivos automaticamente para uma janela de upload utilizando xdotool.

    Parâmetros:
    - folder_name (str): Nome da pasta que contém os arquivos.
    - action_name (str, opcional): Nome da ação para fins de log.

    Retorno:
    - Nenhum retorno. Apenas executa a ação e exibe mensagens de status.
    """

    start_time = time.time()  # Marca o tempo de início da execução

    try:
        # Obtém o caminho absoluto da pasta onde os arquivos estão armazenados
        folder_path = get_file_path(folder_name)

        # Verifica se a pasta realmente existe
        if not os.path.exists(folder_path):
            log_message(f"❌ Erro: A pasta '{folder_name}' não foi encontrada.")
            return  # Encerra a função se a pasta não existir

        time.sleep(1)  # Pequeno atraso antes de continuar

        files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file))]

        time.sleep(0.5)

        file_paths = "\n".join(files)
        file_input = driver.find_element(By.XPATH, "//input[@type='file' and @accept='image/*,.pdf,.zip']")
        file_input.send_keys(file_paths)

        log_message(f"✅ Arquivos da pasta '{folder_name}' enviados com sucesso!")
        
        pyautogui.hotkey('alt', 'f4')  # Fecha a janela de upload

    except subprocess.CalledProcessError as e:
        log_message(f"❌ Erro ao executar comando xdotool: {e}")

    except Exception as e:
        log_message(f"❌ Ocorreu um erro: {e}")

    finally:
        # Calcula e exibe o tempo total da operação
        execution_time = time.time() - start_time
        log_message(f"⏳ Ação '{action_name}' concluída em {execution_time:.2f} segundos.")


def check_text_on_page(driver, text, timeout, check_interval=5):
    """
    Verifica continuamente se um texto específico ainda está presente na página.

    Parâmetros:
    - driver (WebDriver): Instância do Selenium WebDriver.
    - text (str): Texto a ser verificado na página.
    - timeout (int): Tempo máximo para aguardar a remoção do texto (em segundos).
    - check_interval (int, opcional): Intervalo entre verificações (padrão: 5 segundos).

    Retorno:
    - True: Se o texto desaparecer antes do tempo limite.
    - False: Se o texto ainda estiver presente após o tempo limite.
    """

    start_time = time.time()  # Marca o tempo de início da verificação
    log_message(f"🔍 Iniciando verificação do texto: '{text}'")

    while True:
        try:
            # Busca elementos que contêm o texto desejado
            element_present = driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")

            # Se o texto não estiver mais na página, retorna True
            if not element_present:
                log_message(f"✅ O texto '{text}' desapareceu da página.")
                return False

        except Exception as e:
            log_message(f"❌ Erro ao verificar '{text}': {e}")
            return False

        # Se o tempo limite for atingido, retorna False
        if time.time() - start_time > timeout:
            log_message(f"⏳ Tempo limite atingido! O texto '{text}' ainda está na página.")
            return True

        # Aguarda o intervalo definido antes de verificar novamente
        time.sleep(check_interval)

def get_number(driver, identifier, identifier_type, action_name="", timeout=20):
    """
    Localiza um elemento que contém uma numeração e retorna o valor encontrado.

    Parâmetros:
    - driver (WebDriver): Instância do Selenium WebDriver.
    - identifier (str): Identificador do elemento na página.
    - identifier_type (str): Tipo do identificador ('id', 'xpath', 'class_name', etc.).
    - action_name (str, opcional): Nome da ação para fins de log.
    - timeout (int, opcional): Tempo máximo para aguardar o elemento (padrão: 20 segundos).

    Retorno:
    - badge_number (str ou None): O número capturado do elemento ou None se não for encontrado.
    """

    start_time = time.time()  # Marca o início da execução
    badge_number = None  # Inicializa a variável que armazenará o número

    try:
        # Mapeia os tipos de identificadores permitidos
        by_type = {
            'id': By.ID,
            'xpath': By.XPATH,
            'class_name': By.CLASS_NAME,
            'css_selector': By.CSS_SELECTOR,
            'link_text': By.LINK_TEXT,
        }

        # Verifica se o tipo de identificador fornecido é válido
        if identifier_type not in by_type:
            raise ValueError(f"Tipo de identificador '{identifier_type}' não é suportado.")

        # Aguarda até que o elemento esteja presente na página
        wait = WebDriverWait(driver, timeout)
        element = wait.until(EC.presence_of_element_located((by_type[identifier_type], identifier)))

        # Captura e limpa o texto do elemento
        badge_number = element.text.strip()

        # Se o elemento estiver visível, mas sem texto, exibe um aviso
        if not badge_number:
            log_message(f"⚠️ Aviso: O elemento com {identifier_type} '{identifier}' foi encontrado, mas está vazio.")
        else:
            log_message(f"✅ Numeração capturada: {badge_number}")

    except TimeoutException:
        # Se o tempo limite for atingido e o elemento não for encontrado
        log_message(f"❌ Erro: O elemento com {identifier_type} '{identifier}' não foi encontrado após {timeout} segundos.")

    except NoSuchElementException:
        # Se o elemento não existir na página
        log_message(f"❌ Erro: O elemento com {identifier_type} '{identifier}' não foi encontrado.")

    except ValueError as ve:
        # Se o tipo de identificador for inválido
        log_message(f"❌ Erro de valor: {ve}")

    except Exception as e:
        # Qualquer outro erro inesperado
        log_message(f"❌ Ocorreu um erro inesperado: {e}")

    finally:
        # Calcula o tempo de execução da ação
        execution_time = time.time() - start_time
        log_message(f"⏳ Ação '{action_name}' concluída em {execution_time:.2f} segundos.")

    return badge_number  # Retorna o número capturado (ou None se não encontrado)

def identify_fields(driver):
    try:
        # Conjunto de mensagens que indicam ausência de informações
        library = {
            'Esse paciente não possui um histórico de acompanhamento.',
            'Não há medidas a serem exibidas',
            'Nenhuma prescrição de medicamento',
            'Não identificamos palavras-chaves para esse paciente.',
            'Nenhum procedimento.',
            'Nenhuma prescrição de óculos',
            'Nenhuma refração dinâmica',
            'Nenhuma refração estática',
            'Nenhum exame de auto-refrator',
            'Nenhum exame de auto-tonômetro'
        }

        found_messages = set()  # Guarda mensagens encontradas para evitar repetição
        wait = WebDriverWait(driver, 5)  # Tempo máximo de espera por elementos

        # Identifica e expande as seções da página, se necessário
        expansion_headers = driver.find_elements(By.TAG_NAME, "mat-expansion-panel-header")

        for expander in expansion_headers:
            state_expander = expander.get_attribute("aria-expanded")  # Verifica se está expandido

            if state_expander == "false":  # Se estiver fechado, expande
                log_message("Expansor fechado. Expandindo agora...")
                expander.click()
                wait.until(lambda d: expander.get_attribute("aria-expanded") == "true")  # Aguarda a expansão
            else:
                log_message("Expansor já está aberto.")

        # Aguarda e busca todos os textos dentro de <mat-card-content>
        content_elements = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//mat-card-content//p"))
        )
        messages_found = []  # Lista para armazenar mensagens encontradas

        # Percorre os elementos para verificar se possuem alguma mensagem da biblioteca
        for content in content_elements:
            content_text = content.text.strip()  # Remove espaços extras

            if content_text in library and content_text not in found_messages:
                found_messages.add(content_text)  # Adiciona ao conjunto para evitar duplicação
                messages_found.append(content_text)  # Adiciona à lista de retorno

        log_message("Processamento finalizado!")
        return messages_found  # Retorna a lista de mensagens encontradas

    except Exception as e:
        log_message(f"Ocorreu um erro: {e}")  # Captura e exibe erros durante a execução


def delete_patient(patient_id, action_name=""):
    """
    Realiza uma requisição DELETE para remover um paciente da API Voiston.

    Parâmetros:
    - patient_id (str): ID do paciente a ser deletado.
    - action_name (str): Nome da ação para ser registrado no log.
    """
    url_api = os.getenv('URL_API')

    # URL da API onde o paciente será deletado
    url = f"{url_api}{patient_id}"

    # Obtém a API_KEY do ambiente (arquivo .env ou variável de ambiente do sistema)
    api_key = os.getenv("API_KEY")

    # Se a chave da API não for encontrada, exibe um erro e encerra a função
    if not api_key:
        log_message("Erro: API_KEY não encontrada. Verifique o .env!")
        return  # Sai da função sem executar a requisição

    # Define os headers da requisição HTTP
    headers = {
        "Content-Type": "application/json",  # Especifica o formato do conteúdo
        "apiKey": api_key  # Autenticação na API
    }

    # Registra o tempo de início da operação para fins de log
    start_time = time.time()

    try:
        # Envia a requisição DELETE para a API
        response = requests.delete(url, headers=headers)

        # Se a requisição foi bem-sucedida (código 200)
        if response.status_code == 200:
            log_message(f"✅ Paciente {patient_id} deletado com sucesso!")
        else:
            # Se houve um erro na requisição, exibe o código de resposta e a mensagem da API
            log_message(f"❌ Erro ao deletar paciente {patient_id}. Código: {response.status_code}, Resposta: {response.text}")

    except Exception as e:
        # Se houver um erro inesperado (exemplo: API fora do ar), exibe a mensagem de erro
        log_message(f"❌ Erro ao chamar o endpoint de deleção: {e}")

    finally:
        # Calcula o tempo total da operação e registra no log
        execution_time = time.time() - start_time
        log_message(f"⏳ Ação '{action_name}' concluída em {execution_time:.2f} segundos")

_installed_flag = False # Variável global

def install_requirements():
    global _installed_flag

    if _installed_flag:
        log_message("✅ Dependências já instaladas. Iniciando o teste...")
        return
    _installed_flag = True

    # Ajusta o caminho do requirements.txt corretamente
    if getattr(sys, 'frozen', False):  # Se estiver rodando como executável do PyInstaller
        base_path = sys._MEIPASS  # Diretório temporário do PyInstaller
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))  # Diretório do script

    requirements_path = os.path.join(base_path, 'requirements.txt')

    if not os.path.exists(requirements_path):
        log_message(f"❌ Arquivo {requirements_path} não encontrado!")
        sys.exit(1)

    log_message("🔍 Verificando dependências...")

    # Obtém a lista de pacotes necessários
    with open(requirements_path, "r") as req_file:
        required_packages = [line.strip() for line in req_file.readlines() if line.strip()]

    # Obtém a lista de pacotes já instalados
    installed_packages = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True)
    installed_packages = installed_packages.stdout.split("\n")

    # Identifica os pacotes que ainda não estão instalados
    missing_packages = [pkg for pkg in required_packages if not any(pkg in installed for installed in installed_packages)]

    if not missing_packages:
        log_message("✅ Todas as dependências já estão instaladas. Iniciando o teste...")
        return  # Se tudo estiver instalado, não abre o terminal e inicia o teste imediatamente

    log_message("⚙️ Instalando pacotes necessários...")

    python_cmd = sys.executable  # Usa o Python atual
    venv_path = os.path.join(base_path, "venv")  # Caminho do ambiente virtual
    venv_python = os.path.join(venv_path, "Scripts", "python.exe") if os.name == "nt" else os.path.join(venv_path, "bin", "python")

    # Testa se o pip está disponível
    test_pip_cmd = f"{python_cmd} -m pip --version"
    result = subprocess.run(test_pip_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Se pip não estiver disponível ou ambiente for restrito, cria um ambiente virtual
    if b"externally-managed-environment" in result.stderr or not shutil.which("pip"):
        log_message("⚠️ Ambiente do sistema restringe instalações. Criando ambiente virtual...")

        if not os.path.exists(venv_path):
            subprocess.run(f"{python_cmd} -m venv {venv_path}", shell=True)

        python_cmd = venv_python  # Passa a usar o Python do ambiente virtual
        subprocess.run(f"{python_cmd} -m pip install --upgrade pip", shell=True)

    # Comando para instalar as dependências
    install_cmd = f"{python_cmd} -m pip install -r \"{requirements_path}\""

    # Execução no Windows
    if os.name == "nt":
        terminal_cmd = f'start cmd /k "{install_cmd} & timeout /t 2 & exit"'
    else:  # Linux/macOS
        terminal_cmd = f'x-terminal-emulator -e "sh -c \'{install_cmd}; sleep 2\'"'

    subprocess.run(terminal_cmd, shell=True)

    log_message("✅ Instalação concluída. Iniciando o teste...")

def extract_data(driver):
    """
    Extrai informações das páginas de Prontuários e Exames.

    Parâmetros:
    - driver (WebDriver): Instância do Selenium WebDriver.

    Retorno:
    - dict: Dicionário contendo os valores extraídos.
    """

    time.sleep(2)  # Aguarda a página carregar os dados

    categories = {
        "prescription": "Quantidade de prescrições encontradas no prontuário",
        "procedures": "Evidências de procedimentos encontradas no prontuário",
        "measurement_prontuario": "Quantidade de medidas extraídas do prontuário",
        "measurement_exame": "Quantidade de medidas extraídas do exame",
        "group": "Quantidade de grupos encontrados no exame"
    }

    extracted_data = {
        "prescriptions": 0,
        "procedures": 0,
        "measurements": 0,
        "groups": 0
    }

    try:
        # Localiza todas as divs que podem conter os dados
        chips = driver.find_elements(By.CLASS_NAME, "mat-chip")

        for chip in chips:
            try:
                # Obtém a descrição da categoria
                label = chip.get_attribute("aria-label").strip() if chip.get_attribute("aria-label") else ""

                value = 0  # Valor padrão caso não seja encontrado

                # Tenta encontrar o valor no .mat-badge-content (página de Exames)
                try:
                    value_element = chip.find_element(By.CLASS_NAME, "mat-badge-content")
                    value = int(value_element.text) if value_element.text.isdigit() else 0
                except:
                    # Se não encontrou .mat-badge-content, tenta pegar o número diretamente do mat-chip
                    text_value = chip.text.strip()
                    value = int(text_value) if text_value.isdigit() else 0

                # Mapeia os valores para os campos corretos
                if label == categories["prescription"]:
                    extracted_data["prescriptions"] = value
                elif label == categories["procedures"]:
                    extracted_data["procedures"] = value
                elif label == categories["measurement_prontuario"] or label == categories["measurement_exame"]:
                    extracted_data["measurements"] += value  # Soma medidas de ambas as páginas
                elif label == categories["group"]:
                    extracted_data["groups"] = value

            except Exception as e:
                log_message(f"⚠️ Erro ao processar um chip: {e}")

    except Exception as e:
        log_message(f"❌ Erro ao extrair dados da página: {e}")

    log_message(f"📋 Dados extraídos - Prescrições: {extracted_data['prescriptions']}, "
                f"Procedimentos: {extracted_data['procedures']}, "
                f"Medidas: {extracted_data['measurements']}, "
                f"Grupos: {extracted_data['groups']}")

    return extracted_data