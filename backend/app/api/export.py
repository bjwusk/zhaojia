"""导出API - v3 支持ZIP打包下载"""
from flask import Blueprint, send_file, request, jsonify
from app.services.bsca_service import fill_excel, read_excel_results
from app.services.word_service import fill_report, calc_full_cost, create_zip_package
from app.models.project import Project
from app.models.fp_item import FpItem
from app.models.estimate_result import EstimateVersion
from app import db
import os, json

export_bp = Blueprint("export", __name__)


@export_bp.route("/generate", methods=["POST"])
def generate_cost_files():
    """生成造价文件（Excel + Word + ZIP），返回完整费用明细"""
    data = request.get_json()
    project_id = data.get("project_id")
    fp_items_data = data.get("fp_items", [])
    params = data.get("params", {})
    project_name = data.get("project_name", "软件项目")
    doc_text = data.get("doc_text", "")          # 文档建设内容
    doc_filename = data.get("doc_filename", "")  # 文档原始文件名

    if project_id:
        proj = Project.query.get(project_id)
        if proj:
            project_name = proj.name or project_name
            # 从项目加载文档文本
            if not doc_text and hasattr(proj, "document_file") and proj.document_file:
                try:
                    with open(proj.document_file, "r", encoding="utf-8", errors="replace") as f:
                        doc_text = f.read()[:2000]
                except:
                    pass
            if not fp_items_data:
                version = EstimateVersion.query.filter_by(project_id=project_id).order_by(EstimateVersion.created_at.desc()).first()
                if version:
                    items = FpItem.query.filter_by(version_id=version.id).all()
                    fp_items_data = [it.to_dict() for it in items]

    # 填入BSCEA Excel
    excel_result = fill_excel(fp_items_data, params)
    calc_result = excel_result["result"]
    excel_path = excel_result["filepath"]

    # 计算完整费用链
    labor_cost = calc_result.get("labor_cost_median", 0) or 0
    fee_params = params.get("fee_params", {}) if params else {}
    cost_chain = calc_full_cost(labor_cost, fee_params)

    # 填入Word报告（传文档文本和文件名）
    word_path = fill_report(project_name, calc_result, fp_items_data, params,
                            doc_text=doc_text, doc_filename=doc_filename)

    # 打包ZIP
    zip_path = create_zip_package(project_name, excel_path, word_path)

    display_result = dict(calc_result)
    display_result["cost_chain"] = cost_chain
    display_result["labor_cost"] = labor_cost
    display_result["person_months"] = calc_result.get("person_months_median", 0)
    display_result["total_cost"] = cost_chain["total"]
    display_result["pdr"] = calc_result.get("pdr_median", 6.72)

    return jsonify({
        "code": 0,
        "data": {
            "calculation": display_result,
            "excel_path": excel_path,
            "word_path": word_path,
            "zip_path": zip_path,
            "excel_filename": os.path.basename(excel_path),
            "word_filename": os.path.basename(word_path),
            "zip_filename": os.path.basename(zip_path),
        },
        "message": "造价文件生成成功"
    })


@export_bp.route("/download/<path:filepath>", methods=["GET"])
def download_file(filepath):
    """下载生成的文件（支持Excel/Word/ZIP）"""
    EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "exports")
    full_path = os.path.join(EXPORT_DIR, os.path.basename(filepath))
    if not os.path.exists(full_path):
        return jsonify({"code": 404, "message": "文件不存在"}), 404

    # 根据扩展名设置MIME类型
    ext = os.path.splitext(full_path)[1].lower()
    mime_map = {".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ".zip": "application/zip"}
    mime = mime_map.get(ext, "application/octet-stream")

    return send_file(full_path, as_attachment=True,
                     download_name=os.path.basename(full_path),
                     mimetype=mime)


@export_bp.route("/calculate", methods=["POST"])
def calculate_only():
    """仅计算（不生成文件），返回测算结果"""
    data = request.get_json()
    fp_items_data = data.get("fp_items", [])
    params = data.get("params", {})

    excel_result = fill_excel(fp_items_data, params)
    calc_result = excel_result["result"]
    labor_cost = calc_result.get("labor_cost_median", 0) or 0
    fee_params = params.get("fee_params", {}) if params else {}
    cost_chain = calc_full_cost(labor_cost, fee_params)

    display_result = dict(calc_result)
    display_result["cost_chain"] = cost_chain
    display_result["labor_cost"] = labor_cost
    display_result["person_months"] = calc_result.get("person_months_median", 0)
    display_result["total_cost"] = cost_chain["total"]

    return jsonify({
        "code": 0,
        "data": {"calculation": display_result}
    })
