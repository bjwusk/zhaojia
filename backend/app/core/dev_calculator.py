from app.core.fp_counter import FpCounter, DevAdjustmentEngine
from app.core.fp_counter import IndustryData
from app.utils.data_loader import load_dev_library, load_csbmk, load_city_price

class DevCalculator:
    """??????? - ????BSCEA??"""

    def __init__(self, fp_method="estimated"):
        self.fp_counter = FpCounter(fp_method)
        self.adj_engine = DevAdjustmentEngine()
        self.lib = load_dev_library()
        self.csbmk = load_csbmk()
        self.city_price = load_city_price()

    def calculate(self, params):
        """
        params: {
            items: [{ufp, reuse_level, modify_type}],
            application_type, nf_scores: [d, p, r, m],
            integrity_level, dev_language, team_background,
            scale_timing, pdr_percentile, city, person_month_rate
        }
        ?????:
        ??FP -> US(?????????) -> ?????(???????)
        -> ??????(FP?PDR) -> ?????(??????????????????)
        -> ?????(/8) -> ???(/174) -> ???(?????)
        """
        items = params.get("items", [])

        # 1. ??FP
        raw_fp = self.fp_counter.compute_raw_fp(items)

        # 2. US??
        total_us = self.fp_counter.compute_total_us(items)

        # 3. ?????
        adjusted_fp = self.fp_counter.apply_scale_change(
            total_us, params.get("scale_timing", "post_delivery")
        )

        # 4. PDR
        pdr_key = params.get("pdr_percentile", "median")
        pdr = self.csbmk["dev_pdr"].get(pdr_key, self.csbmk["dev_pdr"]["median"])

        # 5. ??????(??)
        raw_workload = round(adjusted_fp * pdr, 2)

        # 6. ??????
        nf_scores = params.get("nf_scores", [0, 0, 0, 0])
        total_factor = self.adj_engine.compute_total_factor(
            params.get("application_type", "????"),
            nf_scores,
            params.get("integrity_level", "C/D???????????"),
            params.get("dev_language", "JAVA?C++?C#????????/??"),
            params.get("team_background", "??????????????????????????????")
        )

        # 7. ??????(??)
        workday_hours = self.lib["workday_hours"]
        adjusted_workload = round(raw_workload / workday_hours * total_factor, 2)

        # 8. ???
        pm_hours = self.lib["person_month_hours"]
        person_months = round(adjusted_workload / pm_hours, 2)

        # 9. ???
        city = params.get("city", "??")
        monthly_rate = params.get("person_month_rate", None)
        if monthly_rate is None:
            idata = IndustryData()
            monthly_rate = idata.get_city_rate(city, "dev")
        labor_cost = round(person_months * monthly_rate, 4)

        return {
            "raw_fp": raw_fp,
            "total_us": total_us,
            "adjusted_fp": adjusted_fp,
            "pdr": pdr,
            "raw_workload_hours": raw_workload,
            "total_factor": total_factor,
            "adjusted_workload_days": adjusted_workload,
            "person_months": person_months,
            "monthly_rate": monthly_rate,
            "labor_cost": labor_cost,
        }
