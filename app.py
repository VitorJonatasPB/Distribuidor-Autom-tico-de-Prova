import os
import threading
import customtkinter as ctk
from tkinter import filedialog
from main import IbadAutomator
from dotenv import load_dotenv, set_key

# Configuração visual do CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        load_dotenv()
        self.env_path = os.path.join(os.getcwd(), ".env")

        # Configuração da Janela
        self.title("Distribuidor Automático de Provas")
        self.geometry("800x650")
        self.automator = None  # Referência para o automator

        # Layout em Grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---- Sidebar de Configurações ----
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Pipeline Prova",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Origem dos Dados
        self.source_label = ctk.CTkLabel(self.sidebar_frame, text="Origem dos Dados:")
        self.source_label.grid(row=1, column=0, padx=20, pady=(10, 0))
        self.source_seg = ctk.CTkSegmentedButton(
            self.sidebar_frame,
            values=["Computador", "Google Sheets/Web"],
            command=self.toggle_source,
        )
        self.source_seg.grid(row=2, column=0, padx=20, pady=(5, 10))
        self.source_seg.set("Computador")

        # Entrada de Dados (Arquivo ou Link)
        self.path_entry = ctk.CTkEntry(
            self.sidebar_frame, placeholder_text="Caminho ou Link..."
        )
        self.path_entry.grid(row=3, column=0, padx=20, pady=5)

        self.file_button = ctk.CTkButton(
            self.sidebar_frame, text="Selecionar Arquivo", command=self.select_file
        )
        self.file_button.grid(row=4, column=0, padx=20, pady=5)

        # Inicializa o estado correto (Computador) após criar os botões
        self.toggle_source("Computador")

        # Configuração da Disciplina
        self.discipline_label = ctk.CTkLabel(
            self.sidebar_frame, text="Nome da Disciplina:"
        )
        self.discipline_label.grid(row=5, column=0, padx=20, pady=(15, 0))
        self.discipline_entry = ctk.CTkEntry(
            self.sidebar_frame, placeholder_text="Ex: Teologia"
        )
        self.discipline_entry.grid(row=6, column=0, padx=20, pady=5)
        # Define o padrão como TEOLOGIA se não houver nada salvo no .env
        self.discipline_entry.insert(0, os.getenv("DISCIPLINA_NOME") or "TEOLOGIA")

        # Configuração de Filtro Dinâmico
        self.filter_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.filter_frame.grid(row=7, column=0, padx=10, pady=10)

        self.col_label = ctk.CTkLabel(
            self.filter_frame, text="Coluna Filtro:", font=ctk.CTkFont(size=11)
        )
        self.col_label.grid(row=0, column=0, padx=5)
        self.col_entry = ctk.CTkEntry(
            self.filter_frame, width=80, placeholder_text="L10"
        )
        self.col_entry.grid(row=1, column=0, padx=5)
        self.col_entry.insert(0, "L10")

        self.val_label = ctk.CTkLabel(
            self.filter_frame, text="Valor Filtro:", font=ctk.CTkFont(size=11)
        )
        self.val_label.grid(row=0, column=1, padx=5)
        self.val_entry = ctk.CTkEntry(
            self.filter_frame, width=80, placeholder_text="✅"
        )
        self.val_entry.grid(row=1, column=1, padx=5)
        self.val_entry.insert(0, "✅")

        # ---- Área Principal ----
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Painel de Controle",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=20)

        # Log
        self.textbox = ctk.CTkTextbox(self.main_frame, width=400, height=300)
        self.textbox.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.textbox.insert(
            "0.0", "Pipeline carregada. Configure os filtros e a origem.\n\n"
        )

        # Botão Ação
        self.btn_start = ctk.CTkButton(
            self.main_frame,
            text="INICIAR",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            command=self.start_pipeline,
        )
        self.btn_start.grid(row=2, column=0, padx=20, pady=(20, 10), sticky="ew")

        self.btn_stop = ctk.CTkButton(
            self.main_frame,
            text="PARAR EXECUÇÃO",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="#d32f2f",
            hover_color="#9a0007",
            command=self.stop_pipeline,
            state="disabled",
        )
        self.btn_stop.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")

        self.btn_login = ctk.CTkButton(
            self.main_frame,
            text="Abrir Navegador (Login/Cookies)",
            fg_color="transparent",
            border_width=2,
            command=self.open_login_page,
        )
        self.btn_login.grid(row=4, column=0, padx=20, pady=(0, 20))

    def log(self, message):
        self.textbox.insert("end", f"> {message}\n")
        self.textbox.see("end")

    def toggle_source(self, value):
        self.path_entry.delete(0, "end")
        if value == "Computador":
            self.file_button.grid(row=4, column=0, padx=20, pady=5)
            self.path_entry.configure(placeholder_text="Caminho do arquivo local...")
            # Tenta recuperar o último caminho salvo
            self.path_entry.insert(0, os.getenv("PLANILHA_NOME") or "")
        else:
            self.file_button.grid_forget()
            self.path_entry.configure(
                placeholder_text="Cole o link do Google Sheets aqui..."
            )
            self.log(
                "Dica: Certifique-se que a planilha está compartilhada como 'Qualquer pessoa com o link'."
            )

    def select_file(self):
        file = filedialog.askopenfilename(
            filetypes=[("Planilhas", "*.xlsx *.xls *.csv")]
        )
        if file:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, file)
            self.log(f"Arquivo selecionado: {os.path.basename(file)}")

    def start_pipeline(self):
        self.btn_start.configure(state="disabled", text="EXECUTANDO...")
        self.btn_stop.configure(state="normal")
        threading.Thread(target=self.run_pipeline, daemon=True).start()

    def stop_pipeline(self):
        if self.automator:
            self.automator.parar()
            self.btn_stop.configure(state="disabled", text="PARANDO...")

    def run_pipeline(self):
        try:
            origem = self.source_seg.get()
            dados_raw = self.path_entry.get()
            coluna = self.col_entry.get()
            valor = self.val_entry.get()
            disciplina = self.discipline_entry.get()

            self.automator = IbadAutomator(log_callback=self.log)

            # PASSO 1: Carga e Filtro Dinâmico
            alunos = self.automator.carregar_e_filtrar_dados(
                origem, dados_raw, coluna, valor
            )

            if not alunos:
                self.log("::: PIPELINE ABORTADA: Nenhum dado filtrado :::")
                return

            # PASSO 2: Automação Web
            self.automator.iniciar_driver()
            self.automator.verificar_login()
            self.automator.escolher_perfil()
            self.automator.ir_para_distribuir_material()

            if self.automator.selecionar_filtros(disciplina):
                self.automator.processar_alunos_lista(alunos)

            self.log("::: PIPELINE FINALIZADA :::")

        except Exception as e:
            self.log(f"ERRO NA PIPELINE: {e}")
        finally:
            self.btn_start.configure(state="normal", text="INICIAR PIPELINE")
            self.btn_stop.configure(state="disabled", text="PARAR EXECUÇÃO")
            self.automator = None

    def open_login_page(self):
        threading.Thread(target=self._just_open_login, daemon=True).start()

    def _just_open_login(self):
        automator = IbadAutomator(log_callback=self.log)
        automator.iniciar_driver()
        automator.driver.get("https://cursos.ibad.com.br/entrar")
        self.log("Navegador aberto para login manual.")


if __name__ == "__main__":
    app = App()
    app.mainloop()
