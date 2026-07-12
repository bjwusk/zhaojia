from flask import Blueprint, request, jsonify
from app.services.estimate_service import EstimateService
from app.models.estimate_result import EstimateVersion
from app.models.fp_item import FpItem
from app.core.fp_counter import FpCounter
from app import db

dev_estimate_bp = Blueprint("dev_estimate", __name__)
svc = EstimateService()

@dev_estimate_bp.route("/version", methods=["POST"])
def create_version():
    data = request.get_json()
    version = svc.create_version(
        project_id=data.get("project_id"),
        version_name=data.get("version_name", "正式版"),
        estimate_type="dev",
    )
    return jsonify({"code": 0, "data": version.to_dict()}), 201

@dev_estimate_bp.route("/version/<int:version_id>", methods=["GET"])
def get_version(version_id):
    result = svc.get_version(version_id)
    if not result:
        return jsonify({"code": 404, "message": "测算版本不存在"}), 404
    return jsonify({"code": 0, "data": result})

@dev_estimate_bp.route("/version/<int:version_id>/items", methods=["POST"])
def save_items(version_id):
    data = request.get_json()
    items = data.get("items", [])
    project_id = data.get("project_id")
    for item in items:
        item["project_id"] = project_id
        item["version_id"] = version_id
    svc.save_items(version_id, items)
    return jsonify({"code": 0, "message": "保存成功"})

@dev_estimate_bp.route("/version/<int:version_id>/calculate", methods=["POST"])
def calculate(version_id):
    data = request.get_json()
    version = EstimateVersion.query.get(version_id)
    if not version:
        return jsonify({"code": 404, "message": "测算版本不存在"}), 404

    items = FpItem.query.filter_by(version_id=version_id).all()
    item_list = [it.to_dict() for it in items]
    if not items and data.get("items"):
        item_list = data["items"]

    params = {
        "items": item_list,
        "application_type": data.get("application_type", version.application_type or "业务处理"),
        "nf_scores": [
            data.get("distributed_score", version.distributed_score or 0),
            data.get("performance_score", version.performance_score or 0),
            data.get("reliability_score", version.reliability_score or 0),
            data.get("multi_site_score", version.multi_site_score or 0),
        ],
        "integrity_level": data.get("integrity_level", version.integrity_level or "C/D级别或无明确完整性级别"),
        "dev_language": data.get("dev_language", version.dev_language or "JAVA、C++、C#及其他同级别语言/平台"),
        "team_background": data.get("team_background", version.team_background or "为其他行业开发过类似的项目，或为本行业开发过不同但相关的项目"),
        "scale_timing": data.get("scale_timing", version.scale_timing or "post_delivery"),
        "pdr_percentile": data.get("pdr_percentile", "median"),
        "city": data.get("city", "北京"),
        "person_month_rate": data.get("person_month_rate", 3.2198),
        "fee_params": data.get("fee_params", {}),
    }

    result = svc.run_dev_estimate(version_id, params)

    for key in ["application_type", "integrity_level", "dev_language", "team_background",
                 "scale_timing", "city"]:
        if key in data:
            setattr(version, key, data[key])
    for key in ["distributed_score", "performance_score", "reliability_score", "multi_site_score"]:
        if key in data:
            setattr(version, key, data[key])
    if "person_month_rate" in data:
        version.person_month_rate = data["person_month_rate"]
    db.session.commit()

    return jsonify({"code": 0, "data": result})

@dev_estimate_bp.route("/project/<int:project_id>/versions", methods=["GET"])
def list_versions(project_id):
    versions = EstimateVersion.query.filter_by(
        project_id=project_id, estimate_type="dev"
    ).order_by(EstimateVersion.created_at.desc()).all()
    return jsonify({"code": 0, "data": [v.to_dict() for v in versions]})
