import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import mido
import pydirectinput
import threading
import time
import os
import keyboard

pydirectinput.PAUSE = 0.01

MAPAS = {
    "Completo (37 Teclas)": {
        48: 'l', 49: ';', 50: '.', 51: ',', 52: '/', 53: 'o', 54: '0', 55: 'p', 56: '-', 57: '[', 58: '=', 59: ']',
        60: 'z', 61: 's', 62: 'x', 63: 'd', 64: 'c', 65: 'v', 66: 'g', 67: 'b', 68: 'h', 69: 'n', 70: 'j', 71: 'm',
        72: 'q', 73: '2', 74: 'w', 75: '3', 76: 'e', 77: 'r', 78: '5', 79: 't', 80: '6', 81: 'y', 82: '7', 83: 'u', 84: 'i'
    },
    "Simplificado (15 Teclas)": {
        60: 'a', 62: 's', 64: 'd', 65: 'f', 67: 'g', 69: 'h', 71: 'j',
        72: 'q', 74: 'w', 76: 'e', 77: 'r', 79: 't', 81: 'y', 83: 'u', 84: 'i'
    }
}

ctk.set_appearance_mode("light") 

class HeartopiaPlayer(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("🎵 Heartopia Player 🎵")
        self.geometry("460x480")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        # Paleta Lúdica com Cores Vivas e Fortes
        self.cor_fundo_app = "#9C88FF"   # Violeta Vibrante
        self.cor_painel = "#FFFFFF"      # Branco Puro para destacar as cores
        self.cor_texto = "#2F3640"       # Cinza Escuro quase preto
        self.cor_destaque = "#E84393"    # Rosa Choque (Sliders e Switches)
        
        self.configure(fg_color=self.cor_fundo_app)

        # --- ÍCONE COM ARQUIVO PNG (Adeus Pena!) ---
        try:
            # Basta salvar qualquer png de nota musical como 'icone_musica.png' na mesma pasta
            img_icone = tk.PhotoImage(file="icone_musica.png")
            self.iconphoto(False, img_icone)
        except Exception:
            pass # Se a imagem não for encontrada, o programa abre normalmente sem crashar

        # Variáveis de controle
        self.arquivo_midi = None
        self.tocando = False
        self.nome_mapa_atual = "Completo (37 Teclas)"
        self.mapa_atual = MAPAS[self.nome_mapa_atual]
        self.canais_disponiveis = ["Todos os Canais"]
        self.duracao_total = 0
        
        self.protocol("WM_DELETE_WINDOW", self.ao_fechar)
        keyboard.add_hotkey('esc', self.parar_musica)

        # --- Abas ---
        self.tabview = ctk.CTkTabview(self, width=420, height=420, corner_radius=20, 
                                      fg_color=self.cor_painel, 
                                      segmented_button_fg_color="#DCDDE1",
                                      segmented_button_selected_color="#00A8FF", # Azul Céu Vivo
                                      segmented_button_selected_hover_color="#0097E6")
        self.tabview.pack(padx=20, pady=15, fill="both", expand=True)

        self.tabview._segmented_button.configure(text_color=self.cor_texto, font=("Arial", 14, "bold"))

        self.aba_musica = self.tabview.add("🎵 Música")
        self.aba_config = self.tabview.add("⚙️ Configs")

        self.construir_aba_musica()
        self.construir_aba_config()

    def construir_aba_musica(self):
        # Botão Carregar (Azul Vivo)
        self.btn_carregar = ctk.CTkButton(self.aba_musica, text="📂 ESCOLHER MÚSICA", 
                                          command=self.carregar_midi, corner_radius=15,
                                          fg_color="#00A8FF", hover_color="#0097E6", 
                                          text_color="white", font=("Arial", 14, "bold"), height=40)
        self.btn_carregar.pack(pady=(20, 10))

        self.lbl_arquivo = ctk.CTkLabel(self.aba_musica, text="Nenhuma música carregada...", text_color="#718093", font=("Arial", 12, "bold"))
        self.lbl_arquivo.pack(pady=5)

        # Barra de Progresso (Rosa Choque)
        self.progress = ctk.CTkProgressBar(self.aba_musica, width=360, height=15, corner_radius=10, progress_color=self.cor_destaque, fg_color="#F5F6FA")
        self.progress.set(0)
        self.progress.pack(pady=20)

        # Container Fixo para os Botões
        frame_botoes = ctk.CTkFrame(self.aba_musica, fg_color="transparent", width=380, height=120)
        frame_botoes.pack_propagate(False) 
        frame_botoes.pack(pady=5)

        # Botão Tocar (Verde Limão Super Vivo)
        self.btn_tocar = ctk.CTkButton(frame_botoes, text="▶️ TOCAR AGORA", 
                                       command=self.iniciar_thread, state="disabled", corner_radius=20,
                                       fg_color="#4CD137", hover_color="#44BD32", text_color="black", text_color_disabled="black",
                                       font=("Arial", 16, "bold"), width=300, height=45)
        self.btn_tocar.pack(pady=8)

        # Botão Parar (Vermelho Fogo)
        self.btn_parar = ctk.CTkButton(frame_botoes, text="⏹️ PARAR MÚSICA", 
                                       command=self.parar_musica, state="disabled", corner_radius=20,
                                       fg_color="#E84118", hover_color="#C23616", text_color="black", text_color_disabled="black",
                                       font=("Arial", 14, "bold"), width=300, height=40)
        self.btn_parar.pack(pady=4)
        
        self.lbl_status = ctk.CTkLabel(self.aba_musica, text="Pronto para começar!", text_color=self.cor_texto, font=("Arial", 13, "bold"))
        self.lbl_status.pack(pady=5)

    def construir_aba_config(self):
        # Instrumento
        ctk.CTkLabel(self.aba_config, text="🎹 Instrumento:", text_color=self.cor_texto, font=("Arial", 13, "bold")).pack(pady=(15, 2))
        self.combo_inst = ctk.CTkOptionMenu(self.aba_config, values=list(MAPAS.keys()), 
                                            command=self.mudar_instrumento, corner_radius=10, 
                                            fg_color="#DCDDE1", button_color="#00A8FF", button_hover_color="#0097E6",
                                            text_color=self.cor_texto, width=240, font=("Arial", 12, "bold"))
        self.combo_inst.pack(pady=5)

        # Canal
        ctk.CTkLabel(self.aba_config, text="🎧 Filtrar Canal:", text_color=self.cor_texto, font=("Arial", 13, "bold")).pack(pady=(10, 2))
        self.combo_canal = ctk.CTkOptionMenu(self.aba_config, values=self.canais_disponiveis, 
                                             corner_radius=10, fg_color="#DCDDE1", button_color="#00A8FF", button_hover_color="#0097E6",
                                             text_color=self.cor_texto, width=240, font=("Arial", 12, "bold"))
        self.combo_canal.pack(pady=5)

        # Switch (Rosa Choque)
        self.usar_conversao = ctk.BooleanVar(value=True)
        self.switch_conv = ctk.CTkSwitch(self.aba_config, text="Converter notas mágicas", 
                                         variable=self.usar_conversao, progress_color=self.cor_destaque,
                                         text_color=self.cor_texto, font=("Arial", 13, "bold"))
        self.switch_conv.pack(pady=15)

        # Transposição
        self.lbl_transp = ctk.CTkLabel(self.aba_config, text="🎵 Ajuste de Tom: 0", text_color=self.cor_texto, font=("Arial", 13, "bold"))
        self.lbl_transp.pack()
        self.slider_transp = ctk.CTkSlider(self.aba_config, from_=-24, to=24, number_of_steps=48, 
                                           command=self.atualizar_label_transp, button_color=self.cor_destaque, progress_color=self.cor_destaque)
        self.slider_transp.set(0)
        self.slider_transp.pack(pady=5)

        # Velocidade
        self.lbl_vel = ctk.CTkLabel(self.aba_config, text="🐇 Velocidade: 1.0x", text_color=self.cor_texto, font=("Arial", 13, "bold"))
        self.lbl_vel.pack(pady=(10, 0))
        self.slider_vel = ctk.CTkSlider(self.aba_config, from_=0.5, to=2.0, number_of_steps=15, 
                                        command=self.atualizar_label_vel, button_color=self.cor_destaque, progress_color=self.cor_destaque)
        self.slider_vel.set(1.0)
        self.slider_vel.pack(pady=5)

    def atualizar_label_transp(self, valor):
        self.lbl_transp.configure(text=f"🎵 Ajuste de Tom: {int(valor)}")

    def atualizar_label_vel(self, valor):
        self.lbl_vel.configure(text=f"🐇 Velocidade: {valor:.1f}x")

    def ao_fechar(self):
        self.tocando = False
        self.after(100, self.destroy)

    def mudar_instrumento(self, valor_selecionado):
        self.nome_mapa_atual = valor_selecionado
        self.mapa_atual = MAPAS[self.nome_mapa_atual]

    def carregar_midi(self):
        arquivo = filedialog.askopenfilename(filetypes=[("MIDI", "*.mid")])
        if arquivo:
            self.arquivo_midi = arquivo
            nome_arq = os.path.basename(arquivo)
            if len(nome_arq) > 30: nome_arq = nome_arq[:27] + "..."
            self.lbl_arquivo.configure(text=f"🎶 {nome_arq}", text_color=self.cor_destaque)
            self.btn_tocar.configure(state="normal")
            self.analisar_midi(arquivo)

    def analisar_midi(self, arquivo):
        try:
            mid = mido.MidiFile(arquivo)
            self.duracao_total = mid.length
            canais = set()
            for msg in mid:
                if hasattr(msg, 'channel'):
                    canais.add(msg.channel)
            
            self.canais_disponiveis = ["Todos os Canais"] + [f"Canal {c}" for c in sorted(canais)]
            self.combo_canal.configure(values=self.canais_disponiveis)
            self.combo_canal.set("Todos os Canais")
            self.progress.set(0)
        except Exception as e:
            print(f"Erro ao analisar MIDI: {e}")

    def iniciar_thread(self):
        if not self.arquivo_midi: return
        self.tocando = True
        self.btn_tocar.configure(state="disabled")
        self.btn_parar.configure(state="normal")
        self.combo_inst.configure(state="disabled")
        threading.Thread(target=self.tocar_musica, daemon=True).start()

    def parar_musica(self):
        self.tocando = False

    def encontrar_tecla_mais_proxima(self, nota_midi):
        notas_disponiveis = list(self.mapa_atual.keys())
        nota_proxima = min(notas_disponiveis, key=lambda x: abs(x - nota_midi))
        return self.mapa_atual[nota_proxima]
        
    def atualizar_progresso(self, valor):
        self.progress.set(valor / 100.0)

    def tocar_musica(self):
        notas_ativas = {}

        try:
            mid = mido.MidiFile(self.arquivo_midi)
            
            for i in range(3, 0, -1):
                if not self.tocando: return
                self.lbl_status.configure(text=f"🚀 Injetando magia em {i}...")
                time.sleep(1)

            self.lbl_status.configure(text=f"✨ Tocando as notas! ✨", text_color="#4CD137")
            
            start_time = time.time()
            input_time = 0.0
            
            velocidade = self.slider_vel.get()
            transposicao = int(self.slider_transp.get())
            canal_selecionado = self.combo_canal.get()
            
            for msg in mid:
                if not self.tocando: break

                input_time += (msg.time / velocidade)
                playback_time = time.time() - start_time
                duration = input_time - playback_time
                
                if duration > 0:
                    time.sleep(duration)

                if self.duracao_total > 0:
                    progresso_atual = (input_time / (self.duracao_total / velocidade)) * 100
                    self.after(0, self.atualizar_progresso, progresso_atual)

                if canal_selecionado != "Todos os Canais" and hasattr(msg, 'channel'):
                    canal_num = int(canal_selecionado.split(" ")[1])
                    if msg.channel != canal_num:
                        continue 

                if msg.type == 'note_on' and msg.velocity > 0:
                    nota_ajustada = msg.note + transposicao
                    tecla = None
                    
                    if nota_ajustada in self.mapa_atual:
                        tecla = self.mapa_atual[nota_ajustada]
                    elif self.usar_conversao.get():
                        tecla = self.encontrar_tecla_mais_proxima(nota_ajustada)
                    
                    if tecla:
                        if msg.note in notas_ativas:
                            pydirectinput.keyUp(notas_ativas[msg.note])
                        
                        pydirectinput.keyDown(tecla)
                        notas_ativas[msg.note] = tecla

                elif (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
                    if msg.note in notas_ativas:
                        tecla_para_soltar = notas_ativas.pop(msg.note)
                        pydirectinput.keyUp(tecla_para_soltar)

            self.lbl_status.configure(text="🎉 Música finalizada!", text_color=self.cor_texto)
            self.after(0, self.atualizar_progresso, 100)

        except Exception as e:
            self.lbl_status.configure(text="❌ Erro ao ler as notas.", text_color="#E84118")
            print(e)
        
        finally:
            for tecla in notas_ativas.values():
                pydirectinput.keyUp(tecla)
            notas_ativas.clear()
            
            self.tocando = False
            self.btn_tocar.configure(state="normal")
            self.btn_parar.configure(state="disabled")
            self.combo_inst.configure(state="normal")

if __name__ == "__main__":
    app = HeartopiaPlayer()
    app.mainloop()