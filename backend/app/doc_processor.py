"""
文档处理模块 - PDF/DOCX/TXT 解析流水线 v2
支持：文本提取、智能清洗、AI建设内容提取、AI功能点标注
"""
import os, re, json, base64, traceback, urllib.request, urllib.error
from typing import Optional, List

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

# ── PDF文本提取 ──────────────────────────────────────────

def extract_text_from_pdf(filepath: str) -> str:
    """使用 PyMuPDF 提取PDF文本（最快），失败则回退 pdfminer/pypdf"""
    text = ""
    try:
        import fitz
        doc = fitz.open(filepath)
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        if _has_meaningful_content(text):
            return text.strip()
    except Exception:
        pass
    try:
        from pdfminer.high_level import extract_text as pm_extract
        from pdfminer.layout import LAParams
        text = pm_extract(filepath, laparams=LAParams())
        if _has_meaningful_content(text):
            return text.strip()
    except Exception:
        pass
    try:
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        text = "\n".join(page.extract_text() or "" for page in reader.pages[:500])
        if _has_meaningful_content(text):
            return text.strip()
    except Exception:
        pass
    return ""


def _has_meaningful_content(text: str, min_chinese: int = 5) -> bool:
    if not text or not text.strip():
        return False
    text = text.strip()
    if len(text) < 20:
        return False
    chinese = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    return chinese >= min_chinese or len(text) > 200


# ── 文档清洗（去噪 + 保留建设内容） ─────────────────────

def _fix_garbled_text(text: str) -> str:
    """修复常见乱码 - 使用字节编码转换"""
    if not text:
        return ""
    # 替换非法控制字符
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # 方法1: 检测Latin-1编码的UTF-8字节并修复
    try:
        # 统计高位字符
        high_chars = sum(1 for c in text if ord(c) >= 0x80)
        chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        if high_chars > len(text) * 0.05 and chinese_chars < 5 and len(text) > 20:
            fixed = text.encode("latin-1", errors="replace").decode("utf-8", errors="replace")
            new_chinese = sum(1 for c in fixed if "\u4e00" <= c <= "\u9fff")
            if new_chinese > chinese_chars and new_chinese > 3:
                text = fixed
    except Exception:
        pass
    # 去掉连续重复符号行
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        s = line.strip()
        if all(c in "=-*_~. #@" for c in s) and len(s) >= 3:
            continue
        cleaned.append(line)
    return "\n".join(cleaned)

def _remove_figures_tables(text: str) -> str:
    """去掉图、表、目录、附录等无关内容"""
    if not text:
        return ""
    lines = text.split("\n")
    result = []
    in_toc = False
    toc_blank = 0
    toc_exit_markers = ["第一章", "第二章", "第三章", "第四章", "第五章",
                        "第1章", "第2章", "第3章", "第4章", "第5章",
                        "第一部分", "第1节", "第一节", "项目概述", "项目背景",
                        "1.", "2.", "3.", "4.", "5."]
    # 表格追踪
    in_table = False

    for line in lines:
        s = line.strip()
        if not s:
            if in_toc:
                toc_blank += 1
                if toc_blank > 3:
                    in_toc = False
            if in_table:
                in_table = False
            continue
        toc_blank = 0

        # 目录检测
        if s in ["目 录", "目录", "目次", "TOC", "Contents", "CONTENTS", "目 次"]:
            in_toc = True
            continue
        if in_toc:
            if any(s.startswith(m) or s.startswith(m.replace(" ", "")) for m in toc_exit_markers):
                in_toc = False
                if len(s) > 3 and not s.isdigit():
                    result.append(s)
                continue
            if "........" in s or "......" in s:
                continue
            if len(s) < 40:
                continue
            in_toc = False

        # 去掉图、表标题
        if re.match(r"^图\s*\d", s) or re.match(r"^表\s*\d", s) or re.match(r"^图表\s*\d", s):
            in_table = True
            continue
        # 去掉附录
        if s.startswith("附录") or (s.startswith("附") and re.search(r"\d", s[:4])):
            in_table = True
            continue
        if s.startswith("附件") or s.startswith("附则") or s.startswith("附表"):
            continue
        if "表" in s[:3] and re.search(r"\d", s[:6]):
            in_table = True
            continue
        # 表格内数据行（纯竖线表格）
        if s.startswith("|") and s.count("|") >= 3:
            in_table = True
            continue
        if in_table:
            if s.count("|") >= 2:
                continue
            if re.match(r"^[\d\s\-\|]+$", s):
                continue
            if re.match(r"^[—\-—━]+$", s):
                continue
            in_table = False

        # 去掉分隔线
        if re.match(r"^[—\-=*_~━│┃]+$", s):
            continue
        if s.isdigit() and len(s) <= 5:
            continue
        if all(c in "=-*_~.#@ " for c in s) and len(s) >= 3:
            continue
        # 去掉纯符号行
        if all(not (c.isalnum() or ord(c) >= 0x4e00) for c in s) and len(s) > 1:
            continue
        if len(s) < 3 and not re.search(r"[\u4e00-\u9fff]", s):
            continue

        result.append(s)

    # 去重连续行
    final = []
    prev = ""
    for line in result:
        if line != prev:
            final.append(line)
            prev = line
    return "\n".join(final)


def _normalize_numbering(text: str) -> str:
    """规范化编号，去掉无意义的编号层级"""
    if not text:
        return ""
    lines = text.split("\n")
    result = []
    for line in lines:
        s = line.strip()
        # 去掉 "1.1.1.1" 这种很深层的编号前缀
        s = re.sub(r"^(\d+\.)+(\d+\.)*\d*\s*", "", s).strip()
        # 去掉 "（一）" "（1）" 等编号
        s = re.sub(r"^[（(][一二三四五六七八九十\d]+[）)]\s*", "", s).strip()
        # 去掉 "一、" "二、" 等
        s = re.sub(r"^[一二三四五六七八九十]+[、,，]\s*", "", s).strip()
        # 去掉 "第X章" "第X节" 等
        s = re.sub(r"^第[一二三四五六七八九十\d]+[章节条]\s*", "", s).strip()
        if s:
            result.append(s)
        else:
            # 如果只剩空行，保留空行结构
            result.append("")
    return "\n".join(result)


def _keep_construction_content(text: str) -> str:
    """智能保留与建设内容相关的行，去掉无关段落（宽松模式，保留大部分内容）"""
    if not text:
        return ""
    # 与软件造价相关的关键词（宽松匹配）
    relevant_kw = [
        "系统", "功能", "模块", "数据", "接口", "存储", "数据库", "录入",
        "查询", "统计", "报表", "导出", "导入", "上传", "审批", "管理",
        "用户", "权限", "配置", "日志", "监控", "告警", "备份", "恢复",
        "开发", "建设", "运维", "维护", "升级", "改造", "迁移", "部署",
        "测试", "验收", "交付", "需求", "设计", "架构", "平台", "服务",
        "服务器", "网络", "安全", "认证", "授权", "登录", "注册",
        "采集", "处理", "分析", "展示", "检索", "搜索", "筛选",
        "登记", "新增", "创建", "编辑", "删除", "修改", "查看", "浏览",
        "生成", "打印", "输出", "同步", "交换", "共享",
    ]
    # 明确无关的段落关键词
    irrelevant_kw = [
        "免责", "版权", "保密", "承诺", "声明", "第X页", "页码",
        "组织机构", "人员安排", "公司简介", "团队介绍", "资质",
    ]

    lines = text.split("\n")
    result = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        # 包含无关关键词的跳过
        if any(kw in s for kw in irrelevant_kw):
            continue
        # 保留包含中文的行（有中文基本就是正文）
        if re.search(r"[\u4e00-\u9fff]", s):
            result.append(s)
        # 也保留包含相关关键词的纯英文行
        elif any(kw in s for kw in relevant_kw):
            result.append(s)
    return "\n".join(result)


def clean_document(raw_text: str) -> str:
    """完整文档清洗流水线：去噪→去图表→规范化→保留建设内容→去乱码"""
    if not raw_text:
        return ""
    text = _fix_garbled_text(raw_text)
    text = _remove_figures_tables(text)
    text = _normalize_numbering(text)
    text = _keep_construction_content(text)
    # 去掉过长行（可能是二进制残留）
    lines = text.split("\n")
    lines = [l for l in lines if len(l) < 500]
    # 最终清理
    text = "\n".join(lines)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


# ── AI 建设内容提取（DeepSeek） ────────────────────────

AI_EXTRACT_PROMPT = """你是一个文档分析助手。请从以下需求文档中提取与软件系统建设相关的内容。

具体要求：
1. 只保留与系统功能、数据存储、接口对接、业务流程等相关的建设内容
2. 去掉项目背景、政策法规、编制依据、组织机构、人员安排、免责声明等无关内容
3. 去掉图、表、目录、附录等结构元素
4. 保持原文段落顺序
5. 直接输出提取后的文本，不要添加额外说明"""


def ai_extract_construction_text(text: str, api_key: str) -> str:
    """用 DeepSeek 提取文档中的核心建设内容"""
    if not api_key or not text or len(text.strip()) < 30:
        return text

    try:
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": AI_EXTRACT_PROMPT},
                {"role": "user", "content": text[:60000]}
            ],
            "temperature": 0.05,
            "max_tokens": 8192,
        }
        req_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            DEEPSEEK_API_URL, data=req_body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        )
        resp = urllib.request.urlopen(req, timeout=120)
        result = json.loads(resp.read().decode("utf-8"))
        extracted = result["choices"][0]["message"]["content"]
        if extracted and len(extracted.strip()) > 20:
            return extracted.strip()
    except Exception:
        pass
    return text


# ── AI 功能点标注（DeepSeek） ──────────────────────────

FP_ANALYZE_PROMPT = """你是一位专业的软件造价评估师，精通BSCEA标准。
从以下需求文档中识别功能点，返回JSON格式列表。

每个功能点包含以下字段：
- category: 类别 ILF/EIF/EI/EO/EQ
- description: 功能描述（20字左右）
- fp_name: 功能点名称（10字左右）
- keyword: 原文中匹配的关键词（用于高亮）
- subsystem: 所属子系统名称（从文档章节标题推断）
- module_l1: 所属一级模块名称（从文档内容推断）

返回格式：{"items": [{"category": "ILF", "description": "描述", "fp_name": "名称", "keyword": "关键词", "subsystem": "子系统", "module_l1": "一级模块"}, ...]}

分类说明：
- ILF：内部逻辑文件，系统内部维护的数据存储
- EIF：外部接口文件，被本系统引用但由其他系统维护的数据
- EI：外部输入，数据录入、导入等输入操作
- EO：外部输出，报表生成、导出等输出操作
- EQ：外部查询，数据查询、检索等查询操作

注意UFP权重：ILF=35, EIF=15, EI=4, EO=5, EQ=4"""


def ai_analyze_fp_with_highlights(text: str, api_key: str, fp_method: str = "estimated") -> dict:
    """用DeepSeek分析功能点，返回带原文高亮关键词的功能点列表"""
    if not api_key or not text or len(text.strip()) < 20:
        return {"items": [], "highlight_map": {}}

    fp_instruction = "只需要识别ILF和EIF两类。" if fp_method == "estimated" else "需要识别ILF、EIF、EI、EO、EQ全部五类。"

    try:
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": FP_ANALYZE_PROMPT + "\n\n" + fp_instruction},
                {"role": "user", "content": f"文档内容：\n\n{text[:60000]}"}
            ],
            "temperature": 0.05,
            "max_tokens": 8192,
        }
        req_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            DEEPSEEK_API_URL, data=req_body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        )
        resp = urllib.request.urlopen(req, timeout=180)
        result = json.loads(resp.read().decode("utf-8"))
        ai_text = result["choices"][0]["message"]["content"]

        items = _parse_fp_json(ai_text)
        highlight_map = _build_highlight_map(items)
        return {"items": items, "highlight_map": highlight_map}
    except Exception as e:
        raise Exception(f"AI功能点分析失败: {str(e)[:200]}")


def _parse_fp_json(ai_text: str) -> list:
    """解析AI返回的JSON功能点列表"""
    json_match = re.search(r"\{.*\}", ai_text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            items = data.get("items", []) if isinstance(data, dict) else data
            return _normalize_items(items)
        except json.JSONDecodeError:
            pass
    list_match = re.search(r"\[.*\]", ai_text, re.DOTALL)
    if list_match:
        try:
            items = json.loads(list_match.group())
            return _normalize_items(items) if isinstance(items, list) else []
        except json.JSONDecodeError:
            pass
    return []


def _normalize_items(items: list) -> list:
    """标准化功能点列表"""
    WEIGHTS = {"ILF": 35, "EIF": 15, "EI": 4, "EO": 5, "EQ": 4}
    results = []
    for item in items:
        if not isinstance(item, dict) or not item.get("category"):
            continue
        cat = item["category"].upper().strip()
        if cat in WEIGHTS:
            results.append({
                "category": cat,
                "description": (item.get("description") or item.get("desc") or "")[:100],
                "fp_name": (item.get("fp_name") or item.get("name") or "")[:40],
                "keyword": item.get("keyword", "")[:30],
                "ufp": WEIGHTS[cat],
                "subsystem": (item.get("subsystem") or item.get("module") or "系统")[:20],
                "module_l1": (item.get("module_l1") or item.get("sub_module") or "数据管理")[:20],
                "complexity": "medium", "reuse_level": "low", "modify_type": "new",
            })
    return results


def _build_highlight_map(items: list) -> dict:
    """构建{类型: [关键词列表]}的高亮映射"""
    mapping = {}
    for item in items:
        cat = item["category"]
        kw = item.get("keyword", "").strip()
        if kw and len(kw) >= 2 and len(kw) <= 20:
            mapping.setdefault(cat, set()).add(kw)
    return {k: list(v) for k, v in mapping.items()}


# ── 完整文档处理流水线 ──────────────────────────────────

def process_document(filepath: str, api_key: str = "", fp_method: str = "estimated") -> dict:
    """完整的文档处理流水线"""
    ext = filepath.rsplit(".", 1)[-1].lower() if "." in filepath else ""
    raw_text = ""
    is_scanned = False

    try:
        if ext in ("txt",):
            with open(filepath, "rb") as f:
                raw_bytes = f.read()
            enc = "utf-8"
            try:
                import charset_normalizer
                r = charset_normalizer.detect(raw_bytes)
                if isinstance(r, dict):
                    enc = r.get("encoding", "utf-8") or "utf-8"
            except Exception:
                pass
            raw_text = raw_bytes.decode(enc, errors="replace")
            if raw_text and raw_text[0] == "\ufeff":
                raw_text = raw_text[1:]
        elif ext == "docx":
            from docx import Document
            doc = Document(filepath)
            raw_text = "\n".join(p.text for p in doc.paragraphs)
        elif ext == "doc":
            try:
                import olefile
                ole = olefile.OleFileIO(filepath)
                if ole.exists("WordDocument"):
                    stream = ole.openstream("WordDocument")
                    data = stream.read()
                    try:
                        decoded = data.decode("utf-16-le", errors="replace")
                        raw_text = "".join(c for c in decoded if c.isprintable() or c in "\n\r\t")
                    except Exception:
                        pass
                ole.close()
            except Exception:
                pass
            if not raw_text or len(raw_text.strip()) < 20:
                raw_text = "【旧版.doc格式暂不支持自动解析】\n请将文档另存为.docx或.txt后重新上传。"
        elif ext == "pdf":
            raw_text = extract_text_from_pdf(filepath)
            if not raw_text or not _has_meaningful_content(raw_text):
                is_scanned = True
                raw_text = "【该文档为扫描件或图片型PDF，无法自动提取文字】\n请使用文字版PDF或DOCX文档重新上传。"
    except Exception as e:
        traceback.print_exc()
        raw_text = f"(文档解析失败: {str(e)[:100]})"

    # 第一步清洗（本地规则）
    cleaned_text = clean_document(raw_text) if isinstance(raw_text, str) else ""

    # 第二步清洗（AI提取建设内容）
    if api_key and cleaned_text and len(cleaned_text.strip()) > 50 and not is_scanned:
        try:
            ai_text = ai_extract_construction_text(cleaned_text, api_key)
            if ai_text and len(ai_text.strip()) > 20:
                cleaned_text = ai_text
        except Exception:
            pass

    # 分析项目信息
    result = _analyze_text_info(cleaned_text)
    result["text_content"] = cleaned_text[:500000]
    result["is_scanned"] = is_scanned
    result["ocr_used"] = False

    # 功能点提取（先用关键词）
    fp_items = []
    try:
        from app.fp_generator import extract_fp_candidates
        fp_items = extract_fp_candidates(cleaned_text, fp_method)
    except Exception:
        fp_items = []
    result["fp_items"] = fp_items

    # 缓存PDF文本
    if ext == "pdf" and cleaned_text and len(cleaned_text) > 100:
        try:
            with open(filepath + "_text.txt", "w", encoding="utf-8") as f:
                f.write(cleaned_text)
        except Exception:
            pass

    return result


def _analyze_text_info(text: str) -> dict:
    """从文本中分析项目名称"""
    if not text:
        return {"project_name": "", "estimate_type": "dev"}
    lines = text.split("\n")
    project_name = ""
    estimate_type = "dev"
    for line in lines[:30]:
        s = line.strip()
        if any(kw in s for kw in ["项目名称", "项目名", "项目编号", "工程名称"]):
            parts = re.split(r"[：:]", s)
            if len(parts) > 1:
                name = parts[-1].strip()
                if name and len(name) > 1:
                    project_name = name
                    break
    if not project_name and len(lines) > 2:
        for line in lines[1:6]:
            s = line.strip()
            if len(s) > 4 and len(s) < 100 and re.search(r"[\u4e00-\u9fff]", s):
                project_name = s[:40]
                break
    dev_kw = ["开发", "新建", "研发", "建设", "平台"]
    ops_kw = ["运维", "维护", "运营", "运行"]
    dev_score = sum(1 for kw in dev_kw for l in lines[:80] if kw in l)
    ops_score = sum(1 for kw in ops_kw for l in lines[:80] if kw in l)
    if ops_score > dev_score:
        estimate_type = "ops"
    if project_name:
        project_name = project_name.rstrip(".").rstrip("建设方案").rstrip("设计方案").rstrip("技术方案").strip() + "造价评估报告"
    return {"project_name": project_name, "estimate_type": estimate_type}