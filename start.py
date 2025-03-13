import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import psutil
from utils import fill_field, click_element, check_text_on_page, send_files, get_number, identify_fields, delete_patient, install_requirements, load_env_file, extract_data
import os
import sys
import re
from datetime import datetime
import threading

# Gera o nome do arquivo de log
log_filename = "testeAutomatico.log"

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
    with open(log_filename, "a", encoding="utf-8") as log_file:
        log_file.write(message + "\n")

# Bloqueio para evitar múltiplas execuções
lock = threading.Lock()

# Caminho do próprio executável (se estiver rodando como PyInstaller)
if getattr(sys, 'frozen', False):
    exe_name = os.path.basename(sys.executable)  # Nome do executável
    current_pid = os.getpid()  # Pega o PID atual

    # Conta quantas instâncias do mesmo executável estão rodando
    instances = [p.info for p in psutil.process_iter(attrs=['pid', 'name']) if p.info['name'] == exe_name]
    
    if len(instances) > 1:  # Se já existir uma instância, encerra
        log_message(f"⚠️ O executável '{exe_name}' já está rodando! Evitando múltiplas execuções.")
        sys.exit(0)  # Sai imediatamente para evitar loops

# Define flag global para evitar execuções repetidas
if hasattr(sys, '_running') and sys._running:
    log_message("⚠️ O script já está em execução. Evitando loop!")
    sys.exit(0)

sys._running = True  # Marca como rodando

# Carrega variáveis de ambiente
load_env_file()

# Executa instalação de dependências **somente uma vez**
with lock:
    install_requirements()

log_message("✅ Ambiente configurado. Iniciando execução...")

class Action:

    _instance_lock = threading.Lock()
    def __init__(self):
        with self._instance_lock:
            self.driver = None
            self.wait = None
            load_env_file()
            self.open_browser()
            self.Login()    
            self.Register_patient()
            self.awaiting_processing()
            self.check_exams()
            self.check_widgets()
            self.del_patient()
            self.logout()

    def open_browser(self):
        """
        Inicializa o navegador Google Chrome com configurações específicas.

        Retorno:
        - Nenhum. Apenas inicia o navegador e acessa o site desejado.
        """

        try:
            log_message("🔧 Configurando navegador...")

            # Configurações do Chrome
            options = webdriver.ChromeOptions()

            # Caminho do ChromeDriver (caso seja necessário em sistemas Linux)
            chromedriver_path = "/usr/bin/chromedriver"
            service = Service(chromedriver_path)  

            # Define opções para melhorar a execução do Selenium
            options.add_argument("--start-maximized")  # Inicia o navegador maximizado
            options.add_argument("--disable-headless")  # Garante que o modo gráfico esteja ativado
            options.add_argument("--disable-gpu")  # Evita possíveis bugs gráficos em alguns sistemas
            options.add_argument("--disable-blink-features=AutomationControlled")  # 🔹 Evita que o site detecte que é um bot
            options.add_argument("--no-sandbox")  # 🔹 Necessário para alguns sistemas Linux
            options.add_argument("--disable-dev-shm-usage")  # 🔹 Evita uso excessivo de memória em contêineres

            # Evita que o Selenium seja detectado pelo Chrome
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            # Instala e configura o ChromeDriver automaticamente
            service = Service(ChromeDriverManager().install())

            # Inicializa o WebDriver com as opções configuradas
            self.driver = webdriver.Chrome(service=service, options=options)
            log_message("✅ Navegador inicializado.")

            # Define um tempo de espera implícito para encontrar elementos
            self.driver.implicitly_wait(2)
            self.wait = WebDriverWait(self.driver, 10)

            log_message("🌐 Abrindo site...")
            self.driver.get("https://staging.voiston.ai/user/login?dp_id=MTA0")  # URL do sistema a ser acessado
            log_message("✅ Site aberto com sucesso!")

        except Exception as e:
            log_message(f"❌ Erro durante a inicialização do navegador: {e}")

    def Login(self):
        """
        Realiza login automático no sistema usando as credenciais armazenadas no .env.

        Retorno:
        - Nenhum. Apenas executa a ação e exibe mensagens de status.
        """

        # Obtém as credenciais do arquivo .env
        email = os.getenv('EMAIL')  # Recupera o e-mail armazenado
        password = os.getenv('PASSWORD')  # Recupera a senha armazenada

        try:
            start_time = time.time()  # Marca o início do login
            time.sleep(5)  # Pequeno atraso para garantir que a página carregue

            log_message("🔑 Realizando login...")

            # Clica no botão de acesso
            click_element(self.driver, 'access', 'class_name', 'Click de acesso')
            time.sleep(5)  # Aguarda a interface carregar

            # Preenche os campos de login com as credenciais
            fill_field(self.driver, 'email', 'id', email, 'Preenchimento de Email')
            fill_field(self.driver, 'password', 'id', password, 'Preenchimento de Password')

            # Clica no botão "Entrar"
            click_element(self.driver, 'next', 'id', 'Click entrar')
            timeout = 400  # Define um tempo limite de 5 minutos

            time.sleep(1)  # Aguarda redirecionamento
            while time.time() - start_time < timeout:
                if not check_text_on_page(self.driver, 'Aguarde enquanto processamos sua requisição...', timeout=timeout):    
                    log_message("✅ Log-in OK. Continuando ...")
                    break
                time.sleep(1)
                log_message("⏳ Aguarde enquanto processamos sua requisição...")
                
            else:
                execution_time = time.time() - start_time
                log_message(f"❌ Timeout: Texto 'Aguarde enquanto processamos sua requisição...' ainda presente após {execution_time:.2f}")
                return  # Encerra a função caso o tempo de espera exceda o limite

            log_message("✅ Login realizado com sucesso!")
            time.sleep(2)  # Aguarda redirecionamento

            # Possível clique para acessar uma seção específica após login (desativado por enquanto)
            # click_element(self.driver, "//span[contains(text(), 'TESTE AUTOMATIZADO')]", 'xpath', 'Clicar no paciente')

        except Exception as e:
            log_message(f"❌ Erro durante login: {e}")

        finally:
            execution_time = time.time() - start_time  # Calcula o tempo total do login
            log_message(f"⏳ Ação Login concluída em {execution_time:.2f} segundos.")

    def Register_patient(self):
        """
        Realiza o cadastro automático de um paciente no sistema.

        Retorno:
        - Nenhum. Apenas executa a ação e exibe mensagens de status.
        """

        try:
            start_time = time.time()  # Marca o início da execução
            time.sleep(5)  # Aguarda carregamento da página

            log_message("📝 Realizando cadastro de paciente...")

            # Clica no botão para adicionar um novo paciente
            click_element(self.driver, "//button[span[contains(., 'Adicionar novo paciente')]]", 'xpath', 'Click novo Paciente')

            # Preenche os campos do paciente
            fill_field(self.driver, "//input[@formcontrolname='name']", 'xpath', 'Teste Automatizado', 'Preencher campo nome')
            fill_field(self.driver, "//input[@placeholder='DD/MM/AAAA']", 'xpath', '20051995', 'Preencher campo data de nascimento')

            # Seleciona o gênero
            click_element(self.driver, "//mat-select[@formcontrolname='gender']", 'xpath', 'Abrir seletor de gênero')
            click_element(self.driver, "//span[text()='Feminino']", 'xpath', 'Selecionar gênero')

            # Clica no botão "Salvar" para concluir o cadastro inicial
            click_element(self.driver, "//button//span[text()='Salvar']", 'xpath', 'Click salvar')

            time.sleep(5)  # Aguarda a página atualizar antes de prosseguir

            # Clica no botão para adicionar exames e prontuários
            click_element(self.driver, "//button[@mattooltip='Adicionar exames, prontuários']", 'xpath', 'Click adicionar exames, prontuários')

            # Envio de exames
            click_element(self.driver, "//button[.//span[text()='Clique para enviar Exames']]", 'xpath', 'Clique para enviar Exames')
            send_files(self.driver,'exames', 'Selecionando exames')

            time.sleep(1)  # Pequeno delay para estabilidade

            # Envio de prontuários
            click_element(self.driver, "//button[.//span[text()='Clique para enviar Prontuários']]", 'xpath', 'Clique para enviar Prontuários')
            send_files(self.driver,'txts', 'Selecionando Prontuários')

            time.sleep(3)  # Aguarda o upload ser concluído

            # Clica no botão "Salvar" para finalizar o processo
            click_element(self.driver, "//button[span[text()='Salvar']]", 'xpath', 'Click Salvar')

        except Exception as e:
            log_message(f"❌ Erro durante preenchimento dos dados do paciente: {e}")

        finally:
            execution_time = time.time() - start_time  # Calcula o tempo total da execução
            log_message(f"⏳ Ação Registrar paciente concluída em {execution_time:.2f} segundos.")

    def awaiting_processing(self):
        """
        Aguarda o processamento dos arquivos enviados (exames e prontuários).

        Retorno:
        - Nenhum. Apenas monitora o progresso e exibe mensagens de status.
        """

        try:
            start_time = time.time()  # Marca o início do tempo de espera
            time.sleep(5)  # Pequena pausa para garantir que a página carregue

            log_message("⏳ Aguardando processamento...")

            # Define o tempo máximo de espera (5 minutos)
            timeout = 400  
            
            # Verifica se a mensagem "Enviando arquivos..." desaparece
            while time.time() - start_time < timeout:
                if not check_text_on_page(self.driver, 'Enviando arquivos...', timeout=timeout):
                    log_message("✅ Texto 'Enviando arquivos...' desapareceu. Continuando processamento...")
                    break
                time.sleep(3)  # Pausa de 5 segundos para estabilidade
                log_message("⏳ Processamento ainda em andamento...")
            else:
                log_message("❌ Timeout: Texto 'Enviando arquivos...' ainda presente após 5 minutos.")
                return  # Encerra a função caso o tempo de espera exceda o limite

            time.sleep(4)  # Pausa adicional para garantir estabilidade na página

            # Clica na aba "Prontuários"
            click_element(self.driver, "//a//img[@src='/assets/icon/VOISTON_ICONS-16.svg']", 'xpath', 'Click Prontuários')

            time.sleep(2)  # Pausa adicional para garantir estabilidade na página

            # Segunda verificação: espera até que "Aguardando processamento" ou "Processando:" desapareça
            while time.time() - start_time < timeout:
                aguarde = check_text_on_page(self.driver, 'Aguardando processamento', timeout=timeout)
                processando = check_text_on_page(self.driver, 'Processando:', timeout=timeout)

                if not aguarde and not processando:
                    # Se ambos os textos desapareceram, o processamento terminou
                    log_message("✅ Texto 'Aguardando processamento' desapareceu. Continuando...")
                    break

                else:
                    log_message("❌ Timeout: Nenhum dos textos desapareceu no tempo limite.")
                    return  # Se o tempo limite for atingido, encerra a função

            time.sleep(1)  # Pequena pausa para estabilidade
            extract_data(self.driver)
            time.sleep(1)  # Pequena pausa antes de finalizar

        except Exception as e:
            log_message(f"❌ Erro durante processamento: {e}")

        finally:
            execution_time = time.time() - start_time  # Calcula o tempo total de execução
            log_message(f"⏳ Ação 'Processamento' concluída em {execution_time:.2f} segundos.")
    
    def check_exams(self):
        """
        Verifica o processamento dos exames enviados, aguardando a conclusão antes de prosseguir.

        Retorno:
        - Nenhum. Apenas monitora o processamento e exibe mensagens de status.
        """

        try:
            start_time = time.time()  # Marca o início do tempo de execução
            medidas = None  # Inicializa a variável de medidas
            erros = None  # Inicializa a variável de erros
            time.sleep(5)  # Pequena pausa para garantir que a página carregue

            log_message("🔍 Verificando processamento dos exames...")

            # Clica no menu de exames
            click_element(self.driver, "//a//img[@src='/assets/icon/VOISTON_ICONS-11.svg']", 'xpath', 'Click Exames')

            # Clica na aba de exames enviados
            click_element(self.driver, "//mat-icon[text()='cloud_download']/parent::a", 'xpath', 'Click Exames enviados')
            time.sleep(2)  # Pausa para garantir que a página carregue
            # Tempo limite para o processamento (5 minutos)
            timeout = 400
            start_time = time.time()

            # Aguarda o desaparecimento dos textos de "Aguardando processamento" ou "Exame aguardando processamento"
            while time.time() - start_time < timeout:
                waiting = check_text_on_page(self.driver, 'Aguardando processamento', timeout=timeout)
                exam = check_text_on_page(self.driver, 'Exame aguardando processamento', timeout=timeout)

                if not waiting and not exam:
                    # Se ambos os textos desapareceram, o processamento terminou
                    execution_time = time.time() - start_time
                    log_message(f"✅ Processamento concluído em {execution_time:.2f} segundos. Continuando...")
                    break

                log_message("⏳ Processamento ainda em andamento...")
                time.sleep(5)  # Pausa de 5 segundos para estabilidade
                click_element(self.driver, "//mat-icon[text()='update']", 'xpath', 'Click Atualizando Envios')
            else:
                log_message("❌ Timeout: Texto 'Aguardando processamento' ainda presente após 5 minutos.")

            # Após a conclusão do processamento, captura os números de medidas e erros
            time.sleep(1)
            medidas = get_number(self.driver, "//p/span[1]", 'xpath', 'Verificação de Medidas')
            erros = get_number(self.driver, "//p[contains(text(), 'Erros')]", 'xpath', 'Verificação de Erros')
            time.sleep(1)
            log_message(f" Foram encontrados nos Arquivos de Exames Enviados {medidas} Medidas e {erros} Erros.")
            click_element(self.driver, "//a//img[@src='/assets/icon/VOISTON_ICONS-11.svg']", 'xpath', 'Click Exames')
            time.sleep(1)  # Pequena pausa para garantir estabilidade
            extract_data(self.driver)
            time.sleep(1)  # Pequena pausa antes de finalizar

        except Exception as e:
            log_message(f"❌ Erro durante processamento: {e}")

        finally:
            execution_time = time.time() - start_time  # Calcula o tempo total da execução
            log_message(f"⏳ Ação 'checando exames' concluída em {execution_time:.2f} segundos.")
    
    def check_widgets(self):
        """
        Expande e verifica os widgets disponíveis na página.

        Retorno:
        - Nenhum. Apenas expande os widgets e registra mensagens de status.
        """

        try:
            start_time = time.time()  # Marca o início da execução
            time.sleep(5)  # Pausa para garantir carregamento da página

            log_message("🔍 Verificando widgets...")

            # Clica no botão para acessar a aba "Panorama"
            click_element(self.driver, "//img[@src='/assets/icon/VOISTON_ICONS-01.svg']", 'xpath', 'Click Panorama')

            time.sleep(5)  # Tempo de espera para carregamento dos widgets

            # Encontra todos os elementos de expansão na página
            expansion = self.driver.find_elements(By.TAG_NAME, "mat-expansion-panel-header")

            for expansions in expansion:
                state_expansions = expansions.get_attribute("aria-expanded")  # Verifica se o painel está expandido

                if state_expansions == "false":  # Se o painel estiver fechado, expande
                    log_message("🔽 Expansor fechado. Expandindo agora...")
                    time.sleep(1)
                    expansions.click()
                else:
                    log_message("✅ Expansor já está aberto.")

            time.sleep(5)  # Tempo de espera para garantir carregamento das informações

            # Chama a função para identificar os campos da página
            teste = identify_fields(self.driver)

            time.sleep(1)  # Pequena pausa antes de finalizar

        except Exception as e:
            log_message(f"❌ Erro durante verificação dos widgets: {e}")
        
        finally:
            execution_time = time.time() - start_time  # Calcula o tempo total da execução
            log_message(f"Não foram encontrados: {teste}.")
            log_message(f"⏳ Ação 'checando widgets' concluída em {execution_time:.2f} segundos.")

    def del_patient(self):
        """
        Exclui um paciente com base no ID extraído da URL atual.

        Retorno:
        - Nenhum. Apenas exclui o paciente e exibe mensagens de status.
        """

        try:
            start_time = time.time()  # Marca o início da execução
            time.sleep(5)  # Aguarda possíveis carregamentos da página

            # Obtém a URL atual da página
            url = self.driver.current_url

            # Usa regex para extrair o ID do paciente da URL
            match = re.search(r'/patient/(\d+)/', url)  
            patient_id = match.group(1) if match else None

            if patient_id:
                # Chama a função que realiza a exclusão do paciente
                delete_patient(patient_id, 'delete_patient')
                log_message(f"✅ Paciente {patient_id} excluído com sucesso!")
            else:
                log_message("❌ Erro: ID do paciente não encontrado na URL!")

        except Exception as e:
            log_message(f"❌ Erro durante exclusão do paciente {patient_id} : {e}")

        finally:
            execution_time = time.time() - start_time  # Calcula o tempo total da execução
            log_message(f"⏳ Ação 'excluir paciente {patient_id}' concluída em {execution_time:.2f} segundos.")

    def logout(self):
        """
        Encerra a sessão do navegador e registra a ação.
    
        Retorno:
        - Nenhum. Apenas fecha o navegador e exibe mensagens de status.
        """
    
        self.driver.quit()  # Fecha todas as janelas do navegador e encerra a sessão

        log_message("🚪 Sessão encerrada.")

if __name__ == "__main__":
    if not hasattr(sys, '_frozen') or (hasattr(sys, '_frozen') and not getattr(sys, '_running', False)):
        setattr(sys, '_running', True)  # Evita múltiplas execuções
        Action() 