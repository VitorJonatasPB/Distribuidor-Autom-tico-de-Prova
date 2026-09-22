import os
import time
import re
import requests
import pandas as pd
from dotenv import load_dotenv, set_key
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

URL_LOGIN = "https://cursos.ibad.com.br/entrar"

class IbadAutomator:
    """
    Classe responsável pela automação do sistema IBAD.
    Gerencia desde a carga de dados (Local/Web) até a interação com o navegador.
    """
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.driver = None
        self.running = True # Flag para controle de parada

    def parar(self):
        """Sinaliza para o robô parar o processamento atual."""
        self.running = False
        self.log("::: Comando de PARADA recebido. Aguardando interrupção segura... :::")

    def log(self, message):
        """Exibe logs no terminal e na interface gráfica."""
        print(message)
        if self.log_callback:
            self.log_callback(message)

    def carregar_e_filtrar_dados(self, origem, caminho_ou_url, coluna_filtro, valor_filtro):
        """
        Baixa a planilha (se web/Google Sheets) e aplica o filtro dinâmico definido na interface.
        """
        self.log(f"Iniciando carga de dados de: {origem}")
        try:
            # 1. Trata origem Web/Google Sheets
            if origem != "Computador":
                url = caminho_ou_url
                if "docs.google.com/spreadsheets" in url:
                    self.log("Link do Google Sheets detectado. Convertendo para CSV...")
                    # Extrai o GID se existir para baixar a aba correta
                    gid_match = re.search(r'gid=(\d+)', url)
                    gid = gid_match.group(1) if gid_match else None
                    
                    # Remove /edit, /view, etc. e reconstrói o link de exportação
                    base_url = re.sub(r'/(edit|view|#).*', '', url)
                    url = f"{base_url}/export?format=csv"
                    if gid:
                        url += f"&gid={gid}"
                
                self.log(f"Baixando dados...")
                response = requests.get(url)
                response.raise_for_status()
                
                temp_file = "temp_dados.csv"
                with open(temp_file, "wb") as f:
                    f.write(response.content)
                caminho_ou_url = temp_file

            # 2. Leitura da planilha
            if caminho_ou_url.endswith('.csv'):
                df = pd.read_csv(caminho_ou_url, encoding='utf-8-sig')
            else:
                df = pd.read_excel(caminho_ou_url)

            # Tratamento extra: remove espaços invisíveis nos nomes das colunas e no filtro
            df.columns = df.columns.str.strip()
            coluna_filtro = str(coluna_filtro).strip()

            # 3. Filtro Dinâmico
            if coluna_filtro in df.columns:
                self.log(f"Filtrando: {coluna_filtro} == {valor_filtro}")
                df_filtrado = df[df[coluna_filtro].astype(str) == str(valor_filtro)]
                col_aluno = os.getenv("COLUNA_ALUNO") or 'NOME'
                nomes = df_filtrado[col_aluno].tolist()
                self.log(f"[OK] {len(nomes)} alunos filtrados.")
                return nomes
            else:
                self.log(f"[ERRO] Coluna '{coluna_filtro}' não existe na planilha.")
                return False

        except Exception as e:
            self.log(f"[ERRO] Falha ao carregar dados: {e}")
            return False

    def iniciar_driver(self):
        self.log("Iniciando navegador...")
        chrome_options = Options()
        perfil_path = os.path.join(os.getcwd(), "perfil_automacao")
        chrome_options.add_argument(f"--user-data-dir={perfil_path}")
        chrome_options.add_argument("--profile-directory=Default")
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.maximize_window()
        return self.driver

    def verificar_login(self):
        self.log(f"Acessando {URL_LOGIN}...")
        self.driver.get(URL_LOGIN)
        time.sleep(3)
        
        if "entrar" in self.driver.current_url.lower():
            self.log("[!] LOGIN MANUAL NECESSÁRIO.")
            self.log("[!] Por favor, logue no navegador e resolva qualquer CAPTCHA.")
            
            while "entrar" in self.driver.current_url.lower():
                time.sleep(2)
            
            self.log("[OK] Login detectado!")
        else:
            self.log("[OK] Já logado!")

    def escolher_perfil(self):
        self.log("Verificando tela de perfil...")
        wait = WebDriverWait(self.driver, 5)
        try:
            perfil_label = wait.until(EC.element_to_be_clickable((By.TAG_NAME, "label")))
            perfil_label.click()
            btn_salvar = self.driver.find_element(By.NAME, "ctl00$cnt$btnSalvar")
            btn_salvar.click()
            self.log("[OK] Perfil selecionado.")
        except:
            self.log("[INFO] Tela de perfil não apareceu ou já foi passada.")

    def ir_para_distribuir_material(self):
        self.log("Indo para 'Distribuir Material'...")
        wait = WebDriverWait(self.driver, 10)
        try:
            link_distribuir = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/home/responsavel?acao=creditos')]")))
            link_distribuir.click()
            self.log("[OK] Tela de distribuição acessada.")
        except:
            self.log("[INFO] Botão não encontrado, usando link direto...")
            self.driver.get("https://cursos.ibad.com.br/home/responsavel?acao=creditos")

    def selecionar_filtros(self, disciplina_nome):
        self.log(f"Configurando filtros para: {disciplina_nome}")
        wait = WebDriverWait(self.driver, 15)
        try:
            # Material
            wait.until(EC.element_to_be_clickable((By.ID, "select2-cnt_lstTipo-container"))).click()
            wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@id, 'material-gratuito-prova-e-videoaula')]"))).click()
            time.sleep(2)
            
            # Disciplina
            # Limpa quebras de linha acidentais (se o usuário copiar/colar da web)
            disciplina_limpa = disciplina_nome.replace('\n', ' ').strip()
            
            wait.until(EC.element_to_be_clickable((By.ID, "select2-cnt_lstLivros-container"))).click()
            search = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "select2-search__field")))
            # Digita apenas o começo do texto para garantir que ele ache sem erros de digitação do final
            texto_busca = disciplina_limpa.split('-')[0].strip() if '-' in disciplina_limpa else disciplina_limpa
            search.send_keys(texto_busca)
            time.sleep(1)
            
            # Pressiona ENTER nativamente para pegar a primeira sugestão que brilhou na tela!
            search.send_keys(Keys.ENTER)
            self.log(f"[OK] Filtros aplicados para: {disciplina_limpa}")
            return True
        except Exception as e:
            self.log(f"[ERRO] Falha nos filtros: {e}")
            return False

    def processar_alunos_lista(self, alunos):
        """
        Percorre a lista de nomes filtrados e realiza a seleção de cada um no sistema IBAD.
        
        Args:
            alunos (list): Lista com nomes dos alunos encontrados na planilha.
        """
        self.log(f"Iniciando processamento de {len(alunos)} alunos.")
        resultados = [] # Lista para guardar o status de cada aluno
        
        try:
            wait = WebDriverWait(self.driver, 10)
            # XPath do campo de alunos
            xpath_campo_aluno = "//*[@id='cnt_divAlunos']/div/div[1]/div/span[2]/span[1]/span/ul/li/input"
            
            for nome in alunos:
                if not self.running:
                    self.log("::: EXECUÇÃO INTERROMPIDA PELO USUÁRIO :::")
                    break
                    
                self.log(f"Processando Aluno: {nome}")
                status = "Sucesso"
                obs = ""
                tentativas = 0
                max_tentativas = 3
                
                # Loop de Redundância (Retry) para erros de Stale Element
                while tentativas < max_tentativas:
                    try:
                        def get_campo():
                            return wait.until(EC.presence_of_element_located((By.XPATH, xpath_campo_aluno)))

                        campo = get_campo()

                        # Scroll + foco
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo)
                        time.sleep(0.5)
                        campo.click()

                        # Limpa e digita
                        campo.clear() # Método oficial e seguro para limpar input
                        campo.send_keys(nome)

                        # Espera resultados aparecerem
                        wait_curto = WebDriverWait(self.driver, 5)
                        wait_curto.until(EC.presence_of_element_located((By.XPATH, "//li[contains(@class,'select2-results__option')]")))

                        # Se o resultado for literalmente a mensagem de "Não encontrado" do Select2, aborta esse aluno
                        if self.driver.find_elements(By.XPATH, "//li[contains(@class, 'select2-results__message')]"):
                            self.log(f"[AVISO] Aluno '{nome}' não encontrado no banco de dados.")
                            status = "Não Encontrado"
                            obs = "O site retornou 'No results found'."
                            for _ in range(20): campo.send_keys(Keys.BACKSPACE) # Limpa gambiarra
                            break

                        # XPath ignorando maiúscula/minúscula
                        nome_lower = nome.lower()
                        xpath_resultado = f"//li[contains(@class,'select2-results__option') and translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = '{nome_lower}']"

                        # Tenta achar o match exato IMEDIATAMENTE (sem esperar 5 segundos de timeout)
                        opcoes_exatas = self.driver.find_elements(By.XPATH, xpath_resultado)
                        
                        if opcoes_exatas:
                            opcoes_exatas[0].click()
                            status = "Sucesso"
                            self.log(f"[OK] Aluno {nome} selecionado (match exato).")
                        else:
                            # Fallback instantâneo: se não achou exato, mas achou alguém, dá ENTER!
                            campo.send_keys(Keys.ENTER)
                            status = "Sucesso (Fallback)"
                            self.log(f"[OK] Aluno {nome} selecionado rapidamente via ENTER.")

                        time.sleep(0.5) # Pausa mínima
                        break # SUCESSO! Sai do loop de tentativas
                            
                    except Exception as e:
                        tentativas += 1
                        if "stale element reference" in str(e).lower() and tentativas < max_tentativas:
                            self.log(f"[RETRY] Tentativa {tentativas}/{max_tentativas} para {nome}")
                            time.sleep(1)
                            continue
                        else:
                            status = "Erro"
                            obs = str(e)
                            self.log(f"[ERRO] Falha ao processar {nome}")
                            break
                
                # Registra o resultado para o relatório
                resultados.append({"Nome": nome, "Status": status, "Observação": obs})
                time.sleep(1)

            # GERAÇÃO DO RELATÓRIO FINAL EM CSV
            df_relatorio = pd.DataFrame(resultados)
            relatorio_path = "relatorio_final.csv"
            df_relatorio.to_csv(relatorio_path, index=False, encoding='utf-8-sig')
            
            # Resumo estatístico para o log
            sucessos = len(df_relatorio[df_relatorio['Status'].str.contains('Sucesso', na=False)])
            nao_encontrados = len(df_relatorio[df_relatorio['Status'] == 'Não Encontrado'])
            erros_tecnicos = len(df_relatorio[df_relatorio['Status'] == 'Erro'])

            self.log(f"\n::: RELATÓRIO GERADO: {relatorio_path} :::")
            self.log(f"✅ Sucessos: {sucessos}")
            self.log(f"⚠️ Não Encontrados: {nao_encontrados}")
            self.log(f"❌ Erros Técnicos: {erros_tecnicos}")
            
            total_real = sucessos + nao_encontrados + erros_tecnicos
            self.log(f"📊 Total Processado: {total_real}")
            
        except Exception as e:
            self.log(f"Erro fatal no processamento: {e}")

    def fechar(self):
        if self.driver:
            self.driver.quit()
            self.log("Navegador fechado.")

if __name__ == "__main__":
    # Mantém compatibilidade com execução via script direto se necessário
    automator = IbadAutomator()
    automator.iniciar_driver()
    automator.verificar_login()
    automator.escolher_perfil()
    automator.ir_para_distribuir_material()
    automator.selecionar_filtros(os.getenv("DISCIPLINA_NOME"))
    time.sleep(5)
    automator.fechar()
