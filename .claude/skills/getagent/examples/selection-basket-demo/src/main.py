"""Selection basket demo entry point."""
from getagent import runtime


def run() -> None:
    cfg = runtime.manifest.get("strategy_config", {}) or {}
    max_assets = int(cfg.get("max_assets", 2) or 2)

    candidates = [
        {
            "asset": "BTC",
            "symbol": "BTCUSDT",
            "market": "spot",
            "name": "Bitcoin",
            "asset_class": "crypto",
            "reference_price": "100000",
            "target_price": "120000",
            "stop_loss": "90000",
            "thesis": "Bitcoin is the liquidity anchor of the demo basket and represents broad crypto beta.",
            "risk": "It can sell off sharply during broad risk-off or ETF-flow reversals.",
            "thesis_i18n": {
                "en": "Bitcoin is the liquidity anchor of the demo basket and represents broad crypto beta.",
                "zh": "比特币是演示篮子的流动性核心，代表广泛的加密市场 beta。",
                "zh-tw": "比特幣是示範籃子的流動性核心，代表廣泛的加密市場 beta。",
                "es": "Bitcoin es el ancla de liquidez de la cesta demo y representa la beta amplia de cripto.",
                "ja": "Bitcoinはデモバスケットの流動性アンカーで、広い暗号資産ベータを表します。",
                "vi": "Bitcoin là neo thanh khoản của rổ demo và đại diện cho beta crypto rộng.",
            },
            "risk_i18n": {
                "en": "It can sell off sharply during broad risk-off or ETF-flow reversals.",
                "zh": "在整体避险或 ETF 资金流反转时可能大幅下跌。",
                "zh-tw": "在整體避險或 ETF 資金流反轉時可能大幅下跌。",
                "es": "Puede caer con fuerza en episodios de aversion al riesgo o reversiones de flujos ETF.",
                "ja": "広範なリスクオフやETFフロー反転時に大きく下落する可能性があります。",
                "vi": "Có thể giảm mạnh khi thị trường risk-off hoặc dòng tiền ETF đảo chiều.",
            },
        },
        {
            "asset": "ETH",
            "symbol": "ETHUSDT",
            "market": "spot",
            "name": "Ethereum",
            "asset_class": "crypto",
            "reference_price": "4000",
            "target_price": "5000",
            "stop_loss": "3500",
            "thesis": "Ethereum adds smart-contract platform exposure and diversifies the demo basket.",
            "risk": "It can lag when network activity weakens or high-beta altcoins rotate out.",
            "thesis_i18n": {
                "en": "Ethereum adds smart-contract platform exposure and diversifies the demo basket.",
                "zh": "以太坊增加智能合约平台敞口，并分散演示篮子的资产结构。",
                "zh-tw": "以太坊增加智慧合約平台曝險，並分散示範籃子的資產結構。",
                "es": "Ethereum agrega exposicion a plataformas de contratos inteligentes y diversifica la cesta demo.",
                "ja": "Ethereumはスマートコントラクト基盤へのエクスポージャーを加え、デモバスケットを分散します。",
                "vi": "Ethereum bổ sung tiếp xúc nền tảng hợp đồng thông minh và đa dạng hóa rổ demo.",
            },
            "risk_i18n": {
                "en": "It can lag when network activity weakens or high-beta altcoins rotate out.",
                "zh": "当链上活跃度走弱或高 beta 山寨币退潮时可能跑输。",
                "zh-tw": "當鏈上活躍度走弱或高 beta 山寨幣退潮時可能落後。",
                "es": "Puede rezagarse cuando baja la actividad de red o rota el capital fuera de altcoins de alta beta.",
                "ja": "ネットワーク活動が弱まる時や高ベータのアルトコインから資金が離れる時に出遅れる可能性があります。",
                "vi": "Có thể hụt hơi khi hoạt động mạng yếu đi hoặc dòng tiền rời khỏi altcoin beta cao.",
            },
        },
    ][:max_assets]

    runtime.emit_signal(
        action="watch",
        symbol=candidates[0]["symbol"] if candidates else "",
        confidence=0.6,
        metrics={"basket_size": len(candidates)},
        meta={"basket": candidates},
    )


if __name__ == "__main__":
    run()
