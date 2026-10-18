"""Seleção de dispositivos e taxas suportadas pela placa de som."""

from dtmf import TAXA_AMOSTRAGEM


def taxa_dispositivo(tipo: str) -> int:
    import sounddevice as sd

    verificar = sd.check_input_settings if tipo == "input" else sd.check_output_settings
    try:
        verificar(samplerate=TAXA_AMOSTRAGEM, channels=1, dtype="float32")
        return TAXA_AMOSTRAGEM
    except sd.PortAudioError:
        taxa = int(sd.query_devices(kind=tipo)["default_samplerate"])
        verificar(samplerate=taxa, channels=1, dtype="float32")
        return taxa


def configurar_audio() -> None:
    try:
        import sounddevice as sd
    except (ImportError, OSError) as erro:
        print(f"Não foi possível carregar o áudio: {erro}")
        return

    try:
        dispositivos = sd.query_devices()
        print(dispositivos)
        print("Deixe em branco para manter o dispositivo atual.")
        for posicao, canais, nome in (
            (0, "max_input_channels", "microfone"),
            (1, "max_output_channels", "saída de som"),
        ):
            while True:
                escolha = input(f"Índice do dispositivo de {nome}: ").strip()
                if not escolha:
                    break
                try:
                    indice = int(escolha)
                    if not 0 <= indice < len(dispositivos) or dispositivos[indice][canais] < 1:
                        raise ValueError
                    par = list(sd.default.device)
                    par[posicao] = indice
                    sd.default.device = par
                    break
                except ValueError:
                    print(f"Escolha um índice válido para {nome}.")
        print("Seleção aplicada para esta execução do programa.")
    except sd.PortAudioError as erro:
        print(f"Não foi possível consultar os dispositivos: {erro}")
