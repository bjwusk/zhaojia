from app import db
import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False, comment='用户名')
    password = db.Column(db.String(200), nullable=False, comment='密码(sha256)')
    display_name = db.Column(db.String(50), default='', comment='显示名称')
    company = db.Column(db.String(100), default='', comment='所属单位')
    cert_no = db.Column(db.String(50), default='', comment='造价资质编号')
    role = db.Column(db.String(20), default='editor', comment='角色: admin/editor/viewer')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name,
            'company': self.company,
            'cert_no': self.cert_no,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else '',
        }
