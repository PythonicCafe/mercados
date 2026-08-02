import datetime

import pytest

from mercados.b3 import B3


class RespostaVazia:
    content: bytes = b""


def test_negociacao_bolsa_levanta_erro_para_arquivo_vazio(monkeypatch: pytest.MonkeyPatch) -> None:
    b3 = B3()

    def get(*args: object, **kwargs: object) -> RespostaVazia:
        return RespostaVazia()

    monkeypatch.setattr(b3.session, "get", get)

    with pytest.raises(ValueError, match="arquivo de cotação vazio"):
        list(b3.negociacao_bolsa("dia", datetime.date(2026, 8, 1)))
