from app import db
from app.models.estimate_result import EstimateVersion, CostDetail
from app.models.fp_item import FpItem
from app.core.dev_calculator import DevCalculator
from app.core.ops_calculator import OpsCalculator
from app.core.fee_engine import FeeEngine

class EstimateService:

    @staticmethod
    def run_dev_estimate(version_id, params):
        '''执行开发费测算并保存结果'''
        calculator = DevCalculator()
        result = calculator.calculate(params)

        version = EstimateVersion.query.get(version_id)
        if version:
            # 更新版本缓存结果
            version.raw_fp = result['raw_fp']
            version.adjusted_fp = result['adjusted_fp']
            version.raw_workload = result['raw_workload_hours']
            version.adjusted_workload = result['adjusted_workload_days']
            version.person_months = result['person_months']
            version.labor_cost = result['labor_cost']

            # 费用计取
            fee_params = params.get('fee_params', {})
            fee_engine = FeeEngine()
            fee_result = fee_engine.calculate(
                labor_cost=result['labor_cost'],
                measure_items=fee_params.get('measure_items', ['survey_fee', 'test_fee', 'training']),
                tax_type=fee_params.get('tax_type', '一般计税'),
                include_management=fee_params.get('include_management', True),
                include_profit=fee_params.get('include_profit', True),
                include_basic_reserve=fee_params.get('include_basic_reserve', True),
                include_price_reserve=fee_params.get('include_price_reserve', False),
                include_risk=fee_params.get('include_risk', False),
                include_warranty=fee_params.get('include_warranty', True),
                external_costs=fee_params.get('external_costs', []),
            )
            version.total_cost = fee_result['summary']['total_cost']

            # 保存费用明细
            CostDetail.query.filter_by(version_id=version_id).delete()
            for detail in fee_result['details']:
                cd = CostDetail(
                    version_id=version_id,
                    category=detail['category'],
                    item_name=detail['item_name'],
                    base_amount=detail['base_amount'],
                    rate=detail['rate'],
                    amount=detail['amount'],
                    note=detail.get('note', ''),
                )
                db.session.add(cd)

            db.session.commit()

        return {
            'calculation': result,
            'fee_result': fee_result if 'fee_result' in locals() else None,
        }

    @staticmethod
    def run_ops_estimate(version_id, params):
        '''执行运维费测算并保存结果'''
        calculator = OpsCalculator()
        result = calculator.calculate(params)

        version = EstimateVersion.query.get(version_id)
        if version:
            version.raw_fp = result['raw_fp']
            version.adjusted_fp = result['adjusted_fp']
            version.raw_workload = result['raw_workload_hours']
            version.adjusted_workload = result['adjusted_workload_days']
            version.person_months = result['person_months']
            version.labor_cost = result['labor_cost']

            # 费用计取
            fee_params = params.get('fee_params', {})
            fee_engine = FeeEngine()
            fee_result = fee_engine.calculate(
                labor_cost=result['labor_cost'],
                measure_items=fee_params.get('measure_items', ['survey_fee', 'test_fee']),
                tax_type=fee_params.get('tax_type', '一般计税'),
                include_management=fee_params.get('include_management', True),
                include_profit=fee_params.get('include_profit', True),
                include_basic_reserve=fee_params.get('include_basic_reserve', False),
                include_price_reserve=fee_params.get('include_price_reserve', False),
                include_risk=fee_params.get('include_risk', False),
                include_warranty=fee_params.get('include_warranty', False),
                external_costs=fee_params.get('external_costs', []),
            )
            version.total_cost = fee_result['summary']['total_cost']

            CostDetail.query.filter_by(version_id=version_id).delete()
            for detail in fee_result['details']:
                cd = CostDetail(
                    version_id=version_id,
                    category=detail['category'],
                    item_name=detail['item_name'],
                    base_amount=detail['base_amount'],
                    rate=detail['rate'],
                    amount=detail['amount'],
                    note=detail.get('note', ''),
                )
                db.session.add(cd)
            db.session.commit()

        return {
            'calculation': result,
            'fee_result': fee_result if 'fee_result' in locals() else None,
        }

    @staticmethod
    def create_version(project_id, version_name='标准版', estimate_type='dev'):
        version = EstimateVersion(
            project_id=project_id,
            version_name=version_name,
            estimate_type=estimate_type,
        )
        db.session.add(version)
        db.session.commit()
        return version

    @staticmethod
    def save_items(version_id, items):
        '''保存功能点条目到版本'''
        FpItem.query.filter_by(version_id=version_id).delete()
        for i, item in enumerate(items):
            fp = FpItem(
                project_id=item.get('project_id'),
                version_id=version_id,
                seq=item.get('seq', i+1),
                subsystem=item.get('subsystem', ''),
                module_l1=item.get('module_l1', ''),
                module_l2=item.get('module_l2', ''),
                module_l3=item.get('module_l3', ''),
                module_l4=item.get('module_l4', ''),
                description=item.get('description', ''),
                fp_name=item.get('fp_name', ''),
                category=item.get('category', 'EI'),
                ufp=item.get('ufp', 4),
                reuse_level=item.get('reuse_level', 'low'),
                modify_type=item.get('modify_type', 'new'),
                us=item.get('us', 0),
                note=item.get('note', ''),
            )
            db.session.add(fp)
        db.session.commit()
        return True

    @staticmethod
    def get_version(version_id):
        version = EstimateVersion.query.get(version_id)
        if not version:
            return None
        items = FpItem.query.filter_by(version_id=version_id).order_by(FpItem.seq).all()
        details = CostDetail.query.filter_by(version_id=version_id).all()
        return {
            'version': version.to_dict(),
            'items': [item.to_dict() for item in items],
            'cost_details': [d.to_dict() for d in details],
        }
