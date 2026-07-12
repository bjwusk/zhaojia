import os, json
from flask import Blueprint, request, jsonify
from app.services.project_service import ProjectService
from app import db
from app.models.project import Project

project_bp = Blueprint("project", __name__)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "uploads")


@project_bp.route("", methods=["GET"])
def list_projects():
    search = request.args.get("search", "")
    industry = request.args.get("industry", "")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    projects, total = ProjectService.list_all(search, industry, page, per_page)
    return jsonify({"code": 0, "data": [p.to_dict() for p in projects], "total": total})


@project_bp.route("/<int:project_id>", methods=["GET"])
def get_project(project_id):
    project = ProjectService.get_by_id(project_id)
    if not project:
        return jsonify({"code": 404, "message": "项目不存在"}), 404
    return jsonify({"code": 0, "data": project.to_dict()})


@project_bp.route("", methods=["POST"])
def create_project():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"code": 400, "message": "请输入项目名称"}), 400
    project = ProjectService.create(data)
    return jsonify({"code": 0, "data": project.to_dict(), "message": "创建成功"}), 201


@project_bp.route("/<int:project_id>", methods=["PUT"])
def update_project(project_id):
    data = request.get_json()
    project = ProjectService.update(project_id, data)
    if not project:
        return jsonify({"code": 404, "message": "项目不存在"}), 404
    return jsonify({"code": 0, "data": project.to_dict(), "message": "更新成功"})


@project_bp.route("/<int:project_id>", methods=["DELETE"])
def delete_project(project_id):
    if ProjectService.delete(project_id):
        return jsonify({"code": 0, "message": "删除成功"})
    return jsonify({"code": 404, "message": "项目不存在"}), 404


@project_bp.route("/<int:project_id>/document", methods=["POST"])
def save_document(project_id):
    """保存文档文本到服务器文件"""
    project = ProjectService.get_by_id(project_id)
    if not project:
        return jsonify({"code": 404, "message": "项目不存在"}), 404

    data = request.get_json()
    text_content = data.get("text", "")
    file_path = data.get("file_path", "")

    if file_path and os.path.exists(file_path):
        project.document_file = file_path

    if text_content:
        # Save text to a file in uploads directory
        doc_file = os.path.join(UPLOAD_DIR, f"doc_{project_id}.txt")
        with open(doc_file, "w", encoding="utf-8") as f:
            f.write(text_content)
        project.document_file = doc_file

    db.session.commit()
    return jsonify({"code": 0, "message": "文档保存成功"})


@project_bp.route("/<int:project_id>/document", methods=["GET"])
def get_document(project_id):
    project = ProjectService.get_by_id(project_id)
    if not project:
        return jsonify({"code": 404, "message": "?????"}), 404
    text = ""
    if project.document_file and os.path.exists(project.document_file):
        try:
            with open(project.document_file, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except:
            pass
    if not text and project.description:
        text = project.description
    if not text:
        return jsonify({"code": 404, "message": "??????"}), 404
    sections = []
    import re
    for i, line in enumerate(text.split("\n")):
        s = line.strip()
        if s and ((s.startswith("?") and ("?" in s or "?" in s)) or
                  re.match(r"^[????????????]+[?. ]", s) or
                  re.match(r"^\\d+[?.\\s]", s)):
            sections.append({"title": s[:60], "line": i})
    return jsonify({
        "code": 0,
        "data": {
            "text": text[:500000],
            "total_lines": len(text.split("\n")),
            "total_pages": 1,
            "page": 1,
            "per_page": 999999,
            "sections": sections[:200],
        }
    })

