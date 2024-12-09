import datetime
import decimal
import json
from pathlib import Path

from mercados.document import InformeFII


def assert_informe_fii(document_id, expected):
    filename = Path(__file__).parent / "data" / f"document-{document_id:06d}.xml"
    with filename.open() as fobj:
        xml = fobj.read()
    docs = InformeFII.from_xml(xml)
    assert len(docs) == len(expected)
    for a, b in zip(docs, expected):
        assert a == b


def load_json_data(document_id):
    filename = Path(__file__).parent / "data" / f"data-{document_id:06d}.json"
    with filename.open() as fobj:
        return json.load(fobj)


def test_informe_mensal_378398():
    expected = [
        InformeFII(
            adm_bvmf=True,
            adm_cetip=False,
            administrador="XP INVESTIMENTOS CORRETORA DE CÂMBIO, TÍTULOS E VAL MOB S/A",
            administrador_cnpj="02332886000104",
            bairro="LEBLON",
            cep="22440-033",
            codigo_isin="BRXPSFCTF009",
            competencia="2022-10-01",
            complemento="5º e 8º andares",
            cotas_emitidas=decimal.Decimal("43302140"),
            data_encerramento_trimestre=None,
            data_funcionamento=datetime.date(2019, 7, 10),
            data_prazo=None,
            email="adm.fundos.estruturados@xpi.com.br",
            encerramento_exercicio="31/12",
            enquadra_nota_seis=None,
            exclusivo=False,
            fundo="XP SELECTION FUNDO DE INVESTIMENTO IMOBILIÁRIO - FII",
            fundo_cnpj="30983020000190",
            gestao_tipo="Ativa",
            logradouro="AVENIDA ATAULFO DE PAIVA",
            mandato="Títulos e Valores Mobiliários",
            mercado_negociacao_bolsa=True,
            mercado_negociacao_mb=False,
            mercado_negociacao_mbo=False,
            municipio="RIO DE JANEIRO",
            numero="153",
            prazo_duracao="Indeterminado",
            publico_alvo="Investidores em Geral",
            segmento="Títulos e Valores Mobiliários",
            site="www.xpi.com.br",
            telefone_1="(11) 3027-2237",
            telefone_2=None,
            telefone_3=None,
            tipo="Informe Mensal",
            uf="RJ",
            vinculo_familiar_cotistas=False,
            dados=load_json_data(378398),
        ),
    ]

    assert_informe_fii(378398, expected)


def test_informe_trimestral_378495():
    expected = [
        InformeFII(
            adm_bvmf=False,
            adm_cetip=False,
            administrador="LIMINE TRUST DTVM LTDA.",
            administrador_cnpj="20118507000151",
            bairro="Vila Olímpia",
            cep="04548-004",
            codigo_isin=None,
            competencia="3/2022",
            complemento="Cj 91",
            cotas_emitidas=decimal.Decimal("29383.77580773"),
            data_encerramento_trimestre=datetime.date(2022, 9, 30),
            data_funcionamento=datetime.date(2015, 1, 8),
            data_prazo=None,
            email="adm.fundos@liminedtvm.com.br",
            encerramento_exercicio="31/12",
            enquadra_nota_seis=False,
            exclusivo=False,
            fundo="CEDRO - FUNDO DE INVESTIMENTO IMOBILIÁRIO - FII",
            fundo_cnpj="20118507000151",
            gestao_tipo="Ativa",
            logradouro="Av. Dr. Cardoso de Melo",
            mandato="Desenvolvimento para Renda",
            mercado_negociacao_bolsa=False,
            mercado_negociacao_mb=True,
            mercado_negociacao_mbo=False,
            municipio="São Paulo",
            numero="1184",
            prazo_duracao="Indeterminado",
            publico_alvo="Investidor Profissional",
            segmento="Outros",
            site="www.liminedtvm.com.br",
            telefone_1="(011) 2846-1166",
            telefone_2=None,
            telefone_3=None,
            tipo="Informe Trimestral",
            uf="SP",
            vinculo_familiar_cotistas=False,
            dados=load_json_data(378495),
        ),
    ]

    assert_informe_fii(378495, expected)


def test_informe_anual_226812():
    expected = [
        InformeFII(
            adm_bvmf=True,
            adm_cetip=False,
            administrador="BTG Pactual Serviços Financeiros S.A. – DTVM",
            administrador_cnpj="05562312000102",
            bairro="Botafogo",
            cep="22250-040",
            codigo_isin="BRFAMBCTF018",
            competencia="2020-12-31",
            complemento="6º Andar",
            cotas_emitidas=decimal.Decimal("104800"),
            data_encerramento_trimestre=None,
            data_funcionamento=datetime.date(2003, 3, 17),
            data_prazo=None,
            email="ri.fundoslistados@btgpactual.com",
            encerramento_exercicio="Dezembro",
            enquadra_nota_seis=None,
            exclusivo=False,
            fundo="FII EDIFICIO ALMIRANTE BARROSO",
            fundo_cnpj="05562312000102",
            gestao_tipo="Passiva",
            logradouro="Praia de Botafogo",
            mandato="Renda",
            mercado_negociacao_bolsa=True,
            mercado_negociacao_mb=False,
            mercado_negociacao_mbo=False,
            municipio="Rio de Janeiro",
            numero="501",
            prazo_duracao="Indeterminado",
            publico_alvo="Investidores em Geral",
            segmento="Lajes Corporativas",
            site="www.btgpactual.com",
            telefone_1="(11) 3383-3102",
            telefone_2=None,
            telefone_3=None,
            tipo="Informe Anual",
            uf="RJ",
            vinculo_familiar_cotistas=False,
            dados=load_json_data(226812),
        ),
    ]

    assert_informe_fii(226812, expected)
