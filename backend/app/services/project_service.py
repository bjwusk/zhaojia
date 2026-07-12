from app import db
from app.models.project import Project

class ProjectService:

    @staticmethod
    def create(data):
        project = Project()
        for key in ['name', 'client', 'industry', 'stage', 'build_mode', 'region',
                     'is_xinchuang', 'is_confidential', 'has_hardware', 'estimate_type',
                     'description', 'creator', 'reviewer', 'cert_no', 'project_no', 'remark']:
            if key in data:
                setattr(project, key, data[key])
        db.session.add(project)
        db.session.commit()
        return project

    @staticmethod
    def get_by_id(project_id):
        return Project.query.get(project_id)

    @staticmethod
    def update(project_id, data):
        project = Project.query.get(project_id)
        if not project:
            return None
        for key in ['name', 'client', 'industry', 'stage', 'build_mode', 'region',
                     'is_xinchuang', 'is_confidential', 'has_hardware', 'estimate_type',
                     'description', 'creator', 'reviewer', 'cert_no', 'project_no', 'remark']:
            if key in data:
                setattr(project, key, data[key])
        db.session.commit()
        return project

    @staticmethod
    def delete(project_id):
        project = Project.query.get(project_id)
        if project:
            db.session.delete(project)
            db.session.commit()
            return True
        return False

    @staticmethod
    def list_all(search='', industry='', page=1, per_page=50):
        query = Project.query.order_by(Project.updated_at.desc())
        if search:
            query = query.filter(Project.name.contains(search))
        if industry:
            query = query.filter(Project.industry == industry)
        total = query.count()
        projects = query.offset((page-1)*per_page).limit(per_page).all()
        return projects, total
