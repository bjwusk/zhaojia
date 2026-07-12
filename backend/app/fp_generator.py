import re
from flask import Blueprint, request, jsonify

fp_gen_bp = Blueprint("fp_gen", __name__)

FP_PATTERNS = {
    "ILF": {
        "keywords": ["数据表", "数据库", "存储", "档案", "文件", "信息库", "仓库", "数据仓库", "数据湖", "数据库表", "数据存储", "数据实体", "数据模型", "数据对象", "实体", "持久化", "保存"],
        "weight": 35
    },
    "EIF": {
        "keywords": ["接口", "对接", "外部系统", "外部接口", "数据接口", "API", "接口调用", "数据交换", "数据共享", "第三方", "外部数据", "数据同步"],
        "weight": 15
    },
    "EI": {
        "keywords": ["录入", "登记", "注册", "采集", "新增", "创建", "添加", "上传", "导入", "提交", "发送", "输入", "录入信息", "数据录入", "数据新增", "登记信息", "信息录入"],
        "weight": 4
    },
    "EO": {
        "keywords": ["导出", "输出", "报表", "报告", "打印", "统计", "汇总", "生成", "展示", "显示", "输出报表", "数据导出", "生成报告", "统计分析", "统计报表"],
        "weight": 5
    },
    "EQ": {
        "keywords": ["查询", "检索", "搜索", "查看", "浏览", "列表", "查阅", "筛选", "过滤", "查找", "查询信息", "数据查询", "条件查询", "模糊查询", "组合查询", "信息查询"],
        "weight": 4
    },
}

def extract_fp_candidates(text, fp_method="estimated"):
    """从文本中提取功能点候选"""
    if not text:
        return []
    active = ["ILF", "EIF"] if fp_method == "estimated" else ["ILF", "EIF", "EI", "EO", "EQ"]
    lines = text.split("\n")
    results = []
    seen_descs = set()
    for line in lines:
        s = line.strip()
        if not s or len(s) < 4:
            continue
        for fp_type in active:
            for kw in FP_PATTERNS[fp_type]["keywords"]:
                if kw in s:
                    desc_key = s[:40]
                    if desc_key in seen_descs:
                        continue
                    seen_descs.add(desc_key)
                    results.append({
                        "category": fp_type,
                        "description": s[:100],
                        "fp_name": kw,
                        "ufp": FP_PATTERNS[fp_type]["weight"],
                        "subsystem": "",
                        "module_l1": "",
                        "complexity": "medium",
                        "reuse_level": "low",
                        "modify_type": "new",
                    })
                    break
    if len(results) < 2:
        results = _generate_default_fps(text, fp_method)
    return results


def _generate_default_fps(text, fp_method):
    """当关键词匹配不足时，生成默认功能点"""
    results = []
    has_storage = any(kw in text for kw in ["数据", "存储", "数据库", "文件", "档案", "信息"])
    has_interface = any(kw in text for kw in ["接口", "对接", "外部", "共享", "交换"])
    has_input = any(kw in text for kw in ["录入", "登记", "新增", "创建", "采集"])
    has_output = any(kw in text for kw in ["报表", "导出", "统计", "报告", "打印"])
    has_query = any(kw in text for kw in ["查询", "检索", "搜索", "查看"])

    if has_storage:
        results.append({"category": "ILF", "description": "数据存储管理", "fp_name": "数据存储", "ufp": 35,
                        "subsystem": "", "module_l1": "数据管理", "complexity": "medium",
                        "reuse_level": "low", "modify_type": "new"})
    if has_interface:
        results.append({"category": "EIF", "description": "外部系统接口对接", "fp_name": "外部接口", "ufp": 15,
                        "subsystem": "", "module_l1": "接口管理", "complexity": "medium",
                        "reuse_level": "low", "modify_type": "new"})
    if fp_method == "detailed":
        if has_input:
            results.append({"category": "EI", "description": "数据录入功能", "fp_name": "数据录入", "ufp": 4,
                            "subsystem": "", "module_l1": "数据采集", "complexity": "medium",
                            "reuse_level": "low", "modify_type": "new"})
        if has_output:
            results.append({"category": "EO", "description": "数据输出功能", "fp_name": "数据输出", "ufp": 5,
                            "subsystem": "", "module_l1": "数据展示", "complexity": "medium",
                            "reuse_level": "low", "modify_type": "new"})
        if has_query:
            results.append({"category": "EQ", "description": "数据查询功能", "fp_name": "数据查询", "ufp": 4,
                            "subsystem": "", "module_l1": "查询检索", "complexity": "medium",
                            "reuse_level": "low", "modify_type": "new"})
    if not results:
        results.append({"category": "ILF", "description": "系统数据管理", "fp_name": "数据管理", "ufp": 35,
                        "subsystem": "", "module_l1": "系统管理", "complexity": "medium",
                        "reuse_level": "low", "modify_type": "new"})
    return results


@fp_gen_bp.route("/generate", methods=["POST"])
def generate_fps():
    data = request.get_json()
    text = data.get("text", "")
    fp_method = data.get("fp_method", "estimated")
    if not text:
        return jsonify({"code": 400, "message": "请提供文档内容"}), 400
    fps = extract_fp_candidates(text, fp_method)
    return jsonify({"code": 0, "data": {"items": fps, "total": len(fps)}})
