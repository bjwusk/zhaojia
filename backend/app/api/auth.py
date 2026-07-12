import hashlib
from flask import Blueprint, request, jsonify
from app import db
from app.models.user import User

auth_bp = Blueprint("auth", __name__)

def hash_pw(pw):
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"code": 400, "message": "用户名和密码为必填项"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"code": 409, "message": "用户名已存在"}), 409
    user = User(username=username, password=hash_pw(password), display_name=data.get("display_name", username))
    user.company = data.get("company", "")
    user.cert_no = data.get("cert_no", "")
    db.session.add(user)
    db.session.commit()
    return jsonify({"code": 0, "data": user.to_dict(), "message": "注册成功"}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    user = User.query.filter_by(username=data.get("username", ""), password=hash_pw(data.get("password", ""))).first()
    if not user:
        return jsonify({"code": 401, "message": "用户名或密码错误"}), 401
    return jsonify({"code": 0, "data": user.to_dict(), "token": user.username + "_" + str(user.id)})

@auth_bp.route("/profile", methods=["GET"])
def get_profile():
    uid = request.args.get("uid")
    user = User.query.get(uid) if uid else User.query.first()
    if not user:
        return jsonify({"code": 404, "message": "用户不存在"}), 404
    return jsonify({"code": 0, "data": user.to_dict()})

@auth_bp.route("/profile", methods=["PUT"])
def update_profile():
    data = request.get_json() or {}
    uid = data.get("id")
    user = User.query.get(uid)
    if not user:
        return jsonify({"code": 404, "message": "用户不存在"}), 404
    for key in ["display_name", "company", "cert_no"]:
        if key in data:
            setattr(user, key, data[key])
    if data.get("password"):
        user.password = hash_pw(data["password"])
    db.session.commit()
    return jsonify({"code": 0, "data": user.to_dict(), "message": "更新成功"})
