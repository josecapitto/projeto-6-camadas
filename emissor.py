"""Aplicação emissora de tons DTMF."""

from pathlib import Path

import matplotlib.pyplot as plt
from scipy.io.wavfile import write

from audio import taxa_dispositivo
from dtmf import (
    FREQUENCIAS_NUMERICAS,
    TAXA_AMOSTRAGEM,
    calcular_espectro,
    gerar_tom,
)


def _ler_tecla() -> str:
    while True:
        tecla = input("Digite um número entre 0 e 9: ").strip()
        if tecla in FREQUENCIAS_NUMERICAS:
            return tecla
        print("Entrada inválida. Digite somente um algarismo de 0 a 9.")


def _plotar_emissao(tempo, sinal, tecla: str, taxa: int = TAXA_AMOSTRAGEM) -> None:
    frequencias, magnitudes = calcular_espectro(sinal, taxa)
    figura, eixos = plt.subplots(2, 1, figsize=(10, 7), constrained_layout=True)

    # Um intervalo curto deixa as duas senoides somadas visíveis.
    quantidade = min(len(tempo), int(0.02 * taxa))
    eixos[0].plot(tempo[:quantidade] * 1_000, sinal[:quantidade])
    eixos[0].set_title(f"Sinal DTMF emitido - tecla {tecla}")
    eixos[0].set_xlabel("Tempo (ms)")
    eixos[0].set_ylabel("Amplitude")
    eixos[0].grid(True, alpha=0.3)

    faixa = frequencias <= 2_000
    eixos[1].plot(frequencias[faixa], magnitudes[faixa])
    eixos[1].set_title("Transformada de Fourier do sinal emitido")
    eixos[1].set_xlabel("Frequência (Hz)")
    eixos[1].set_ylabel("Magnitude")
    eixos[1].grid(True, alpha=0.3)
    plt.show()


def executar_emissor() -> None:
    tecla = _ler_tecla()
    taxa = TAXA_AMOSTRAGEM
    tempo, sinal = gerar_tom(tecla, duracao=5.0, taxa_amostragem=taxa)
    baixa, alta = FREQUENCIAS_NUMERICAS[tecla]
    print(f"Gerando a tecla {tecla}: {baixa:.0f} Hz + {alta:.0f} Hz")

    try:
        import sounddevice as sd

        try:
            taxa = taxa_dispositivo("output")
            tempo, sinal = gerar_tom(tecla, duracao=5.0, taxa_amostragem=taxa)
            print("Reproduzindo o tom por 5 segundos... Acione o receptor agora.")
            sd.play(sinal, taxa)
            sd.wait()
        except sd.PortAudioError as erro:
            print(f"Falha na saída de som: {erro}")
            print("Confira a saída padrão do Windows ou selecione outra no menu 3.")
    except (ImportError, OSError) as erro:
        print(f"Não foi possível reproduzir o áudio: {erro}")

    salvar = input("Deseja salvar o sinal em WAV? [s/N]: ").strip().lower()
    if salvar == "s":
        caminho = Path(f"dtmf_{tecla}.wav")
        write(caminho, taxa, sinal)
        print(f"Áudio salvo em: {caminho.resolve()}")

    _plotar_emissao(tempo, sinal, tecla, taxa)


if __name__ == "__main__":
    executar_emissor()
