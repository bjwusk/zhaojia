class FeeEngine:
    """费用计取引擎 - 完全对齐软件造价联盟计价规范"""

    MEASURE_RATES = {
        "survey_fee":       {"name": "需求调研费",       "rate": 0.05,  "base": "labor"},
        "test_fee":         {"name": "测试费",           "rate": 0.08,  "base": "labor"},
        "third_party_test": {"name": "第三方测评费",       "rate": 0.03,  "base": "labor"},
        "security_test":    {"name": "安全测评费",         "rate": 0.04,  "base": "labor"},
        "supervision":      {"name": "监理费",           "rate": 0.05,  "base": "labor"},
        "training":         {"name": "培训费",           "rate": 0.03,  "base": "labor"},
    }

    MANAGEMENT_RATE = 0.10
    PROFIT_RATE = 0.08
    TAX_RATES = {"简易计税": 0.03, "一般计税": 0.06}
    BASIC_RESERVE_RATE = 0.05
    PRICE_RESERVE_RATE = 0.03
    RISK_RATE = 0.03
    WARRANTY_RATE = 0.05

    def __init__(self, params=None):
        self.params = params or {}

    def calculate_measure_fees(self, labor_cost, selected_items=None):
        if selected_items is None:
            selected_items = ["survey_fee", "test_fee", "training"]
        fees = []
        total = 0
        for key, cfg in self.MEASURE_RATES.items():
            if key in selected_items:
                amount = round(labor_cost * cfg["rate"], 4)
                fees.append({"item_name": cfg["name"], "base_amount": labor_cost, "rate": cfg["rate"] * 100, "amount": amount})
                total += amount
        return fees, round(total, 4)

    def calculate(self, labor_cost, measure_items=None, tax_type="一般计税",
                  include_management=True, include_profit=True,
                  include_basic_reserve=True, include_price_reserve=False,
                  include_risk=False, include_warranty=False,
                  external_costs=None):
        external_costs = external_costs or []
        measure_fees, measure_total = self.calculate_measure_fees(labor_cost, measure_items)
        direct_engineer_cost = round(labor_cost + measure_total, 4)
        management_fee = round(direct_engineer_cost * self.MANAGEMENT_RATE, 4) if include_management else 0
        profit_base = direct_engineer_cost + management_fee
        profit = round(profit_base * self.PROFIT_RATE, 4) if include_profit else 0
        subtotal = direct_engineer_cost + management_fee + profit + sum(external_costs)
        tax_rate = self.TAX_RATES.get(tax_type, 0.06)
        tax = round(subtotal * tax_rate, 4)
        basic_reserve = round(subtotal * self.BASIC_RESERVE_RATE, 4) if include_basic_reserve else 0
        price_reserve = round(subtotal * self.PRICE_RESERVE_RATE, 4) if include_price_reserve else 0
        risk_fee = round(subtotal * self.RISK_RATE, 4) if include_risk else 0
        warranty_fee = round(labor_cost * self.WARRANTY_RATE, 4) if include_warranty else 0
        total = round(subtotal + tax + basic_reserve + price_reserve + risk_fee + warranty_fee, 4)

        details = [
            {"category": "人工费", "item_name": "直接人工费", "base_amount": labor_cost, "rate": 0, "amount": labor_cost, "note": ""},
        ]
        for mf in measure_fees:
            details.append({"category": "措施费", **mf, "note": ""})
        details.append({"category": "直接工程费", "item_name": "直接工程费合计", "base_amount": 0, "rate": 0, "amount": direct_engineer_cost, "note": ""})
        if include_management:
            details.append({"category": "管理费", "item_name": "企业管理费", "base_amount": direct_engineer_cost, "rate": self.MANAGEMENT_RATE * 100, "amount": management_fee, "note": ""})
        if include_profit:
            details.append({"category": "利润", "item_name": "利润", "base_amount": round(direct_engineer_cost + management_fee, 4), "rate": self.PROFIT_RATE * 100, "amount": profit, "note": ""})
        for ec in external_costs:
            details.append({"category": "其他费用", "item_name": ec.get("name", ""), "base_amount": 0, "rate": 0, "amount": ec.get("amount", 0), "note": ""})
        details.append({"category": "税金", "item_name": f"增值税({tax_type})", "base_amount": subtotal, "rate": tax_rate * 100, "amount": tax, "note": ""})
        if include_basic_reserve:
            details.append({"category": "预备费", "item_name": "基本预备费", "base_amount": subtotal, "rate": self.BASIC_RESERVE_RATE * 100, "amount": basic_reserve, "note": ""})
        if include_price_reserve:
            details.append({"category": "预备费", "item_name": "价差预备费", "base_amount": subtotal, "rate": self.PRICE_RESERVE_RATE * 100, "amount": price_reserve, "note": ""})
        if include_risk:
            details.append({"category": "风险费", "item_name": "风险费", "base_amount": subtotal, "rate": self.RISK_RATE * 100, "amount": risk_fee, "note": ""})
        if include_warranty:
            details.append({"category": "质保服务费", "item_name": "质保服务费", "base_amount": labor_cost, "rate": self.WARRANTY_RATE * 100, "amount": warranty_fee, "note": ""})
        details.append({"category": "总造价", "item_name": "总造价合计", "base_amount": 0, "rate": 0, "amount": total, "note": ""})

        return {
            "details": details,
            "summary": {
                "labor_cost": labor_cost,
                "measure_total": measure_total,
                "direct_engineer_cost": direct_engineer_cost,
                "management_fee": management_fee,
                "profit": profit,
                "external_costs_total": round(sum(external_costs), 4),
                "subtotal_before_tax": subtotal,
                "tax": tax,
                "basic_reserve": basic_reserve,
                "price_reserve": price_reserve,
                "risk_fee": risk_fee,
                "warranty_fee": warranty_fee,
                "total_cost": total,
            }
        }