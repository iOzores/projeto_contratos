class SimuladorService:
    """Serviço responsável pela matemática financeira de simulação de parcelamentos."""

    @staticmethod
    def simular_sac(valor_total: float, taxa_juros_percentual: float, meses: int) -> list:
        """Gera parcelas pelo Sistema de Amortização Constante (SAC)."""
        taxa_decimal = taxa_juros_percentual / 100.0
        amortizacao = valor_total / meses
        saldo_devedor = valor_total
        parcelas = []

        for mes in range(1, meses + 1):
            juros = saldo_devedor * taxa_decimal
            prestacao = amortizacao + juros
            saldo_devedor -= amortizacao

            # Evitar saldo negativo irrisório por arredondamento de ponto flutuante
            if saldo_devedor < 0.01:
                saldo_devedor = 0.0

            parcelas.append({
                "mes": mes,
                "prestacao": round(prestacao, 2),
                "amortizacao": round(amortizacao, 2),
                "juros": round(juros, 2),
                "saldo_devedor": round(saldo_devedor, 2)
            })
        return parcelas

    @staticmethod
    def simular_price(valor_total: float, taxa_juros_percentual: float, meses: int) -> list:
        """Gera parcelas pela Tabela Price (Parcelas Fixas)."""
        taxa_decimal = taxa_juros_percentual / 100.0
        saldo_devedor = valor_total
        parcelas = []

        # Prevenção para divisão por zero caso o juros seja 0
        if taxa_decimal > 0:
            prestacao = valor_total * (taxa_decimal * (1 + taxa_decimal)**meses) / (((1 + taxa_decimal)**meses) - 1)
        else:
            prestacao = valor_total / meses

        for mes in range(1, meses + 1):
            juros = saldo_devedor * taxa_decimal
            amortizacao = prestacao - juros
            saldo_devedor -= amortizacao

            if saldo_devedor < 0.01:
                saldo_devedor = 0.0

            parcelas.append({
                "mes": mes,
                "prestacao": round(prestacao, 2),
                "amortizacao": round(amortizacao, 2),
                "juros": round(juros, 2),
                "saldo_devedor": round(saldo_devedor, 2)
            })
        return parcelas