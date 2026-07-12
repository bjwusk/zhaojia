import os, json, re, urllib.request, urllib.error
from flask import Blueprint, request, jsonify

ai_fp_bp = Blueprint("ai_fp", __name__)
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

FP_SYSTEM_PROMPT = """你是一位专业的软件造价评估师，精通BSCEA标准。
从需求文档中识别并提取功能点（Function Point）。

分类说明：
- ILF：内部逻辑文件，系统内部维护的数据存储，如数据库表、文件等
- EIF：外部接口文件，被本系统引用但由其他系统维护的数据
- EI：外部输入，数据录入、导入、上传、注册、采集等输入操作
- EO：外部输出，报表生成、数据导出、打印输出等输出操作
- EQ：外部查询，数据查询、检索、搜索、查看等查询操作

返回JSON格式：{"items": [{"category": "ILF", "description": "描述", "fp_name": "名称", "ufp": 35, "subsystem": "子系统名称", "module_l1": "一级模块名称"}]}
注意：ILF=35, EIF=15, EI=4, EO=5, EQ=4
请根据文档章节和内容推断每个功能点所属的子系统（subsystem）和一级模块（module_l1）。"""

@ai_fp_bp.route("/ai-generate", methods=["POST"])
def ai_generate_fps():
    data = request.get_json()
    text = data.get("text", "")
    api_key = data.get("api_key", "")
    fp_method = data.get("fp_method", "estimated")
    if not text:
        return jsonify({"code": 400, "message": "请提供文档内容"}), 400
    if not api_key:
        return jsonify({"code": 400, "message": "请先在设置中配置DeepSeek API Key"}), 400
    fp_types = "ILF、EIF" if fp_method == "estimated" else "ILF、EIF、EI、EO、EQ"
    user_prompt = ("请从以下需求文档中识别功能点，只需要识别" + fp_types + "类型。\n\n"
                   "文档内容：\n" + text)
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": FP_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 4096,
    }
    try:
        req_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            DEEPSEEK_API_URL, data=req_body,
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + api_key}
        )
        resp = urllib.request.urlopen(req, timeout=120)
        result = json.loads(resp.read().decode("utf-8"))
        ai_text = result["choices"][0]["message"]["content"]
        fps = _parse_ai_response(ai_text)
        return jsonify({"code": 0, "data": {"items": fps, "total": len(fps)}})
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return jsonify({"code": 500, "message": "DeepSeek API调用失败: " + err_body}), 500
    except Exception as e:
        return jsonify({"code": 500, "message": "AI分析异常: " + str(e)[:200]}), 500

def _parse_ai_response(ai_text):
    json_match = re.search(r"\{.*\}", ai_text, re.DOTALL)
    if not json_match:
        json_match = re.search(r"\[.*\]", ai_text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            if isinstance(data, dict) and "items" in data:
                items = data["items"]
            elif isinstance(data, list):
                items = data
            else:
                items = []
            WEIGHTS = {"ILF": 35, "EIF": 15, "EI": 4, "EO": 5, "EQ": 4}
            normalized = []
            for item in items:
                if isinstance(item, dict) and item.get("category"):
                    cat = item["category"].upper()
                    if cat in WEIGHTS:
                        normalized.append({
                            "category": cat,
                            "description": (item.get("description") or item.get("desc") or "")[:80],
                            "fp_name": (item.get("fp_name") or item.get("name") or "")[:40],
                            "ufp": WEIGHTS[cat],
                            "subsystem": (item.get("subsystem") or item.get("module") or "系统")[:20],
                            "module_l1": (item.get("module_l1") or item.get("sub_module") or "数据管理")[:20],
                            "complexity": "medium", "reuse_level": "low", "modify_type": "new"
                        })
            if normalized:
                return normalized
        except:
            pass
    return _extract_fallback(ai_text)

def _extract_fallback(text):
    results = []
    patterns = {
        "ILF": ["内部逻辑文件", "数据存储", "数据库", "数据表", "档案库"],
        "EIF": ["外部接口文件", "接口", "对接", "外部系统"],
        "EI": ["外部输入", "录入", "登记", "注册", "采集", "新增"],
        "EO": ["外部输出", "报表", "导出", "打印", "统计"],
        "EQ": ["外部查询", "查询", "检索", "搜索", "查看"]
    }
    weights = {"ILF": 35, "EIF": 15, "EI": 4, "EO": 5, "EQ": 4}
    found = set()
    for line in text.split("\n"):
        for cat, kws in patterns.items():
            for kw in kws:
                if kw in line and len(line.strip()) > len(kw) + 3:
                    key = line.strip()[:30]
                    if key not in found:
                        found.add(key)
                        results.append({
                            "category": cat, "description": line.strip()[:80],
                            "fp_name": kw, "ufp": weights[cat],
                            "subsystem": "系统", "module_l1": "数据管理",
                            "complexity": "medium", "reuse_level": "low", "modify_type": "new"
                        })
    return results

@ai_fp_bp.route("/analyze-highlight", methods=["POST"])
def analyze_and_highlight():
    """AI分析文本中的功能点并返回标注信息"""
    data = request.get_json()
    text = data.get("text", "")
    api_key = data.get("api_key", "")
    fp_method = data.get("fp_method", "estimated")
    if not text:
        return jsonify({"code": 400, "message": "请提供文本内容"}), 400
    if not api_key:
        return jsonify({"code": 400, "message": "请先在设置中配置DeepSeek API Key"}), 400

    from app.doc_processor import ai_analyze_fp_with_highlights
    try:
        result = ai_analyze_fp_with_highlights(text, api_key, fp_method)
        items = result.get("items", [])
        highlight_map = result.get("highlight_map", {})
        return jsonify({
            "code": 0,
            "data": {
                "items": items,
                "total": len(items),
                "highlight_map": highlight_map,
            }
        })
    except Exception as e:
        return jsonify({"code": 500, "message": "AI分析失败: " + str(e)[:200]}), 500
@ai_fp_bp.route("/extract-content", methods=["POST"])
def extract_construction_content():
    """AI提取文档中的建设方案核心内容"""
    data = request.get_json()
    text = data.get("text", "")
    api_key = data.get("api_key", "")
    if not text:
        return jsonify({"code": 400, "message": "请提供文本内容"}), 400
    if not api_key:
        return jsonify({"code": 400, "message": "请先配置DeepSeek API Key"}), 400

    from app.doc_processor import ai_extract_construction_text
    try:
        extracted = ai_extract_construction_text(text, api_key)
        if not extracted or len(extracted.strip()) < 20:
            extracted = text  # fallback to original
        return jsonify({"code": 0, "data": {"text": extracted}})
    except Exception as e:
        return jsonify({"code": 500, "message": "提取失败: " + str(e)[:200]}), 500