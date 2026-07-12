from app import db

class EstimateVersion(db.Model):
    __tablename__ = 'estimate_versions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    version_name = db.Column(db.String(50), default='标准版', comment='版本名称: 标准版/压缩工期版/低成本版/国产化加价版')
    estimate_type = db.Column(db.String(20), default='dev', comment='dev/ops')

    # 项目特征/调整因子 (开发)
    application_type = db.Column(db.String(50), default='业务处理', comment='应用类型')
    distributed_score = db.Column(db.Integer, default=0)
    performance_score = db.Column(db.Integer, default=0)
    reliability_score = db.Column(db.Integer, default=0)
    multi_site_score = db.Column(db.Integer, default=0)
    integrity_level = db.Column(db.String(50), default='C/D级别或无明确完整性级别')
    dev_language = db.Column(db.String(50), default='JAVA、C++、C#及其他同级别语言/平台')
    team_background = db.Column(db.String(50), default='为其他行业开发过类似的项目，或为本行业开发过不同但相关的项目')
    scale_timing = db.Column(db.String(20), default='post_delivery', comment='估算时机: early_stage/mid_stage/late_stage/post_delivery')

    # 运维调整因子
    ops_business_importance = db.Column(db.String(10), default='一般')
    ops_update_frequency = db.Column(db.String(20), default='平均每月1次或以下')
    ops_support_mode = db.Column(db.String(20), default='现场支持为主')
    ops_security_level = db.Column(db.String(10), default='第三级')
    ops_response_time = db.Column(db.String(30), default='一级故障处理时间小于48h')
    ops_integrity_level = db.Column(db.String(50), default='C/D级别或无明确完整性级别')
    ops_deploy_mode = db.Column(db.String(10), default='集中式')
    ops_user_scale = db.Column(db.String(20), default='小于等于10000')
    ops_system_correlation = db.Column(db.String(20), default='1-5个系统')
    ops_team_experience = db.Column(db.String(50), default='为其他行业做过类似的项目，或为本行业做过不同但相关的项目')
    ops_confidential = db.Column(db.String(10), default='非涉密')
    ops_software_level = db.Column(db.String(10), default='中级')

    # 费用参数
    city = db.Column(db.String(20), default='北京')
    pdr_percentile = db.Column(db.String(10), default='median', comment='PDR采用: lower/median/upper')
    person_month_rate = db.Column(db.Float, default=3.2198, comment='人月单价(万元)')
    has_survey_fee = db.Column(db.Boolean, default=True, comment='需求调研费')
    has_test_fee = db.Column(db.Boolean, default=True, comment='测试费')
    has_third_party_test = db.Column(db.Boolean, default=False, comment='第三方测评')
    has_security_test = db.Column(db.Boolean, default=False, comment='安全测评')
    has_supervision = db.Column(db.Boolean, default=False, comment='监理费')
    has_training = db.Column(db.Boolean, default=True, comment='培训费')
    tax_type = db.Column(db.String(10), default='一般计税', comment='简易计税/一般计税')
    overall_discount = db.Column(db.Float, default=1.0, comment='整体下浮比例')

    # 运维费率法参数
    ops_rate_percentile = db.Column(db.String(10), default='P50')
    ops_it_asset_amount = db.Column(db.Float, default=0, comment='IT资产额/开发费用(万元)')

    # 计算结果(缓存)
    raw_fp = db.Column(db.Float, default=0, comment='原始功能点')
    adjusted_fp = db.Column(db.Float, default=0, comment='调整后功能点')
    raw_workload = db.Column(db.Float, default=0, comment='未调整工作量(人时)')
    adjusted_workload = db.Column(db.Float, default=0, comment='调整后工作量(人天)')
    person_months = db.Column(db.Float, default=0, comment='人月数')
    labor_cost = db.Column(db.Float, default=0, comment='人工费(万元)')
    total_cost = db.Column(db.Float, default=0, comment='总造价(万元)')

    created_at = db.Column(db.DateTime, default=db.func.now())

    items = db.relationship('FpItem', backref='version', lazy='dynamic', cascade='all, delete-orphan')
    cost_details = db.relationship('CostDetail', backref='version', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        d = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        d['created_at'] = self.created_at.isoformat() if self.created_at else ''
        return d


class CostDetail(db.Model):
    __tablename__ = 'cost_details'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    version_id = db.Column(db.Integer, db.ForeignKey('estimate_versions.id'), nullable=False)
    category = db.Column(db.String(50), comment='费用类别: 人工费/措施费/管理费/利润/税金/预备费')
    item_name = db.Column(db.String(100), comment='费用项名称')
    base_amount = db.Column(db.Float, default=0, comment='基数(万元)')
    rate = db.Column(db.Float, default=0, comment='费率(%)')
    amount = db.Column(db.Float, default=0, comment='金额(万元)')
    note = db.Column(db.String(200), default='', comment='备注')

    def to_dict(self):
        return {
            'id': self.id,
            'version_id': self.version_id,
            'category': self.category,
            'item_name': self.item_name,
            'base_amount': self.base_amount,
            'rate': self.rate,
            'amount': self.amount,
            'note': self.note,
        }
