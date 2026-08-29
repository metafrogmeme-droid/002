"""US stock RWA selection basket test Playbook."""
from getagent import runtime


def _candidate_rows() -> list[dict[str, object]]:
    return [
        {
            "asset": "NVDA",
            "base_coin": "rNVDA",
            "symbol": "RNVDAUSDT",
            "market": "spot",
            "name": "NVIDIA",
            "asset_class": "stock",
            "reference_price": "142.50",
            "target_price": "158.00",
            "stop_loss": "132.00",
            "score": 96,
            "thesis": "AI infrastructure demand keeps NVIDIA at the center of the quality-growth basket.",
            "risk": "Valuation can compress quickly if AI capex expectations reset.",
            "thesis_i18n": {
                "en": "AI infrastructure demand keeps NVIDIA at the center of the quality-growth basket.",
                "zh": "AI 基础设施需求让英伟达继续处在质量成长篮子的核心。",
                "zh-tw": "AI 基礎設施需求讓輝達持續處在品質成長籃子的核心。",
                "es": "La demanda de infraestructura de IA mantiene a NVIDIA en el centro de la cesta de crecimiento de calidad.",
                "ja": "AIインフラ需要がNVIDIAをクオリティ成長バスケットの中心に置いています。",
                "vi": "Nhu cầu hạ tầng AI giữ NVIDIA ở trung tâm rổ tăng trưởng chất lượng.",
            },
            "risk_i18n": {
                "en": "Valuation can compress quickly if AI capex expectations reset.",
                "zh": "如果 AI 资本开支预期重置，估值可能迅速压缩。",
                "zh-tw": "如果 AI 資本開支預期重置，估值可能迅速壓縮。",
                "es": "La valoración puede comprimirse rápido si se reajustan las expectativas de capex en IA.",
                "ja": "AI設備投資への期待が見直されると、バリュエーションは急速に縮小する可能性があります。",
                "vi": "Định giá có thể co hẹp nhanh nếu kỳ vọng capex AI bị điều chỉnh.",
            },
        },
        {
            "asset": "AAPL",
            "base_coin": "rAAPL",
            "symbol": "RAAPLUSDT",
            "market": "spot",
            "name": "Apple",
            "asset_class": "stock",
            "reference_price": "196.00",
            "target_price": "212.00",
            "stop_loss": "184.00",
            "score": 91,
            "thesis": "Apple adds durable consumer hardware, services cash flow, and defensive mega-cap depth.",
            "risk": "Upgrade cycles or regulatory pressure can weaken the defensive profile.",
            "thesis_i18n": {
                "en": "Apple adds durable consumer hardware, services cash flow, and defensive mega-cap depth.",
                "zh": "苹果提供稳健的消费硬件、服务现金流和防御型超大盘深度。",
                "zh-tw": "蘋果提供穩健的消費硬體、服務現金流和防禦型超大型股深度。",
                "es": "Apple aporta hardware de consumo duradero, flujo de caja de servicios y profundidad defensiva de megacap.",
                "ja": "Appleは耐久性のある消費者向けハードウェア、サービス収益、防御的な大型株の厚みを加えます。",
                "vi": "Apple bổ sung phần cứng tiêu dùng bền vững, dòng tiền dịch vụ và chiều sâu phòng thủ của mega-cap.",
            },
            "risk_i18n": {
                "en": "Upgrade cycles or regulatory pressure can weaken the defensive profile.",
                "zh": "换机周期走弱或监管压力可能削弱其防御属性。",
                "zh-tw": "換機週期走弱或監管壓力可能削弱其防禦屬性。",
                "es": "Los ciclos de renovación o la presión regulatoria pueden debilitar su perfil defensivo.",
                "ja": "買い替えサイクルや規制圧力が防御的な特徴を弱める可能性があります。",
                "vi": "Chu kỳ nâng cấp hoặc áp lực quản lý có thể làm suy yếu đặc tính phòng thủ.",
            },
        },
        {
            "asset": "MSFT",
            "base_coin": "rMSFT",
            "symbol": "RMSFTUSDT",
            "market": "spot",
            "name": "Microsoft",
            "asset_class": "stock",
            "reference_price": "448.00",
            "target_price": "482.00",
            "stop_loss": "420.00",
            "score": 89,
            "thesis": "Microsoft brings enterprise software, cloud scale, and AI platform exposure.",
            "risk": "Cloud growth deceleration can pressure multiples across the software complex.",
            "thesis_i18n": {
                "en": "Microsoft brings enterprise software, cloud scale, and AI platform exposure.",
                "zh": "微软带来企业软件、云规模和 AI 平台敞口。",
                "zh-tw": "微軟帶來企業軟體、雲端規模和 AI 平台曝險。",
                "es": "Microsoft aporta software empresarial, escala en la nube y exposición a plataformas de IA.",
                "ja": "Microsoftは企業向けソフトウェア、クラウド規模、AIプラットフォームへのエクスポージャーをもたらします。",
                "vi": "Microsoft mang lại phần mềm doanh nghiệp, quy mô đám mây và tiếp xúc nền tảng AI.",
            },
            "risk_i18n": {
                "en": "Cloud growth deceleration can pressure multiples across the software complex.",
                "zh": "云增长放缓可能压制整个软件板块的估值倍数。",
                "zh-tw": "雲端成長放緩可能壓抑整個軟體板塊的估值倍數。",
                "es": "Una desaceleración del crecimiento cloud puede presionar los múltiplos del sector software.",
                "ja": "クラウド成長の減速は、ソフトウェア全体の評価倍率を圧迫する可能性があります。",
                "vi": "Tăng trưởng cloud chậm lại có thể gây áp lực lên bội số định giá của nhóm phần mềm.",
            },
        },
        {
            "asset": "AMZN",
            "base_coin": "rAMZN",
            "symbol": "RAMZNUSDT",
            "market": "spot",
            "name": "Amazon",
            "asset_class": "stock",
            "reference_price": "185.00",
            "target_price": "204.00",
            "stop_loss": "172.00",
            "score": 85,
            "thesis": "Amazon balances retail operating leverage with AWS and advertising optionality.",
            "risk": "Consumer softness or cloud price competition can weigh on sentiment.",
            "thesis_i18n": {
                "en": "Amazon balances retail operating leverage with AWS and advertising optionality.",
                "zh": "亚马逊兼具零售经营杠杆、AWS 和广告业务的可选增长空间。",
                "zh-tw": "亞馬遜兼具零售營運槓桿、AWS 和廣告業務的可選成長空間。",
                "es": "Amazon combina apalancamiento operativo minorista con AWS y opcionalidad publicitaria.",
                "ja": "Amazonは小売の営業レバレッジにAWSと広告事業の選択肢を組み合わせています。",
                "vi": "Amazon cân bằng đòn bẩy vận hành bán lẻ với AWS và tùy chọn tăng trưởng quảng cáo.",
            },
            "risk_i18n": {
                "en": "Consumer softness or cloud price competition can weigh on sentiment.",
                "zh": "消费走弱或云价格竞争可能拖累市场情绪。",
                "zh-tw": "消費走弱或雲端價格競爭可能拖累市場情緒。",
                "es": "La debilidad del consumidor o la competencia de precios en cloud pueden pesar sobre el sentimiento.",
                "ja": "消費の弱さやクラウドの価格競争が投資家心理の重しになる可能性があります。",
                "vi": "Tiêu dùng yếu hoặc cạnh tranh giá cloud có thể đè nặng lên tâm lý thị trường.",
            },
        },
        {
            "asset": "META",
            "base_coin": "rMETA",
            "symbol": "RMETAUSDT",
            "market": "spot",
            "name": "Meta Platforms",
            "asset_class": "stock",
            "reference_price": "505.00",
            "target_price": "548.00",
            "stop_loss": "470.00",
            "score": 82,
            "thesis": "Meta offers ad recovery, strong cash generation, and AI-driven engagement improvements.",
            "risk": "Ad cyclicality and platform policy changes can create sharp drawdowns.",
            "thesis_i18n": {
                "en": "Meta offers ad recovery, strong cash generation, and AI-driven engagement improvements.",
                "zh": "Meta 受益于广告复苏、强劲现金生成和 AI 驱动的互动改善。",
                "zh-tw": "Meta 受益於廣告復甦、強勁現金生成和 AI 驅動的互動改善。",
                "es": "Meta ofrece recuperación publicitaria, fuerte generación de caja y mejoras de interacción impulsadas por IA.",
                "ja": "Metaは広告回復、強いキャッシュ創出、AIによるエンゲージメント改善を備えています。",
                "vi": "Meta có phục hồi quảng cáo, tạo tiền mặt mạnh và cải thiện tương tác nhờ AI.",
            },
            "risk_i18n": {
                "en": "Ad cyclicality and platform policy changes can create sharp drawdowns.",
                "zh": "广告周期性和平台政策变化可能带来剧烈回撤。",
                "zh-tw": "廣告週期性和平台政策變化可能帶來劇烈回撤。",
                "es": "La ciclicidad publicitaria y los cambios de políticas de plataforma pueden provocar caídas fuertes.",
                "ja": "広告の循環性やプラットフォーム方針の変更が急な下落を招く可能性があります。",
                "vi": "Tính chu kỳ quảng cáo và thay đổi chính sách nền tảng có thể tạo ra nhịp giảm mạnh.",
            },
        },
        {
            "asset": "GOOGL",
            "base_coin": "rGOOGL",
            "symbol": "RGOOGLUSDT",
            "market": "spot",
            "name": "Alphabet",
            "asset_class": "stock",
            "reference_price": "176.00",
            "target_price": "192.00",
            "stop_loss": "164.00",
            "score": 80,
            "thesis": "Alphabet adds search cash flow, cloud growth, and broad AI model exposure.",
            "risk": "Search share pressure or regulatory remedies can hurt the thesis.",
            "thesis_i18n": {
                "en": "Alphabet adds search cash flow, cloud growth, and broad AI model exposure.",
                "zh": "Alphabet 提供搜索现金流、云业务增长和广泛 AI 模型敞口。",
                "zh-tw": "Alphabet 提供搜尋現金流、雲端業務成長和廣泛 AI 模型曝險。",
                "es": "Alphabet aporta flujo de caja de búsqueda, crecimiento cloud y amplia exposición a modelos de IA.",
                "ja": "Alphabetは検索のキャッシュフロー、クラウド成長、広範なAIモデルへのエクスポージャーを加えます。",
                "vi": "Alphabet bổ sung dòng tiền tìm kiếm, tăng trưởng cloud và tiếp xúc rộng với mô hình AI.",
            },
            "risk_i18n": {
                "en": "Search share pressure or regulatory remedies can hurt the thesis.",
                "zh": "搜索份额压力或监管整改可能损害投资逻辑。",
                "zh-tw": "搜尋市占壓力或監管補救措施可能損害投資邏輯。",
                "es": "La presión sobre cuota de búsqueda o remedios regulatorios pueden dañar la tesis.",
                "ja": "検索シェアへの圧力や規制上の是正措置が投資仮説を傷つける可能性があります。",
                "vi": "Áp lực thị phần tìm kiếm hoặc biện pháp quản lý có thể làm suy yếu luận điểm.",
            },
        },
        {
            "asset": "TSLA",
            "base_coin": "rTSLA",
            "symbol": "RTSLAUSDT",
            "market": "spot",
            "name": "Tesla",
            "asset_class": "stock",
            "reference_price": "180.00",
            "target_price": "205.00",
            "stop_loss": "162.00",
            "score": 72,
            "thesis": "Tesla keeps high-beta exposure to EV, autonomy, and energy-storage themes.",
            "risk": "Margin pressure and delivery volatility can dominate the long-term optionality story.",
            "thesis_i18n": {
                "en": "Tesla keeps high-beta exposure to EV, autonomy, and energy-storage themes.",
                "zh": "特斯拉保留对电动车、自动驾驶和储能主题的高 beta 敞口。",
                "zh-tw": "特斯拉保留對電動車、自動駕駛和儲能主題的高 beta 曝險。",
                "es": "Tesla mantiene exposición de beta alta a vehículos eléctricos, autonomía y almacenamiento energético.",
                "ja": "TeslaはEV、自動運転、エネルギー貯蔵テーマへの高ベータのエクスポージャーを維持します。",
                "vi": "Tesla giữ tiếp xúc beta cao với chủ đề xe điện, tự lái và lưu trữ năng lượng.",
            },
            "risk_i18n": {
                "en": "Margin pressure and delivery volatility can dominate the long-term optionality story.",
                "zh": "利润率压力和交付波动可能盖过长期可选增长叙事。",
                "zh-tw": "利潤率壓力和交付波動可能蓋過長期可選成長敘事。",
                "es": "La presión de márgenes y la volatilidad de entregas pueden dominar la opcionalidad de largo plazo.",
                "ja": "利益率への圧力や納車台数の変動が、長期的な成長オプションの物語を上回る可能性があります。",
                "vi": "Áp lực biên lợi nhuận và biến động giao hàng có thể lấn át câu chuyện tùy chọn dài hạn.",
            },
        },
    ]


def run() -> None:
    config = runtime.manifest.get("strategy_config", {}) or {}
    max_assets = int(config.get("max_assets", 5) or 5)
    max_assets = max(1, min(max_assets, 7))

    ranked = sorted(_candidate_rows(), key=lambda row: int(row["score"]), reverse=True)
    basket = []
    for row in ranked[:max_assets]:
        pick = dict(row)
        pick.pop("score", None)
        basket.append(pick)

    runtime.emit_signal(
        action="watch",
        symbol=str(basket[0]["symbol"]) if basket else "",
        confidence=0.68,
        metrics={"basket_size": len(basket), "candidate_count": len(ranked)},
        meta={"basket": basket},
    )


if __name__ == "__main__":
    run()
