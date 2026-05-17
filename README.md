# 🎵 Heartopia MIDI Auto-Player

O **Heartopia MIDI Auto-Player** é uma aplicação desktop desenvolvida para automatizar a execução de músicas em instrumentos virtuais dentro de jogos (com foco principal no *Heartopia*). 

Através da leitura de arquivos de áudio padrão (`.mid`), o programa interpreta as notas musicais e as traduz automaticamente em comandos de teclado, permitindo que você realize apresentações musicais perfeitas no jogo sem a necessidade de digitar as notas manualmente.

## 🎯 Para que serve?

Em muitos jogos modernos que possuem mecânicas de "bardo" ou instrumentos musicais (como *Heartopia*, *Genshin Impact*, entre outros), os jogadores precisam pressionar teclas específicas do computador para tocar notas musicais. 

O objetivo deste projeto é **servir como uma ponte entre partituras digitais (arquivos MIDI) e o jogo**. O aplicativo lê o arquivo de música, calcula o tempo exato de cada nota e simula o pressionamento da tecla correspondente no seu teclado, "tocando" a música para você.

## ✨ Principais Funcionalidades

* **Reprodução Automatizada:** Lê arquivos `.mid` e simula os toques de teclado em tempo real com precisão milimétrica.
* **Mapeamento de Teclas:** Suporte pré-configurado para diferentes tipos de instrumentos do jogo:
  * *Completo (37 Teclas):* Para mapeamentos que utilizam várias oitavas no teclado.
  * *Simplificado (15 Teclas):* Para instrumentos mais básicos.
* **Controle Dinâmico de Reprodução:**
  * **Transposição de Tom:** Ajuste o tom da música (em semitons) para adequá-la aos limites do instrumento do jogo.
  * **Controle de Velocidade:** Acelere ou diminua o andamento (BPM) da música com um simples controle deslizante.
* **Filtragem de Canais (Tracks):** A maioria dos arquivos MIDI possui vários instrumentos misturados (bateria, baixo, piano). O aplicativo permite isolar e tocar apenas o canal desejado (ex: apenas a melodia principal).
* **Conversão Inteligente de Notas:** Caso o arquivo original possua notas muito agudas ou muito graves que não existem no instrumento do jogo, o aplicativo encontra e converte automaticamente para a tecla válida mais próxima, garantindo que a música não perca o ritmo.
* **Botão de Emergência (Killswitch):** Sistema de segurança integrado que permite interromper a execução instantaneamente ao pressionar a tecla `ESC`, liberando o controle do seu teclado imediatamente.

## 🛠️ Tecnologias Utilizadas

A aplicação foi construída em **Python**, possuindo uma interface moderna e "cozy", utilizando as seguintes bibliotecas:
* `mido`: Para leitura, análise e extração do tempo das notas dos arquivos MIDI.
* `pydirectinput`: Para simulação de comandos de teclado compatíveis com as engines de jogos (DirectX).
* `keyboard`: Para monitoramento em segundo plano do botão de interrupção de emergência.
* `customtkinter`: Para a interface gráfica moderna, responsiva e amigável.
