from app.utils.data_loader import load_dev_library, load_ops_library

class FpCounter:
    """??????? - ????BSCEA????"""

    def __init__(self, method="estimated"):
        self.lib = load_dev_library()
        self.weights = self.lib["ufp_weights"][method]
        self.reuse_coeffs = self.lib["reuse_coefficients"]
        self.mod_coeffs = self.lib["modification_type"]

    @staticmethod
    def get_category_weight(category, method="estimated"):
        lib = load_dev_library()
        weights = lib["ufp_weights"][method]
        return weights.get(category, 4)

    def compute_us(self, ufp, reuse_level="low", modify_type="new"):
        """????????US(??????)"""
        reuse_factor = self.reuse_coeffs.get(reuse_level, 1.0)
        mod_factor = self.mod_coeffs.get(modify_type, 1.0)
        return round(ufp * reuse_factor * mod_factor, 4)

    def compute_raw_fp(self, items):
        """????FP??"""
        return sum(item.get("ufp", 0) for item in items) if items else 0

    def compute_total_us(self, items):
        """????????US??"""
        total = 0
        for item in items or []:
            us = self.compute_us(
                item.get("ufp", 0),
                item.get("reuse_level", "low"),
                item.get("modify_type", "new")
            )
            total += us
        return total

    def apply_scale_change(self, total_us, timing="post_delivery"):
        """??????????"""
        factor = self.lib["scale_change_factors"].get(timing, 1.0)
        return round(total_us * factor, 2)

    def get_reuse_factor(self, level):
        return self.reuse_coeffs.get(level, 1.0)

    def get_mod_factor(self, mod_type):
        return self.mod_coeffs.get(mod_type, 1.0)

    def apply_complexity_weight(self, category, complexity):
        """?????????(??: ?????????)"""
        return self.weights.get(category, 4)


class DevAdjustmentEngine:
    """?????????"""

    def __init__(self):
        self.lib = load_dev_library()

    def get_application_type_factor(self, app_type_name):
        for at in self.lib["application_types"]:
            if at["name"] == app_type_name or at["desc"].startswith(app_type_name):
                return at["factor"]
        return 1.0

    def get_non_functional_factor(self, scores):
        """scores: [distributed, performance, reliability, multi_site]"""
        total_score = sum(scores)
        return 1 + total_score * 0.025

    def get_integrity_factor(self, level_name):
        for item in self.lib["integrity_level"]:
            if item["name"] == level_name or item["desc"].startswith(level_name):
                return item["factor"]
        return 1.0

    def get_language_factor(self, lang_name):
        for lang in self.lib["dev_languages"]:
            if lang["name"] == lang_name or lang_name in lang["name"]:
                return lang["factor"]
        return 1.0

    def get_team_factor(self, bg_name):
        for bg in self.lib["team_background"]:
            if bg["name"] == bg_name or bg_name in bg["name"]:
                return bg["factor"]
        return 1.0

    def compute_total_factor(self, app_type, nf_scores, integrity, language, team):
        af = self.get_application_type_factor(app_type)
        nf = self.get_non_functional_factor(nf_scores)
        inf = self.get_integrity_factor(integrity)
        lf = self.get_language_factor(language)
        tf = self.get_team_factor(team)
        return round(af * nf * inf * lf * tf, 4)


class IndustryData:
    """?????????"""
    def __init__(self):
        from app.utils.data_loader import load_csbmk, load_city_price
        self.csbmk = load_csbmk()
        self.cp = load_city_price()

    def get_dev_pdr(self, industry="??", percentile="median"):
        ind_data = self.csbmk["dev_pdr"]["by_industry"].get(industry, self.csbmk["dev_pdr"]["by_industry"]["??"])
        return ind_data.get(percentile, ind_data["median"])

    def get_ops_pdr(self, industry="??", percentile="median"):
        ind_data = self.csbmk["ops_pdr"]["by_industry"].get(industry, self.csbmk["ops_pdr"]["by_industry"]["??"])
        return ind_data.get(percentile, ind_data["median"])

    def get_city_rate(self, city="??", rate_type="dev"):
        cities = self.cp["cities"]
        if city in cities:
            return cities[city][f"{rate_type}_rate"]
        return 2.2

    def get_industries(self):
        return self.csbmk.get("industries", ["??"])

    def get_cities(self):
        return list(self.cp["cities"].keys())
