import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import traceback

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    app.config['JSON_AS_ASCII'] = False
    app.json.ensure_ascii = False

    os.makedirs(app.instance_path, exist_ok=True)

    CORS(app)
    db.init_app(app)

    from app.api.project import project_bp
    from app.api.dev_estimate import dev_estimate_bp
    from app.api.ops_estimate import ops_estimate_bp
    from app.api.export import export_bp
    from app.api.auth import auth_bp
    from app.fp_generator import fp_gen_bp
    from app.ai_fp import ai_fp_bp
    from app.upload import upload_bp

    app.register_blueprint(project_bp, url_prefix='/api/project')
    app.register_blueprint(dev_estimate_bp, url_prefix='/api/estimate/dev')
    app.register_blueprint(ops_estimate_bp, url_prefix='/api/estimate/ops')
    app.register_blueprint(export_bp, url_prefix='/api/export')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(fp_gen_bp, url_prefix='/api/fp')
    app.register_blueprint(ai_fp_bp, url_prefix='/api/fp')

    with app.app_context():
        from app.models import project, fp_item, estimate_result, user
        db.create_all()

    @app.errorhandler(Exception)
    def handle_error(e):
        traceback.print_exc()
        code = 500
        msg = str(e)[:200] if str(e) else '服务器内部错误'
        if hasattr(e, 'code'):
            code = e.code
        return jsonify({'code': code, 'message': msg}), code

    # 生产环境下服务静态文件（Vue 构建输出）
    frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'frontend', 'dist')
    if os.path.exists(frontend_dist):
        from flask import send_from_directory
        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def serve_frontend(path):
            if path and os.path.exists(os.path.join(frontend_dist, path)):
                return send_from_directory(frontend_dist, path)
            return send_from_directory(frontend_dist, 'index.html')

    return app
