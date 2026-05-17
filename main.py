import tkinter as tk
from tkinter import filedialog, ttk
import mido
import pydirectinput
import threading
import time
import os
import keyboard  # Nova importação para o botão de emergência

pydirectinput.PAUSE = 0.01

MAPAS = {
    "Piano Completo (37 Teclas)": {
        # Oitava Baixa
        48: 'l', 49: ';', 50: '.', 51: ',', 52: '/', 
        53: 'o', 54: '0', 55: 'p', 56: '-', 57: '[', 58: '=', 59: ']',
        # Oitava Média
        60: 'z', 61: 's', 62: 'x', 63: 'd', 64: 'c', 
        65: 'v', 66: 'g', 67: 'b', 68: 'h', 69: 'n', 70: 'j', 71: 'm',
        # Oitava Alta
        72: 'q', 73: '2', 74: 'w', 75: '3', 76: 'e', 
        77: 'r', 78: '5', 79: 't', 80: '6', 81: 'y', 82: '7', 83: 'u', 84: 'i'
    },
    
    "Simplificado (15 Teclas)": {
        # Linha de Baixo (ASDFGHJ)
        60: 'a', 62: 's', 64: 'd', 65: 'f', 67: 'g', 69: 'h', 71: 'j',
        # Linha de Cima (QWERTYUI)
        72: 'q', 74: 'w', 76: 'e', 77: 'r', 79: 't', 81: 'y', 83: 'u', 84: 'i'
    }
}

class HeartopiaPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Heartopia Player")
        # Aumentámos a janela para acomodar os novos controlos
        self.root.geometry("450x550") 
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)

        self.arquivo_midi = None
        self.tocando = False
        self.nome_mapa_atual = "Piano Completo (37 Teclas)"
        self.mapa_atual = MAPAS[self.nome_mapa_atual]
        self.canais_disponiveis = ["Todos os Canais"]
        self.duracao_total = 0
        
        # --- 4. Tratamento do Fechamento da Janela ---
        self.root.protocol("WM_DELETE_WINDOW", self.ao_fechar)

        # --- 1. Botão de Emergência (Killswitch) ---
        # Pressionar 'ESC' a qualquer momento para a reprodução instantaneamente
        keyboard.add_hotkey('esc', self.parar_musica)

        # --- Interface ---
        self.lbl_titulo = tk.Label(root, text="Heartopia Auto-Player", font=("Arial", 14, "bold"))
        self.lbl_titulo.pack(pady=10)

        self.lbl_inst = tk.Label(root, text="Escolha o Instrumento:", font=("Arial", 10))
        self.lbl_inst.pack()
        
        self.combo_inst = ttk.Combobox(root, values=list(MAPAS.keys()), state="readonly", width=30)
        self.combo_inst.current(0)
        self.combo_inst.bind("<<ComboboxSelected>>", self.mudar_instrumento)
        self.combo_inst.pack(pady=5)

        self.usar_conversao = tk.BooleanVar()
        self.usar_conversao.set(True)
        self.chk_conversao = tk.Checkbutton(root, text="Converter notas desconhecidas", var=self.usar_conversao)
        self.chk_conversao.pack(pady=2)

        # --- 3. Transposição de Notas ---
        frame_transp = tk.Frame(root)
        frame_transp.pack(pady=5)
        tk.Label(frame_transp, text="Transposição (Semitons):").pack(side=tk.LEFT, padx=5)
        self.var_transposicao = tk.IntVar(value=0)
        tk.Spinbox(frame_transp, from_=-24, to=24, textvariable=self.var_transposicao, width=5).pack(side=tk.LEFT)

        # --- 2. Filtragem de Canais ---
        frame_canal = tk.Frame(root)
        frame_canal.pack(pady=5)
        tk.Label(frame_canal, text="Filtrar Canal:").pack(side=tk.LEFT, padx=5)
        self.combo_canal = ttk.Combobox(frame_canal, values=self.canais_disponiveis, state="readonly", width=15)
        self.combo_canal.current(0)
        self.combo_canal.pack(side=tk.LEFT)

        # --- 5. Controlo de Velocidade ---
        frame_vel = tk.Frame(root)
        frame_vel.pack(pady=5)
        tk.Label(frame_vel, text="Velocidade:").pack(side=tk.LEFT, padx=5)
        self.var_velocidade = tk.DoubleVar(value=1.0)
        tk.Scale(frame_vel, from_=0.5, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, variable=self.var_velocidade, length=100).pack(side=tk.LEFT)

        self.btn_carregar = tk.Button(root, text="📂 Carregar MIDI", command=self.carregar_midi)
        self.btn_carregar.pack(pady=10)

        self.lbl_arquivo = tk.Label(root, text="Nenhum ficheiro...", fg="gray")
        self.lbl_arquivo.pack(pady=5)

        # --- 5. Barra de Progresso ---
        self.progress = ttk.Progressbar(root, orient="horizontal", length=350, mode="determinate")
        self.progress.pack(pady=5)

        self.btn_tocar = tk.Button(root, text="▶️ TOCAR (3s)", command=self.iniciar_thread, bg="#4CAF50", fg="white", font=("bold"), state="disabled")
        self.btn_tocar.pack(pady=10)

        self.btn_parar = tk.Button(root, text="⏹️ PARAR (ou pressione ESC)", command=self.parar_musica, bg="#f44336", fg="white", state="disabled")
        self.btn_parar.pack(pady=5)
        
        self.lbl_status = tk.Label(root, text="A aguardar...", fg="blue")
        self.lbl_status.pack(pady=5)

    def ao_fechar(self):
        """Garante que a música para e as teclas são libertadas antes de fechar"""
        self.tocando = False
        # Aguarda 100ms para a thread terminar o ciclo e soltar as teclas
        self.root.after(100, self.root.destroy)

    def mudar_instrumento(self, event):
        self.nome_mapa_atual = self.combo_inst.get()
        self.mapa_atual = MAPAS[self.nome_mapa_atual]

    def carregar_midi(self):
        arquivo = filedialog.askopenfilename(filetypes=[("MIDI", "*.mid")])
        if arquivo:
            self.arquivo_midi = arquivo
            self.lbl_arquivo.config(text=os.path.basename(arquivo), fg="black")
            self.btn_tocar.config(state="normal")
            self.analisar_midi(arquivo)

    def analisar_midi(self, arquivo):
        """Lê o ficheiro MIDI para detetar quais canais têm notas e o tempo total"""
        try:
            mid = mido.MidiFile(arquivo)
            self.duracao_total = mid.length
            canais = set()
            for msg in mid:
                if hasattr(msg, 'channel'):
                    canais.add(msg.channel)
            
            # Atualiza a lista de canais disponíveis na interface
            self.canais_disponiveis = ["Todos os Canais"] + [f"Canal {c}" for c in sorted(canais)]
            self.combo_canal.config(values=self.canais_disponiveis)
            self.combo_canal.current(0)
            self.progress['value'] = 0
        except Exception as e:
            print(f"Erro ao analisar MIDI: {e}")

    def iniciar_thread(self):
        if not self.arquivo_midi: return
        self.tocando = True
        self.btn_tocar.config(state="disabled")
        self.btn_parar.config(state="normal")
        self.combo_inst.config(state="disabled")
        threading.Thread(target=self.tocar_musica, daemon=True).start()

    def parar_musica(self):
        self.tocando = False

    def encontrar_tecla_mais_proxima(self, nota_midi):
        notas_disponiveis = list(self.mapa_atual.keys())
        nota_proxima = min(notas_disponiveis, key=lambda x: abs(x - nota_midi))
        return self.mapa_atual[nota_proxima]
        
    def atualizar_progresso(self, valor):
        """Atualiza a barra de progresso de forma segura através da thread principal"""
        self.progress['value'] = valor

    def tocar_musica(self):
        notas_ativas = {}

        try:
            mid = mido.MidiFile(self.arquivo_midi)
            
            for i in range(3, 0, -1):
                if not self.tocando: return
                self.lbl_status.config(text=f"A começar em {i}...")
                time.sleep(1)

            self.lbl_status.config(text=f"🎵 A tocar ({self.nome_mapa_atual})...")
            
            start_time = time.time()
            input_time = 0.0
            
            # Obter os valores das novas configurações
            velocidade = self.var_velocidade.get()
            transposicao = self.var_transposicao.get()
            canal_selecionado = self.combo_canal.get()
            
            for msg in mid:
                if not self.tocando: break

                # Ajuste de velocidade no tempo de espera
                input_time += (msg.time / velocidade)
                
                playback_time = time.time() - start_time
                duration = input_time - playback_time
                
                if duration > 0:
                    time.sleep(duration)

                # Atualizar Barra de Progresso
                if self.duracao_total > 0:
                    progresso_atual = (input_time / (self.duracao_total / velocidade)) * 100
                    self.root.after(0, self.atualizar_progresso, progresso_atual)

                # Filtragem de Canal
                if canal_selecionado != "Todos os Canais" and hasattr(msg, 'channel'):
                    canal_num = int(canal_selecionado.split(" ")[1])
                    if msg.channel != canal_num:
                        continue # Ignora as notas deste canal e passa para a próxima mensagem

                if msg.type == 'note_on' and msg.velocity > 0:
                    # Aplica a Transposição
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

            self.lbl_status.config(text="Fim da música.")
            self.root.after(0, self.atualizar_progresso, 100)

        except Exception as e:
            self.lbl_status.config(text="Erro ao tocar!")
            print(e)
        
        finally:
            # Garante que as teclas nunca ficam presas
            for tecla in notas_ativas.values():
                pydirectinput.keyUp(tecla)
            notas_ativas.clear()
            
            self.tocando = False
            self.btn_tocar.config(state="normal")
            self.btn_parar.config(state="disabled")
            self.combo_inst.config(state="readonly")

if __name__ == "__main__":
    root = tk.Tk()
    app = HeartopiaPlayer(root)
    root.mainloop()