import os
import threading
import customtkinter as ctk
from commands import processar_comando
from memory import (
    criar_usuario, 
    autenticar_usuario, 
    criar_sessao, 
    obter_session_id_por_token,
    adicionar_mensagem_chat, 
    obter_historico_chat,
    logout_usuario, 
    verificar_usuario_existe,
    verificar_autenticacao_persistente
)

# Configurações de Aparência CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# ================== CONFIGURAÇÃO DE PERSISTÊNCIA LOCAL ==================
SESSION_FILE = ".jarvis_session"

def salvar_login_local(username, token):
    with open(SESSION_FILE, "w") as f:
        f.write(f"{username}\n{token}")

def carregar_login_local():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            dados = f.read().splitlines()
            if len(dados) == 2:
                return dados[0], dados[1]
    return None, None

def limpar_login_local():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

# ================== INTERFACE GRÁFICA (GUI) ==================

from tkinter import filedialog

class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("J.A.R.V.I.S — System Assistant v4.0.0")
        self.geometry("1100x700")
        
        # Session Data
        self.username = None
        self.token = None
        self.session_id = None

        # Layout Principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Inicialização (Tenta auto-login se existir sessão válida)
        self.show_login_screen()
        self.check_auto_login()

    def check_auto_login(self):
        u, t = carregar_login_local()
        if u and t and verificar_autenticacao_persistente(t):
            self.login_success(u, t)

    def show_login_screen(self):
        if hasattr(self, 'main_frame') and self.main_frame:
            self.main_frame.destroy()
        self.login_frame = LoginFrame(self, self.login_success)
        self.login_frame.grid(row=0, column=0, sticky="nsew")

    def login_success(self, username, token):
        self.username = username
        self.token = token
        self.session_id = obter_session_id_por_token(token)
        if not self.session_id:
            self.session_id = criar_sessao(username, token)
        
        salvar_login_local(username, token)
        
        if hasattr(self, 'login_frame'):
            self.login_frame.destroy()
        
        self.main_frame = MainFrame(self, self.username, self.logout)
        self.main_frame.grid(row=0, column=0, sticky="nsew")

    def logout(self):
        logout_usuario(self.username, self.token)
        limpar_login_local()
        self.username = None
        self.token = None
        self.show_login_screen()

class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, login_callback):
        super().__init__(master, fg_color="#0A0A0A")
        self.login_callback = login_callback

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 5), weight=1)

        # Botão de Registro (Novo)
        self.reg_btn = ctk.CTkButton(self, text="CRIAR CONTA", command=self.show_register, 
                                     fg_color="transparent", border_width=1, border_color="#00FFFF", width=120)
        self.reg_btn.grid(row=0, column=0, sticky="ne", padx=20, pady=20)

        # Estilo Neon
        self.title_label = ctk.CTkLabel(self, text="J.A.R.V.I.S", font=ctk.CTkFont(size=50, weight="bold"), text_color="#00FFFF")
        self.title_label.grid(row=1, column=0, pady=(0, 5))

        self.subtitle = ctk.CTkLabel(self, text="ADVANCED SYSTEM ASSISTANT", font=ctk.CTkFont(size=12), text_color="#B026FF")
        self.subtitle.grid(row=2, column=0, pady=(0, 40))

        # Container Central
        self.form = ctk.CTkFrame(self, fg_color="transparent")
        self.form.grid(row=3, column=0)

        self.user_entry = ctk.CTkEntry(self.form, placeholder_text="LOGIN", width=320, height=50, border_color="#00FFFF", fg_color="#1A1A1A")
        self.user_entry.pack(pady=10)

        self.pass_entry = ctk.CTkEntry(self.form, placeholder_text="SENHA", show="*", width=320, height=50, border_color="#00FFFF", fg_color="#1A1A1A")
        self.pass_entry.pack(pady=10)

        self.login_btn = ctk.CTkButton(self.form, text="ENTRAR", command=self.do_login, width=320, height=50, 
                                       fg_color="#B026FF", hover_color="#8A1FCC", font=ctk.CTkFont(weight="bold"))
        self.login_btn.pack(pady=25)

        self.status_label = ctk.CTkLabel(self, text="STATUS: AGUARDANDO AUTENTICAÇÃO", font=ctk.CTkFont(size=10), text_color="gray")
        self.status_label.grid(row=4, column=0, pady=20)

    def do_login(self):
        u = self.user_entry.get()
        p = self.pass_entry.get()
        token, _ = autenticar_usuario(u, p)
        if token:
            self.login_callback(u, token)
        else:
            self.status_label.configure(text="STATUS: FALHA NA AUTENTICAÇÃO", text_color="red")

    def show_register(self):
        # Janela de diálogo para registro rápido
        dialog = ctk.CTkInputDialog(text="Digite o novo nome de usuário:", title="Registro")
        u = dialog.get_input()
        if u:
            if verificar_usuario_existe(u):
                self.status_label.configure(text="STATUS: USUÁRIO JÁ EXISTE", text_color="orange")
                return
            dialog_p = ctk.CTkInputDialog(text="Digite a senha para o novo usuário:", title="Registro")
            p = dialog_p.get_input()
            if p:
                criar_usuario(u, p)
                self.status_label.configure(text="STATUS: CONTA CRIADA! FAÇA LOGIN", text_color="green")

class MainFrame(ctk.CTkFrame):
    def __init__(self, master, username, logout_callback):
        super().__init__(master, fg_color="#050505")
        self.master = master
        self.username = username
        self.logout_callback = logout_callback

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar Lateral
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#0A0A0A", border_color="#1A1A1A", border_width=1)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.logo = ctk.CTkLabel(self.sidebar, text="JARVIS Core", font=ctk.CTkFont(size=20, weight="bold"), text_color="#00FFFF")
        self.logo.pack(pady=40)

        self.info_box = ctk.CTkFrame(self.sidebar, fg_color="#151515", corner_radius=10)
        self.info_box.pack(padx=20, pady=10, fill="x")
        
        ctk.CTkLabel(self.info_box, text="OPERADOR ATIVO", font=ctk.CTkFont(size=10), text_color="gray").pack(pady=(10, 0))
        self.user_lbl = ctk.CTkLabel(self.info_box, text=self.username.upper(), font=ctk.CTkFont(size=14, weight="bold"), text_color="#B026FF")
        self.user_lbl.pack(pady=(0, 10))

        # Menu
        self.create_side_btn("🌐 Abrir Site", lambda: self.open_site_dialog())
        self.create_side_btn("📻 Tocar Música", lambda: self.play_music_dialog())
        self.create_side_btn("📅 Ver Agenda", lambda: self.quick_cmd("ver agenda"))

        self.logout_btn = ctk.CTkButton(self.sidebar, text="ENCERRAR SESSÃO", command=self.logout_callback, 
                                        fg_color="transparent", border_width=1, border_color="#FF3333", text_color="#FF3333")
        self.logout_btn.pack(side="bottom", pady=30, padx=20, fill="x")

        # Chat
        self.center_area = ctk.CTkFrame(self, fg_color="transparent")
        self.center_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.center_area.grid_columnconfigure(0, weight=1)
        self.center_area.grid_rowconfigure(0, weight=1)

        self.chat_display = ctk.CTkTextbox(self.center_area, fg_color="#0D0D0D", border_color="#1A1A1A", border_width=1, 
                                          font=("Consolas", 14), corner_radius=15, text_color="#E0E0E0")
        self.chat_display.grid(row=0, column=0, sticky="nsew", pady=(0, 20))
        self.chat_display.configure(state="disabled")

        # Input Area (Nova com botões de Upload e Voz)
        self.input_frame = ctk.CTkFrame(self.center_area, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)

        # Botão Upload (Imagens/Documentos)
        self.upload_btn = ctk.CTkButton(self.input_frame, text="+", width=50, height=55, fg_color="#1A1A1A", 
                                        border_width=1, border_color="#B026FF", text_color="#B026FF", 
                                        font=ctk.CTkFont(size=20, weight="bold"), command=self.upload_file)
        self.upload_btn.grid(row=0, column=0, padx=(0, 10))

        self.entry = ctk.CTkEntry(self.input_frame, placeholder_text="Fale ou digite um comando...", height=55, 
                                 border_color="#B026FF", fg_color="#0D0D0D", font=("Segoe UI", 14))
        self.entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self.send_command())

        # Botão Voz
        self.voice_btn = ctk.CTkButton(self.input_frame, text="🎤", width=50, height=55, fg_color="#1A1A1A", 
                                       border_width=1, border_color="#00FFFF", text_color="#00FFFF", 
                                       font=ctk.CTkFont(size=20), command=self.start_voice_mode)
        self.voice_btn.grid(row=0, column=2, padx=(0, 10))

        self.send_btn = ctk.CTkButton(self.input_frame, text="▶", width=80, height=55, command=self.send_command,
                                     fg_color="#00FFFF", text_color="black", font=ctk.CTkFont(weight="bold"))
        self.send_btn.grid(row=0, column=3)

        self.log_event("Sinal de rede estável. Núcleo v4.0.0 em prontidão.")

    def create_side_btn(self, text, command_fn):
        btn = ctk.CTkButton(self.sidebar, text=text, anchor="w", fg_color="transparent", 
                           hover_color="#151515", text_color="#D0D0D0", command=command_fn)
        btn.pack(padx=15, pady=2, fill="x")

    def open_site_dialog(self):
        dialog = ctk.CTkInputDialog(text="Qual site o senhor deseja abrir?", title="Abrir Site")
        site = dialog.get_input()
        if site:
            self.quick_cmd(f"abrir {site}")

    def play_music_dialog(self):
        dialog = ctk.CTkInputDialog(text="Qual música o senhor deseja ouvir?", title="Tocar Música")
        musica = dialog.get_input()
        if musica:
            self.quick_cmd(f"tocar {musica}")

    def quick_cmd(self, cmd):
        self.entry.delete(0, "end")
        self.entry.insert(0, cmd)
        self.send_command()

    def upload_file(self):
        file_path = filedialog.askopenfilename(
            title="Selecionar Arquivo",
            filetypes=[("Todos os arquivos", "*.*"), ("Imagens", "*.png *.jpg *.jpeg"), ("Documentos", "*.pdf *.docx *.txt")]
        )
        if file_path:
            self.entry.delete(0, "end")
            # Se for imagem, formata comando de análise
            ext = file_path.lower().split('.')[-1]
            if ext in ['png', 'jpg', 'jpeg']:
                self.entry.insert(0, f"analisar imagem {file_path}")
            else:
                self.entry.insert(0, f"analisar arquivo {file_path}")
            self.send_command()

    def start_voice_mode(self):
        self.log_event("Modo de voz ativado. Fale agora...", "#B026FF")
        threading.Thread(target=self.voice_backend, daemon=True).start()

    def voice_backend(self):
        # Aqui integraríamos com o comando_voz_interativo. 
        # Por agora, simulamos a ativação do processamento de áudio.
        from commands.voice import ouvir
        audio_text = ouvir()
        if audio_text:
            self.master.after(0, lambda: self.process_voice_result(audio_text))
        else:
            self.master.after(0, lambda: self.log_event("Não consegui ouvir nada, senhor.", "orange"))

    def process_voice_result(self, text):
        self.chat_history_append("VOCÊ (VOZ)", text, "#B026FF")
        threading.Thread(target=self.process_backend, args=(text,), daemon=True).start()

    def log_event(self, msg, color="#00FFFF"):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"\n[SYSTEM] {msg}\n", "system")
        self.chat_display.tag_config("system", foreground=color)
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def send_command(self):
        cmd = self.entry.get().strip()
        if not cmd: return
        
        self.entry.delete(0, "end")
        self.chat_history_append("VOCÊ", cmd, "#FF00FF")
        
        threading.Thread(target=self.process_backend, args=(cmd,), daemon=True).start()

    def chat_history_append(self, author, text, color):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"\n{author}: ", author)
        self.chat_display.tag_config(author, foreground=color)
        self.chat_display.insert("end", f"{text}\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def process_backend(self, cmd):
        res = processar_comando(cmd, self.username, self.master.token)
        self.master.after(0, lambda: self.chat_history_append("JARVIS", res, "#00FFFF"))

if __name__ == "__main__":
    app = JarvisApp()
    app.mainloop()