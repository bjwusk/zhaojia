import os, uuid, traceback
from flask import Blueprint, request, jsonify

upload_bp = Blueprint("upload", __name__)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

from app.doc_processor import process_document


@upload_bp.route("/analyze", methods=["POST"])
def analyze_doc():
    if "file" not in request.files:
        return jsonify({"code": 400, "message": "请上传文件"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"code": 400, "message": "文件名为空"}), 400

    api_key = request.form.get("api_key", "") or request.headers.get("X-DeepSeek-Key", "")
    fp_method = request.form.get("fp_method", "estimated")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    save_name = str(uuid.uuid4()) + "." + ext if ext else str(uuid.uuid4())
    filepath = os.path.join(UPLOAD_DIR, save_name)
    file.save(filepath)

    try:
        result = process_document(filepath, api_key=api_key, fp_method=fp_method)
        result["filename"] = file.filename
        result["filepath"] = filepath
        # Store the saved file path for later retrieval
        result["saved_path"] = filepath
        return jsonify({"code": 0, "data": result})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"code": 500, "message": "文档处理失败: " + str(e)[:200]}), 500


@upload_bp.route("/text/<path:filepath>", methods=["GET"])
def get_document_text(filepath):
    """按文件路径获取文档文本内容（支持分段读取）"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 200, type=int)

    full_path = os.path.join(UPLOAD_DIR, os.path.basename(filepath))
    if not os.path.exists(full_path):
        # Try as absolute path
        if os.path.exists(filepath):
            full_path = filepath
        else:
            return jsonify({"code": 404, "message": "文档文件不存在"}), 404

    # Read text from the original uploaded file or from saved processed text
    ext = full_path.rsplit(".", 1)[-1].lower() if "." in full_path else ""
    text = ""
    try:
        if ext in ("txt",):
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        elif ext in ("docx", "doc"):
            from docx import Document
            doc = Document(full_path)
            text = "\n".join(p.text for p in doc.paragraphs)
        elif ext == "pdf":
            # Try to get processed text - check if _text file exists
            text_path = full_path + "_text.txt"
            if os.path.exists(text_path):
                with open(text_path, "r", encoding="utf-8") as f:
                    text = f.read()
            else:
                from app.doc_processor import extract_text_from_pdf
                text = extract_text_from_pdf(full_path)
                # Cache for next time
                try:
                    with open(text_path, "w", encoding="utf-8") as f:
                        f.write(text)
                except:
                    pass
    except Exception as e:
        return jsonify({"code": 500, "message": "读取文档失败: " + str(e)[:100]}), 500

    if not text:
        return jsonify({"code": 404, "message": "文档内容为空"}), 404

    lines = text.split("\n")
    total_lines = len(lines)
    total_pages = max(1, (total_lines + per_page - 1) // per_page)

    start = (page - 1) * per_page
    end = start + per_page
    page_lines = lines[start:end]
    page_text = "\n".join(page_lines)

    return jsonify({
        "code": 0,
        "data": {
            "text": page_text,
            "total_lines": total_lines,
            "total_pages": total_pages,
            "page": page,
            "per_page": per_page,
        }
    })