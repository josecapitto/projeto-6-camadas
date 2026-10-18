"""Testes do reconhecimento sem depender de alto-falantes ou microfone."""

import unittest
from unittest.mock import patch

import numpy as np

from dtmf import calcular_espectro, detectar_tecla, gerar_tom


class TestDTMF(unittest.TestCase):
    def test_dez_digitos_com_ruido_e_silencio_em_taxas_diferentes(self):
        rng = np.random.default_rng(42)
        for taxa in (8000, 44100, 48000):
            for tecla in "0123456789":
                with self.subTest(taxa=taxa, tecla=tecla):
                    _, tom = gerar_tom(tecla, 0.4, taxa)
                    sinal = np.concatenate((np.zeros(taxa // 5), tom, np.zeros(taxa // 5)))
                    sinal += rng.normal(0, 0.015, sinal.size)
                    resultado = detectar_tecla(sinal, taxa)
                    self.assertEqual(resultado.tecla, tecla)
                    self.assertGreaterEqual(resultado.picos.size, 5)

    def test_dez_digitos_sem_ruido(self):
        for tecla in "0123456789":
            with self.subTest(tecla=tecla):
                _, sinal = gerar_tom(tecla)
                resultado = detectar_tecla(sinal)
                self.assertEqual(resultado.tecla, tecla)
                self.assertGreaterEqual(resultado.picos.size, 5)

    def test_rejeita_silencio_ruido_e_frequencia_unica(self):
        taxa = 44100
        tempo = np.arange(taxa) / taxa
        rng = np.random.default_rng(42)
        sinais = [
            np.zeros(taxa),
            np.array([]),
            np.ones(taxa),
            rng.normal(0, 0.1, taxa),
            np.sin(2 * np.pi * 697 * tempo),
            np.sin(2 * np.pi * 1209 * tempo),
            np.sin(2 * np.pi * 500 * tempo) + np.sin(2 * np.pi * 2000 * tempo),
        ]
        for indice, sinal in enumerate(sinais):
            with self.subTest(caso=indice), self.assertRaises(ValueError):
                detectar_tecla(sinal)

    def test_parametros_invalidos(self):
        for argumentos in (("10",), ("",), ("1", 0), ("1", 1, 0), ("1", 1e-8)):
            with self.subTest(argumentos=argumentos), self.assertRaises(ValueError):
                gerar_tom(*argumentos)
        for sinal in ([float("nan"), 0], [float("inf"), 0], [1]):
            with self.subTest(sinal=sinal), self.assertRaises(ValueError):
                calcular_espectro(sinal)

    def test_emissor_trata_falha_da_placa_de_som(self):
        import emissor
        import sounddevice as sd

        with patch("builtins.input", side_effect=["1", "n"]), \
             patch("emissor.taxa_dispositivo", side_effect=sd.PortAudioError("sem saída")), \
             patch("emissor._plotar_emissao"), patch("builtins.print"):
            emissor.executar_emissor()


if __name__ == "__main__":
    unittest.main()
