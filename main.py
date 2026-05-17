import tkinter as tk
from tkinter import filedialog, ttk
import mido
import pydirectinput
import threading
import time
import os

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
        self.root.geometry("400x350")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)

        self.arquivo_midi = None
        self.tocando = False
        self.nome_mapa_atual = "Piano Completo (37 Teclas)"
        self.mapa_atual = MAPAS[self.nome_mapa_atual]
        
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
        
        self.lbl_aviso = tk.Label(root, text="(Segura teclas longas automaticamente)", font=("Arial", 8), fg="green")
        self.lbl_aviso.pack()

        self.btn_carregar = tk.Button(root, text="📂 Carregar MIDI", command=self.carregar_midi)
        self.btn_carregar.pack(pady=10)

        self.lbl_arquivo = tk.Label(root, text="Nenhum arquivo...", fg="gray")
        self.lbl_arquivo.pack(pady=5)

        self.btn_tocar = tk.Button(root, text="▶️ TOCAR (3s)", command=self.iniciar_thread, bg="#4CAF50", fg="white", font=("bold"), state="disabled")
        self.btn_tocar.pack(pady=10)

        self.btn_parar = tk.Button(root, text="⏹️ PARAR", command=self.parar_musica, bg="#f44336", fg="white", state="disabled")
        self.btn_parar.pack(pady=5)
        
        self.lbl_status = tk.Label(root, text="Aguardando...", fg="blue")
        self.lbl_status.pack(pady=5)

    def mudar_instrumento(self, event):
        self.nome_mapa_atual = self.combo_inst.get()
        self.mapa_atual = MAPAS[self.nome_mapa_atual]

    def carregar_midi(self):
        arquivo = filedialog.askopenfilename(filetypes=[("MIDI", "*.mid")])
        if arquivo:
            self.arquivo_midi = arquivo
            self.lbl_arquivo.config(text=os.path.basename(arquivo), fg="black")
            self.btn_tocar.config(state="normal")

    def iniciar_thread(self):
        if not self.arquivo_midi: return
        self.tocando = True
        self.btn_tocar.config(state="disabled")
        self.btn_parar.config(state="normal")
        self.combo_inst.config(state="disabled")
        threading.Thread(target=self.tocar_musica).start()

    def parar_musica(self):
        self.tocando = False

    def encontrar_tecla_mais_proxima(self, nota_midi):
        notas_disponiveis = list(self.mapa_atual.keys())
        nota_proxima = min(notas_disponiveis, key=lambda x: abs(x - nota_midi))
        return self.mapa_atual[nota_proxima]

    def tocar_musica(self):
        notas_ativas = {}

        try:
            mid = mido.MidiFile(self.arquivo_midi)
            
            for i in range(3, 0, -1):
                if not self.tocando: break
                self.lbl_status.config(text=f"Começando em {i}...")
                time.sleep(1)

            self.lbl_status.config(text=f"🎵 Tocando ({self.nome_mapa_atual})...")
            
            start_time = time.time()
            input_time = 0.0
            
            for msg in mid:
                if not self.tocando: break

                input_time += msg.time
                playback_time = time.time() - start_time
                duration = input_time - playback_time
                
                if duration > 0:
                    time.sleep(duration)

                if msg.type == 'note_on' and msg.velocity > 0:
                    tecla = None
                    if msg.note in self.mapa_atual:
                        tecla = self.mapa_atual[msg.note]
                    elif self.usar_conversao.get():
                        tecla = self.encontrar_tecla_mais_proxima(msg.note)
                    
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

        except Exception as e:
            self.lbl_status.config(text="Erro ao tocar!")
            print(e)
        
        finally:
            for tecla in notas_ativas.values():
                pydirectinput.keyUp(tecla)
            
            self.tocando = False
            self.btn_tocar.config(state="normal")
            self.btn_parar.config(state="disabled")
            self.combo_inst.config(state="readonly")

if __name__ == "__main__":
    root = tk.Tk()
    app = HeartopiaPlayer(root)
    root.mainloop()