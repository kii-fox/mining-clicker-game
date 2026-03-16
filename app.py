from flask import Flask, request, jsonify, session, render_template, redirect
import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.security import generate_password_hash, check_password_hash
import random
from datetime import datetime
import os
import json


app = Flask(__name__)
app.secret_key = "secret-key-change-this"

# -------------------------
# Firebase 初期化
# -------------------------

if os.getenv("FIREBASE_KEY"):
    # Renderなどクラウド環境
    firebase_key = json.loads(os.environ["FIREBASE_KEY"])
    cred = credentials.Certificate(firebase_key)
else:
    # ローカル環境
    cred = credentials.Certificate(
        "mining-clicker-79aa7-firebase-adminsdk-fbsvc-c340d8fc74.json"
    )

firebase_admin.initialize_app(cred)

db = firestore.client()
# -------------------------
# UID生成（6桁）
# -------------------------

def generate_uid():

    while True:

        uid = str(random.randint(100000, 999999))

        if not db.collection("users").document(uid).get().exists:
            return uid


# -------------------------
# ページ
# -------------------------

@app.route("/")
def login_page():
    return render_template("index.html")


@app.route("/game")
def game_page():

    if "uid" not in session:
        return redirect("/")

    return render_template("game.html")


# -------------------------
# 自分情報
# -------------------------

@app.route("/me")
def me():

    uid = session.get("uid")

    if not uid:
        return jsonify({"error": "not login"}), 401

    return jsonify({"uid": uid})


# -------------------------
# register
# -------------------------

@app.route("/register", methods=["POST"])
def register():

    data = request.json
    password = data.get("password")

    if not password:
        return jsonify({"error": "Password required"}), 400

    uid = generate_uid()

    password_hash = generate_password_hash(password)

    user_ref = db.collection("users").document(uid)

    user_ref.set({
        "password_hash": password_hash,
        "is_logged_in": False,
        "created_at": datetime.utcnow()
    })

    # -------------------------
    # 初期素材
    # -------------------------

    user_ref.collection("materials").document("data").set({
        "stone": 0,
        "coal": 0
    })

    # -------------------------
    # 初期ツール
    # -------------------------

    tool_master = db.collection("tool_master").document("wood_pickaxe").get().to_dict()

    max_durability = tool_master["max_durability"]

    user_ref.collection("tools").add({
        "tool_type": "wood_pickaxe",
        "durability": max_durability,
        "max_durability": max_durability,
        "is_equipped": True
    })

    return jsonify({"uid": uid})

# -------------------------
# login
# -------------------------

@app.route("/login", methods=["POST"])
def login():

    data = request.json

    uid = data.get("uid")
    password = data.get("password")

    user_ref = db.collection("users").document(uid)

    user = user_ref.get()

    if not user.exists:
        return jsonify({"error": "User not found"}), 404

    user_data = user.to_dict()

    if user_data["is_logged_in"]:
        return jsonify({"error": "Already logged in elsewhere"}), 403

    if not check_password_hash(user_data["password_hash"], password):
        return jsonify({"error": "Invalid password"}), 401

    session["uid"] = uid

    user_ref.update({
        "is_logged_in": True
    })

    return jsonify({"message": "Login successful"})


# -------------------------
# logout
# -------------------------

@app.route("/logout", methods=["POST"])
def logout():

    uid = session.get("uid")

    if not uid:
        return jsonify({"error": "Not logged in"}), 401

    db.collection("users").document(uid).update({
        "is_logged_in": False
    })

    session.pop("uid")

    return jsonify({"message": "Logged out"})


# -------------------------
# materials
# -------------------------

@app.route("/materials")
def get_materials():

    uid = session.get("uid")

    if not uid:
        return jsonify({"error": "Not logged in"}), 401

    ref = db.collection("users").document(uid).collection("materials").document("data")

    data = ref.get().to_dict()

    return jsonify(data)

# -------------------------
# tools list
# -------------------------

@app.route("/tools")
def tools():

    uid = session.get("uid")

    if not uid:
        return jsonify({"error": "Not logged in"}), 401

    user_ref = db.collection("users").document(uid)

    tools = []

    for doc in user_ref.collection("tools").stream():

        tool = doc.to_dict()

        tool_master = db.collection("tool_master").document(
            tool["tool_type"]
        ).get().to_dict()

        tools.append({

            "id": doc.id,

            "tool_type": tool["tool_type"],

            "name": tool_master["name"],

            "durability": tool["durability"],

            "max_durability": tool["max_durability"],

            "is_equipped": tool["is_equipped"]

        })

    return jsonify(tools)

# -------------------------
# equip
# -------------------------
@app.route("/tools/equip", methods=["POST"])
def equip_tool():

    uid = session.get("uid")

    tool_id = request.json.get("tool_id")

    tools_ref = db.collection("users").document(uid).collection("tools")

    # 全装備解除
    for doc in tools_ref.stream():
        doc.reference.update({"is_equipped": False})

    # 装備
    tools_ref.document(tool_id).update({
        "is_equipped": True
    })

    return jsonify({"message":"equipped"})
# -------------------------
# craft
# -------------------------

@app.route("/tools/craft", methods=["POST"])
def craft_tool():

    uid = session.get("uid")

    if not uid:
        return jsonify({"error": "Not logged in"}), 401

    data = request.json
    tool_type = data.get("tool_type")

    if not tool_type:
        return jsonify({"error": "tool_type required"}), 400

    # -------------------------
    # tool_master取得
    # -------------------------

    tool_master_ref = db.collection("tool_master").document(tool_type)
    tool_master_doc = tool_master_ref.get()

    if not tool_master_doc.exists:
        return jsonify({"error": "Tool not found"}), 404

    tool_master = tool_master_doc.to_dict()

    user_ref = db.collection("users").document(uid)

    # -------------------------
    # 研究チェック
    # -------------------------

    research_required = tool_master.get("research_required")

    if research_required is not None:

        research_doc = user_ref.collection("research").document(
            research_required
        ).get()

        if not research_doc.exists:
            return jsonify({
                "error": "Research required"
            }), 400

    # -------------------------
    # 素材取得
    # -------------------------

    craft_cost = tool_master.get("craft_cost", {})

    mat_ref = user_ref.collection("materials").document("data")
    mat_doc = mat_ref.get()

    mats = mat_doc.to_dict() if mat_doc.exists else {}

    # -------------------------
    # 素材チェック
    # -------------------------

    for material, cost in craft_cost.items():

        if mats.get(material, 0) < cost:
            return jsonify({
                "error": f"Not enough {material}"
            }), 400

    # -------------------------
    # 素材消費
    # -------------------------

    for material, cost in craft_cost.items():
        mats[material] -= cost

    mat_ref.set(mats)

    # -------------------------
    # ツール作成
    # -------------------------

    max_durability = tool_master.get("max_durability", 10)

    user_ref.collection("tools").add({

        "tool_type": tool_type,

        "durability": max_durability,

        "max_durability": max_durability,

        "is_equipped": False

    })

    return jsonify({
        "message": "Craft success"
    })

# -------------------------
# craftable tools
# -------------------------

@app.route("/craftable_tools")
def craftable_tools():

    uid = session.get("uid")

    if not uid:
        return jsonify([])

    user_ref = db.collection("users").document(uid)

    research = {
        doc.id for doc in user_ref.collection("research").stream()
    }

    tools = []

    for doc in db.collection("tool_master").stream():

        tool = doc.to_dict()

        research_required = tool.get("research_required")

        if research_required and research_required not in research:
            continue

        tools.append({
            "tool_type": doc.id,
            "name": tool["name"],
            "craft_cost": tool.get("craft_cost", {})
        })

    return jsonify(tools)
# -------------------------
# mine
# -------------------------

@app.route("/mine", methods=["POST"])
def mine():

    uid = session.get("uid")

    if not uid:
        return jsonify({"error": "Not logged in"}), 401

    user_ref = db.collection("users").document(uid)

    # -------------------------
    # 装備取得
    # -------------------------

    equipped = None
    equipped_doc = None

    for doc in user_ref.collection("tools").stream():

        tool = doc.to_dict()

        if tool.get("is_equipped"):
            equipped = tool
            equipped_doc = doc
            break

    if not equipped:
        return jsonify({"error": "No tool equipped"}), 400

    tool_master = db.collection("tool_master").document(
        equipped["tool_type"]
    ).get().to_dict()

    durability_cost = tool_master["effect"]["durability_cost_per_mine"]
    bonus_drop = tool_master["effect"].get("bonus_drop_rate", 0)

    # -------------------------
    # 耐久消費
    # -------------------------

    equipped["durability"] -= durability_cost

    if equipped["durability"] <= 0:

        # ツール破壊
        equipped_doc.reference.delete()

    else:

        equipped_doc.reference.update({
            "durability": equipped["durability"]
        })

    # -------------------------
    # 素材抽選
    # -------------------------

    RARITY_LEVEL = {
        "common": 1,
        "uncommon": 2,
        "rare": 3,
        "epic": 4,
        "legendary": 5
    }

    material_list = []
    total_weight = 0

    for doc in db.collection("material_master").stream():

        m = doc.to_dict()

        weight = float(m.get("base_drop_weight", 1))

        rarity_name = m.get("rarity", "common")
        rarity = RARITY_LEVEL.get(rarity_name, 1)

        # レア素材補正
        if rarity >= 3:
            weight *= (1 + bonus_drop)

        material_list.append((doc.id, weight))

        total_weight += weight

    if total_weight == 0:
        return jsonify({"error": "Material master empty"}), 500

    # -------------------------
    # 重み抽選
    # -------------------------

    r = random.uniform(0, total_weight)

    upto = 0
    selected = None

    for name, weight in material_list:

        if upto + weight >= r:
            selected = name
            break

        upto += weight

    if not selected:
        return jsonify({"error": "Material roll failed"}), 500

    # -------------------------
    # 素材追加
    # -------------------------

    mat_ref = user_ref.collection("materials").document("data")

    mat_doc = mat_ref.get()

    if mat_doc.exists:
        mats = mat_doc.to_dict()
    else:
        mats = {}

    mats[selected] = mats.get(selected, 0) + 1

    mat_ref.set(mats)

    return jsonify({
        "material": selected
    })
# -------------------------
# research
# -------------------------

@app.route("/research", methods=["POST"])
def research():

    uid = session.get("uid")

    if not uid:
        return jsonify({"error": "Not logged in"}), 401

    data = request.json
    research_id = data.get("research_id")

    if not research_id:
        return jsonify({"error": "research_id required"}), 400

    user_ref = db.collection("users").document(uid)

    # 研究済みチェック
    research_ref = user_ref.collection("research").document(research_id)

    if research_ref.get().exists:
        return jsonify({"error": "Already researched"}), 400

    # マスター取得
    master_ref = db.collection("research_master").document(research_id)

    master_doc = master_ref.get()

    if not master_doc.exists:
        return jsonify({"error": "Research not found"}), 404

    master = master_doc.to_dict()

    cost = master.get("cost", {})

    # 素材取得
    mat_ref = user_ref.collection("materials").document("data")

    mats = mat_ref.get().to_dict()

    # 素材チェック
    for m, c in cost.items():
        if mats.get(m, 0) < c:
            return jsonify({"error": f"Not enough {m}"}), 400

    # 素材消費
    for m, c in cost.items():
        mats[m] -= c

    mat_ref.set(mats)

    # 研究完了
    research_ref.set({
        "unlocked": True
    })

    return jsonify({
        "message": "Research complete"
    })
# -------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)