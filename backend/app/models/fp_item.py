from app import db

class FpItem(db.Model):
    __tablename__ = 'fp_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    version_id = db.Column(db.Integer, db.ForeignKey('estimate_versions.id'), nullable=True)

    seq = db.Column(db.Integer, default=0, comment='序号')
    subsystem = db.Column(db.String(100), default='', comment='子系统')
    module_l1 = db.Column(db.String(100), default='', comment='一级模块')
    module_l2 = db.Column(db.String(100), default='', comment='二级模块')
    module_l3 = db.Column(db.String(100), default='', comment='三级模块')
    module_l4 = db.Column(db.String(100), default='', comment='四级模块')
    description = db.Column(db.String(500), default='', comment='功能项描述')
    fp_name = db.Column(db.String(200), default='', comment='功能点计数项名称')
    category = db.Column(db.String(10), default='EI', comment='类别: ILF/EIF/EI/EO/EQ')
    ufp = db.Column(db.Float, default=4, comment='未调整功能点数')
    reuse_level = db.Column(db.String(10), default='low', comment='重用程度: high/medium/low')
    modify_type = db.Column(db.String(10), default='new', comment='修改类型: new/modify/delete')
    us = db.Column(db.Float, default=0, comment='调整后功能点(US)')
    note = db.Column(db.String(500), default='', comment='备注')

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'version_id': self.version_id,
            'seq': self.seq,
            'subsystem': self.subsystem,
            'module_l1': self.module_l1,
            'module_l2': self.module_l2,
            'module_l3': self.module_l3,
            'module_l4': self.module_l4,
            'description': self.description,
            'fp_name': self.fp_name,
            'category': self.category,
            'ufp': self.ufp,
            'reuse_level': self.reuse_level,
            'modify_type': self.modify_type,
            'us': self.us,
            'note': self.note,
        }
