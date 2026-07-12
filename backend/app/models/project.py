import datetime
from app import db

class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False, comment='项目名称')
    client = db.Column(db.String(200), default='', comment='建设单位/委托单位')
    industry = db.Column(db.String(50), default='', comment='行业分类')
    stage = db.Column(db.String(50), default='可行性研究', comment='项目阶段')
    build_mode = db.Column(db.String(50), default='自研', comment='建设模式')
    region = db.Column(db.String(50), default='北京', comment='实施地域')
    is_xinchuang = db.Column(db.Boolean, default=False, comment='是否信创')
    is_confidential = db.Column(db.Boolean, default=False, comment='是否涉密')
    has_hardware = db.Column(db.Boolean, default=False, comment='是否配套硬件/云服务')
    estimate_type = db.Column(db.String(20), default='dev', comment='测算类型: dev开发/ops运维')
    description = db.Column(db.Text, default='', comment='项目简短描述')
    document_file = db.Column(db.String(500), default='', comment='上传文档文件路径')
    creator = db.Column(db.String(50), default='', comment='编制人')
    reviewer = db.Column(db.String(50), default='', comment='审核人')
    cert_no = db.Column(db.String(50), default='', comment='造价资质编号')
    project_no = db.Column(db.String(50), default='', comment='项目编号')
    remark = db.Column(db.Text, default='', comment='归档备注')

    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    fp_items = db.relationship('FpItem', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    versions = db.relationship('EstimateVersion', backref='project', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'client': self.client,
            'industry': self.industry,
            'stage': self.stage,
            'build_mode': self.build_mode,
            'region': self.region,
            'is_xinchuang': self.is_xinchuang,
            'is_confidential': self.is_confidential,
            'has_hardware': self.has_hardware,
            'estimate_type': self.estimate_type,
            'description': self.description,
            'creator': self.creator,
            'reviewer': self.reviewer,
            'cert_no': self.cert_no,
            'project_no': self.project_no,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else '',
            'updated_at': self.updated_at.isoformat() if self.updated_at else '',
        }