from app.core.fp_counter import FpCounter, IndustryData
from app.utils.data_loader import load_ops_library, load_csbmk, load_city_price

class OpsCalculator:
    '''??????? - ????BSCEA??'''

    def __init__(self, fp_method='estimated'):
        self.fp_counter = FpCounter(fp_method)
        self.lib = load_ops_library()
        self.csbmk = load_csbmk()
        self.city_price = load_city_price()

    def get_ops_factor(self, factor_key, option_name):
        '''????????'''
        factors = self.lib['ops_adjustment_factors'].get(factor_key)
        if not factors:
            return 1.0
        for opt in factors['options']:
            if opt['name'] == option_name or option_name in opt['name']:
                return opt['factor']
        return 1.0

    def compute_total_ops_factor(self, params):
        '''??????????'''
        factors = [
            self.get_ops_factor('business_importance', params.get('business_importance', '??')),
            self.get_ops_factor('update_frequency', params.get('update_frequency', '????1????')),
            self.get_ops_factor('support_mode', params.get('support_mode', '??????')),
            self.get_ops_factor('security_level', params.get('security_level', '???')),
            self.get_ops_factor('response_time', params.get('response_time', '??????????8h')),
            self.get_ops_factor('integrity_level', params.get('integrity_level', 'C/D???????????')),
            self.get_ops_factor('deploy_mode', params.get('deploy_mode', '????')),
            self.get_ops_factor('user_scale', params.get('user_scale', '????10000')),
            self.get_ops_factor('system_correlation', params.get('system_correlation', '1-5???')),
            self.get_ops_factor('team_experience', params.get('team_experience', '????????????????????????????')),
            self.get_ops_factor('confidential', params.get('confidential', '???')),
        ]
        total = 1.0
        for f in factors:
            total *= f
        return round(total, 4)

    def calculate(self, params):
        items = params.get('items', [])
        raw_fp = self.fp_counter.compute_raw_fp(items)
        total_us = self.fp_counter.compute_total_us(items)
        adjusted_fp = self.fp_counter.apply_scale_change(
            total_us, params.get('scale_timing', 'completed')
        )
        pdr_key = params.get('pdr_percentile', 'median')
        industry = params.get('industry', '??')
        idata = IndustryData()
        pdr = idata.get_ops_pdr(industry, pdr_key)
        raw_workload = round(adjusted_fp * pdr, 2)
        ops_factor = self.compute_total_ops_factor(params)
        workday_hours = self.lib['workday_hours']
        adjusted_workload = round(raw_workload / workday_hours * ops_factor, 2)
        pm_hours = self.lib['person_month_hours']
        person_months = round(adjusted_workload / pm_hours, 2)
        city = params.get('city', '??')
        monthly_rate = params.get('person_month_rate', None)
        if monthly_rate is None:
            monthly_rate = idata.get_city_rate(city, 'ops')
        labor_cost = round(person_months * monthly_rate, 4)

        rate_method_amount = 0
        rate_key = params.get('ops_rate_percentile', 'P50')
        it_asset = params.get('ops_it_asset_amount', 0)
        if it_asset > 0:
            rate_val = self.lib['ops_rate_method']['rates'].get(rate_key, 0.0902)
            rate_method_amount = round(it_asset * rate_val, 4)

        return {
            'raw_fp': raw_fp, 'total_us': total_us, 'adjusted_fp': adjusted_fp,
            'pdr': pdr, 'raw_workload_hours': raw_workload,
            'ops_factor': ops_factor, 'adjusted_workload_days': adjusted_workload,
            'person_months': person_months, 'monthly_rate': monthly_rate,
            'labor_cost': labor_cost, 'rate_method_amount': rate_method_amount,
        }
