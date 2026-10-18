"""Funções compartilhadas para geração e reconhecimento de tons DTMF."""

from dataclasses import dataclass

import numpy as np
from scipy.signal import find_peaks


TAXA_AMOSTRAGEM = 44_100
FREQUENCIAS_BAIXAS = np.array([697.0, 770.0, 852.0, 941.0])
FREQUENCIAS_ALTAS = np.array([1209.0, 1336.0, 1477.0, 1633.0])

MATRIZ_DTMF = np.array(
    [
        ["1", "2", "3", "A"],
        ["4", "5", "6", "B"],
        ["7", "8", "9", "C"],
        ["*", "0", "#", "D"],
    ]
)

FREQUENCIAS_NUMERICAS = {
    MATRIZ_DTMF[linha, coluna]: (
        FREQUENCIAS_BAIXAS[linha],
        FREQUENCIAS_ALTAS[coluna],
    )
    for linha in range(4)
    for coluna in range(3)
    if MATRIZ_DTMF[linha, coluna] in "0123456789"
}


@dataclass(frozen=True)
class ResultadoDeteccao:
    tecla: str
    frequencia_baixa: float
    frequencia_alta: float
    frequencias: np.ndarray
    magnitudes: np.ndarray
    picos: np.ndarray


def gerar_tom(
    tecla: str,
    duracao: float = 2.0,
    taxa_amostragem: int = TAXA_AMOSTRAGEM,
) -> tuple[np.ndarray, np.ndarray]:
    """Gera duas senoides DTMF somadas, com pequenas rampas nas extremidades."""
    if tecla not in FREQUENCIAS_NUMERICAS:
        raise ValueError("A tecla deve ser um número entre 0 e 9.")
    if not np.isfinite(duracao) or duracao <= 0:
        raise ValueError("A duração deve ser positiva.")
    if not np.isfinite(taxa_amostragem) or taxa_amostragem <= 2 * FREQUENCIAS_ALTAS.max():
        raise ValueError("A taxa de amostragem deve ser maior que 3266 Hz.")

    quantidade = int(duracao * taxa_amostragem)
    if quantidade < 2:
        raise ValueError("A duração precisa produzir pelo menos duas amostras.")
    tempo = np.arange(quantidade) / taxa_amostragem
    baixa, alta = FREQUENCIAS_NUMERICAS[tecla]
    sinal = 0.45 * (
        np.sin(2 * np.pi * baixa * tempo)
        + np.sin(2 * np.pi * alta * tempo)
    )

    # Evita estalos ao iniciar e interromper o áudio.
    tamanho_rampa = min(int(0.01 * taxa_amostragem), quantidade // 2)
    if tamanho_rampa:
        rampa = np.linspace(0.0, 1.0, tamanho_rampa)
        sinal[:tamanho_rampa] *= rampa
        sinal[-tamanho_rampa:] *= rampa[::-1]

    return tempo, sinal.astype(np.float32)


def calcular_espectro(
    sinal: np.ndarray,
    taxa_amostragem: int = TAXA_AMOSTRAGEM,
) -> tuple[np.ndarray, np.ndarray]:
    """Calcula o espectro unilateral do sinal usando uma janela de Hann."""
    amostras = np.asarray(sinal, dtype=float).reshape(-1)
    if amostras.size < 2:
        raise ValueError("O sinal precisa conter pelo menos duas amostras.")
    if not np.all(np.isfinite(amostras)):
        raise ValueError("O sinal contém amostras inválidas.")
    if not np.isfinite(taxa_amostragem) or taxa_amostragem <= 0:
        raise ValueError("A taxa de amostragem deve ser positiva.")

    amostras = amostras - np.mean(amostras)
    janela = np.hanning(amostras.size)
    transformada = np.fft.rfft(amostras * janela)
    frequencias = np.fft.rfftfreq(amostras.size, d=1 / taxa_amostragem)
    magnitudes = 2.0 * np.abs(transformada) / max(np.sum(janela), 1.0)
    return frequencias, magnitudes


def _recortar_trecho_ativo(sinal: np.ndarray, taxa_amostragem: int) -> np.ndarray:
    """Remove silêncio antes/depois e limita a análise ao trecho mais útil."""
    amostras = np.asarray(sinal, dtype=float).reshape(-1)
    if amostras.size < 2 or not np.all(np.isfinite(amostras)):
        raise ValueError("O áudio precisa conter pelo menos duas amostras válidas.")
    amostras = amostras - np.mean(amostras)
    pico = float(np.max(np.abs(amostras), initial=0.0))
    if pico < 1e-4:
        raise ValueError("O áudio está em silêncio ou com volume muito baixo.")

    piso_estimado = float(np.quantile(np.abs(amostras), 0.20))
    limiar = max(0.06 * pico, 3.0 * piso_estimado)
    ativos = np.flatnonzero(np.abs(amostras) >= limiar)
    if ativos.size:
        margem = int(0.03 * taxa_amostragem)
        inicio = max(0, int(ativos[0]) - margem)
        fim = min(amostras.size, int(ativos[-1]) + margem + 1)
        amostras = amostras[inicio:fim]

    # Um segundo já fornece resolução de 1 Hz e reduz ruídos fora do tom.
    maximo = taxa_amostragem
    if amostras.size > maximo:
        energia_acumulada = np.concatenate(
            ([0.0], np.cumsum(amostras**2, dtype=float))
        )
        energia = (
            energia_acumulada[maximo:] - energia_acumulada[:-maximo]
        ) / maximo
        inicio = int(np.argmax(energia))
        amostras = amostras[inicio : inicio + maximo]
    return amostras


def _picos_do_espectro(
    frequencias: np.ndarray,
    magnitudes: np.ndarray,
    quantidade_minima: int,
) -> np.ndarray:
    """Localiza e ordena os picos audíveis por magnitude."""
    faixa = (frequencias >= 300) & (frequencias <= 5_000)
    indices_faixa = np.flatnonzero(faixa)
    valores = magnitudes[faixa]
    if valores.size < 3:
        return np.array([], dtype=int)

    distancia = max(1, int(20 / (frequencias[1] - frequencias[0])))
    proeminencia = max(float(np.max(valores)) * 0.002, 1e-12)
    locais, _ = find_peaks(
        valores,
        prominence=proeminencia,
        distance=distancia,
    )

    # Se a gravação estiver muito limpa, relaxa a sensibilidade para exibir
    # ao menos cinco máximos locais, como solicitado no enunciado.
    if locais.size < quantidade_minima:
        locais, _ = find_peaks(valores, distance=distancia)

    globais = indices_faixa[locais]
    ordem = np.argsort(magnitudes[globais])[::-1]
    return globais[ordem]


def _melhor_pico_esperado(
    alvo: float,
    frequencias: np.ndarray,
    magnitudes: np.ndarray,
    picos: np.ndarray,
    tolerancia: float,
) -> tuple[int, float]:
    candidatos = picos[np.abs(frequencias[picos] - alvo) <= tolerancia]
    if candidatos.size == 0:
        return -1, 0.0
    indice = int(candidatos[np.argmax(magnitudes[candidatos])])
    return indice, float(magnitudes[indice])


def detectar_tecla(
    sinal: np.ndarray,
    taxa_amostragem: int = TAXA_AMOSTRAGEM,
    tolerancia_hz: float = 30.0,
    quantidade_minima_picos: int = 5,
) -> ResultadoDeteccao:
    """Identifica a tecla numérica a partir dos dois picos DTMF fundamentais."""
    if not np.isfinite(taxa_amostragem) or taxa_amostragem <= 2 * FREQUENCIAS_ALTAS.max():
        raise ValueError("A taxa de amostragem deve ser maior que 3266 Hz.")
    if not np.isfinite(tolerancia_hz) or tolerancia_hz <= 0:
        raise ValueError("A tolerância deve ser positiva.")
    if quantidade_minima_picos < 2:
        raise ValueError("A quantidade mínima de picos deve ser pelo menos dois.")
    trecho = _recortar_trecho_ativo(sinal, taxa_amostragem)
    frequencias, magnitudes = calcular_espectro(trecho, taxa_amostragem)
    picos = _picos_do_espectro(
        frequencias,
        magnitudes,
        quantidade_minima_picos,
    )
    if picos.size < 2:
        raise ValueError("Não foi possível encontrar picos suficientes no áudio.")

    picos_baixos = [
        _melhor_pico_esperado(
            alvo, frequencias, magnitudes, picos, tolerancia_hz
        )
        for alvo in FREQUENCIAS_BAIXAS
    ]
    picos_altos = [
        _melhor_pico_esperado(
            alvo, frequencias, magnitudes, picos, tolerancia_hz
        )
        for alvo in FREQUENCIAS_ALTAS
    ]

    linha = int(np.argmax([magnitude for _, magnitude in picos_baixos]))
    coluna = int(np.argmax([magnitude for _, magnitude in picos_altos]))
    indice_baixo, magnitude_baixa = picos_baixos[linha]
    indice_alto, magnitude_alta = picos_altos[coluna]

    faixa_ruido = (frequencias >= 300) & (frequencias <= 5_000)
    ruido = max(float(np.median(magnitudes[faixa_ruido])), 1e-12)
    if indice_baixo < 0 or indice_alto < 0:
        raise ValueError("Não encontrei as duas frequências DTMF esperadas.")
    if min(magnitude_baixa, magnitude_alta) < 8.0 * ruido:
        raise ValueError("Os picos DTMF estão fracos em relação ao ruído.")

    tecla = str(MATRIZ_DTMF[linha, coluna])
    if tecla not in "0123456789":
        raise ValueError(f"O áudio parece representar a tecla {tecla}, não um número.")

    return ResultadoDeteccao(
        tecla=tecla,
        frequencia_baixa=float(frequencias[indice_baixo]),
        frequencia_alta=float(frequencias[indice_alto]),
        frequencias=frequencias,
        magnitudes=magnitudes,
        picos=picos,
    )
