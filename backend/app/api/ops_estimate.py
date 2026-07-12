from flask import Blueprint, request, jsonify
from app.services.estimate_service import EstimateService
from app.models.estimate_result import EstimateVersion
from app.models.fp_item import FpItem
from app import db

ops_estimate_bp = Blueprint("ops_estimate", __name__)
svc = EstimateService()

@ops_estimate_bp.route("/version", methods=["POST"])
def create_version():
    data = request.get_json()
    version = svc.create_version(
        project_id=data.get("project_id"),
        version_name=data.get("version_name", "正式版"),
        estimate_type="ops",
    )
    return jsonify({"code": 0, "data": version.to_dict()}), 201

@ops_estimate_bp.route("/version/<int:version_id>", methods=["GET"])
def get_version(version_id):
    result = svc.get_version(version_id)
    if not result:
        return jsonify({"code": 404, "message": "测算版本不存在"}), 404
    return jsonify({"code": 0, "data": result})

@ops_estimate_bp.route("/version/<int:version_id>/items", methods=["POST"])
def save_items(version_id):
    data = request.get_json()
    items = data.get("items", [])
    project_id = data.get("project_id")
    for item in items:
        item["project_id"] = project_id
        item["version_id"] = version_id
    svc.save_items(version_id, items)
    return jsonify({"code": 0, "message": "保存成功"})

@ops_estimate_bp.route("/version/<int:version_id>/calculate", methods=["POST"])
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
        "scale_timing": data.get("scale_timing", version.scale_timing or "post_delivery"),
        "pdr_percentile": data.get("pdr_percentile", "median"),
        "city": data.get("city", "北京"),
        "person_month_rate": data.get("person_month_rate", None),
        "business_importance": data.get("business_importance", "一般"),
        "update_frequency": data.get("update_frequency", "平均每月1次或以下"),
        "support_mode": data.get("support_mode", "现场支持为主"),
        "security_level": data.get("security_level", "第三级"),
        "response_time": data.get("response_time", "一级故障处理时间小于8h"),
        "deploy_mode": data.get("deploy_mode", "集中部署"),
        "user_scale": data.get("user_scale", "小于等于10000"),
        "system_correlation": data.get("system_correlation", "1-5个系统"),
        "team_experience": data.get("team_experience", "为其他行业做过类似的项目，或为本行业做过不同但相关的项目"),
        "confidential": data.get("confidential", "非涉密"),
        "industry": data.get("industry", "通用"),
        "ops_rate_percentile": data.get("ops_rate_percentile", "P50"),
        "ops_it_asset_amount": data.get("ops_it_asset_amount", 0),
        "fee_params": data.get("fee_params", {}),
    }

    result = svc.run_ops_estimate(version_id, params)
    return jsonify({"code": 0, "data": result})

@ops_estimate_bp.route("/project/<int:project_id>/versions", methods=["GET"])
def list_versions(project_id):
    versions = EstimateVersion.query.filter_by(
        project_id=project_id, estimate_type="ops"
    ).order_by(EstimateVersion.created_at.desc()).all()
    return jsonify({"code": 0, "data": [v.to_dict() for v in versions]})
