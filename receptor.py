"""Aplicação receptora e reconhecedora de tons DTMF."""

import matplotlib.pyplot as plt
import numpy as np

from audio import taxa_dispositivo
from dtmf import TAXA_AMOSTRAGEM, ResultadoDeteccao, detectar_tecla


def _plotar_recepcao(
    sinal: np.ndarray, resultado: ResultadoDeteccao, taxa: int = TAXA_AMOSTRAGEM
) -> None:
    tempo = np.arange(sinal.size) / taxa
    figura, eixos = plt.subplots(2, 1, figsize=(10, 7), constrained_layout=True)

    eixos[0].plot(tempo, sinal, linewidth=0.8)
    eixos[0].set_title("Sinal recebido pelo microfone")
    eixos[0].set_xlabel("Tempo (s)")
    eixos[0].set_ylabel("Amplitude")
    eixos[0].grid(True, alpha=0.3)

    faixa = resultado.frequencias <= 5_000
    eixos[1].plot(
        resultado.frequencias[faixa],
        resultado.magnitudes[faixa],
        linewidth=0.9,
    )
    picos_visiveis = resultado.picos[:10]
    eixos[1].scatter(
        resultado.frequencias[picos_visiveis],
        resultado.magnitudes[picos_visiveis],
        color="red",
        s=25,
        label="Picos encontrados",
        zorder=3,
    )
    eixos[1].axvline(resultado.frequencia_baixa, color="green", linestyle="--")
    eixos[1].axvline(resultado.frequencia_alta, color="green", linestyle="--")
    eixos[1].set_title(f"FFT do áudio recebido - número {resultado.tecla}")
    eixos[1].set_xlabel("Frequência (Hz)")
    eixos[1].set_ylabel("Magnitude")
    eixos[1].legend()
    eixos[1].grid(True, alpha=0.3)
    plt.show()


def executar_receptor() -> None:
    try:
        import sounddevice as sd
    except (ImportError, OSError) as erro:
        print(f"Não foi possível acessar o módulo de áudio: {erro}")
        return

    input(
        "Faça o outro dispositivo começar a emitir o tom e, depois, "
        "pressione ENTER para gravar..."
    )
    duracao = 2.0
    print(f"Gravando por {duracao:.0f} segundos...")
    try:
        taxa = taxa_dispositivo("input")
        gravacao = sd.rec(
            int(duracao * taxa),
            samplerate=taxa,
            channels=1,
            dtype="float32",
        )
        sd.wait()
    except sd.PortAudioError as erro:
        print(f"Falha ao gravar pelo microfone: {erro}")
        print("Confira a permissão de microfone do Windows ou selecione outro no menu 3.")
        return

    sinal = gravacao[:, 0]
    try:
        resultado = detectar_tecla(sinal, taxa)
    except ValueError as erro:
        print(f"Não foi possível reconhecer uma tecla: {erro}")
        return

    print("\nPicos predominantes encontrados:")
    for indice in resultado.picos[: max(5, min(10, resultado.picos.size))]:
        print(
            f"  {resultado.frequencias[indice]:8.2f} Hz "
            f"(magnitude {resultado.magnitudes[indice]:.5f})"
        )
    print(
        f"\nFrequências DTMF: {resultado.frequencia_baixa:.2f} Hz "
        f"e {resultado.frequencia_alta:.2f} Hz"
    )
    print(f"Número identificado: {resultado.tecla}")
    _plotar_recepcao(sinal, resultado, taxa)


if __name__ == "__main__":
    executar_receptor()
