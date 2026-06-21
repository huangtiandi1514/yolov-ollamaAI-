import os
import json
import datetime
import tempfile
import shutil
import cv2
import re
import traceback
import io
import numpy as np
from PIL import Image
import torch
from ultralytics import YOLO
import whisper
import edge_tts
import requests
import matplotlib.pyplot as plt
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# ===================== 全局配置 =====================
# YOLO模型路径（按你实际路径修改）
MODEL_PATH = r"E:/ultralytics-8.3.33/runs/detect/数据2.0版/定量分析/模型增强前后的性能对比/new_train_static_enforce/weights/best.pt"
DATA_YAML = "./data.yaml"
RECORD_FILE = "./detect_records.json"
FAVORITE_FILE = "./favorite_schemes.json"
TASK_LOG_FILE = "./task_logs.json"

# Ollama 配置
OLLAMA_API = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:3b"
OLLAMA_TIMEOUT = 60

# Matplotlib全局配置：解决中文乱码
plt.rcParams["font.sans-serif"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False

# 自动判断设备
DEVICE = "0" if torch.cuda.is_available() else "cpu"

# 临时文件目录
TEMP_DIR = "./temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

# 语音静态文件目录（可直接HTTP访问）
AUDIO_STATIC_DIR = os.path.join("static", "audio")
os.makedirs(AUDIO_STATIC_DIR, exist_ok=True)

# ===================== 模型全局加载 =====================
print("正在加载 YOLO 玉米病害检测模型...")
yolo_model = None
try:
    if not os.path.exists(MODEL_PATH):
        print(f"❌ 模型文件不存在: {MODEL_PATH}")
    else:
        yolo_model = YOLO(MODEL_PATH)
        print("✅ YOLO 模型加载成功")
except Exception as e:
    print(f"❌ YOLO 模型加载失败: {e}")
    traceback.print_exc()

print("正在加载 Whisper 语音识别模型(base)...")
speech_model = whisper.load_model("base")
print("✅ Whisper 语音模型加载完成")


# ===================== 工具函数 =====================
def clean_value(val):
    if isinstance(val, (np.integer, np.int64, np.int32)):
        return int(val)
    if isinstance(val, (np.floating, np.float64, np.float32)):
        return float(val)
    return val


def clean_tts_text(text):
    if not text:
        return ""
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*{1,3}', '', text)
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'`{1,3}', '', text)
    text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002500-\U00002BEF"
        u"\U00002702-\U000027B0"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642"
        u"\u2600-\u2B55"
        u"\u200d"
        u"\ufe0f"
        u"\u3030"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)
    text = re.sub(r'\n+', '，', text)
    text = re.sub(r'，{2,}', '。', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()


def create_disease_chart(counts):
    if not counts:
        return None
    names = list(counts.keys())
    values = list(counts.values())
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(names, values, color="#4CAF50")
    ax.set_title("玉米病害数量统计", fontsize=14)
    ax.set_ylabel("检出数量", fontsize=12)
    plt.xticks(rotation=20)
    plt.tight_layout()
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., height,
                f"{height}", ha="center", va="bottom")
    return fig


def add_task_log(task_type, info):
    logs = []
    if os.path.exists(TASK_LOG_FILE):
        with open(TASK_LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
    logs.insert(0, {
        "task_time": str(datetime.datetime.now()),
        "task_type": task_type,
        "info": info
    })
    with open(TASK_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def save_record(img_name, detect_summary, report_text):
    records = []
    if os.path.exists(RECORD_FILE):
        with open(RECORD_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)
    new_item = {
        "time": str(datetime.datetime.now()),
        "img_name": img_name,
        "summary": detect_summary,
        "report": report_text
    }
    records.insert(0, new_item)
    with open(RECORD_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


# ===================== Flask 初始化 =====================
app = Flask(__name__)
CORS(app)  # 全局开启跨域


# ===================== 接口1：单图病害检测 =====================
@app.route("/api/detect", methods=["POST"])
def detect_disease():
    if yolo_model is None:
        return jsonify({"code": 500, "msg": "YOLO 模型未加载"}), 500

    if "image" not in request.files:
        return jsonify({"code": 400, "msg": "未上传图片"}), 400

    file = request.files["image"]
    conf = float(request.form.get("conf", 0.25))
    img_name = file.filename

    temp_path = os.path.join(TEMP_DIR, f"detect_{datetime.datetime.now().timestamp()}.jpg")
    file.save(temp_path)

    try:
        results = yolo_model.predict(source=temp_path, conf=conf, imgsz=640, device=DEVICE)
        res = results[0]

        counts = {}
        detect_text = ""
        total_disease = 0
        if len(res.boxes) == 0:
            detect_text = "未检测到玉米病害，植株状态正常。"
            level = "正常"
            risk = 0
        else:
            for box in res.boxes:
                cls_name = res.names[int(box.cls[0])]
                counts[cls_name] = counts.get(cls_name, 0) + 1
                total_disease += 1
            for cls_name, count in counts.items():
                detect_text += f"检测到【{cls_name}】: {count} 处\n"

            if total_disease <= 2:
                level = "轻度"
                risk = 30
            elif total_disease <= 5:
                level = "中度"
                risk = 60
            else:
                level = "重度"
                risk = 90

        # 调用 Ollama 生成诊断报告
        system_prompt = "你是国家级玉米种植与植物病理学专家，精通玉米各类病害识别、成因分析、危害评估、防治方案。必须根据检测结果给出专业可落地诊断报告。"
        user_prompt = f"玉米病害检测结果如下：\n{detect_text}\n\n生成完整诊断报告，包含：病害确诊、发生程度、发病诱因、产量危害、全套防治方案。"

        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {"temperature": 0.5, "top_p": 0.9, "num_predict": 1500}
        }

        ai_report = ""
        try:
            resp = requests.post(OLLAMA_API, json=payload, timeout=OLLAMA_TIMEOUT)
            ai_report = resp.json()["message"]["content"]
        except Exception as e:
            ai_report = f"AI 诊断生成失败：{str(e)}"

        save_record(img_name, detect_text, ai_report)
        add_task_log("单图检测", f"图片：{img_name}，病害等级：{level}")

        return jsonify({
            "code": 200,
            "data": {
                "detect_text": detect_text,
                "counts": counts,
                "level": level,
                "risk": risk,
                "report": ai_report
            }
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"code": 500, "msg": f"检测失败：{str(e)}"}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# ===================== 接口2：获取检测标注图 =====================
@app.route("/api/detect/image", methods=["POST"])
def get_detect_image():
    if yolo_model is None:
        return jsonify({"code": 500, "msg": "模型未加载"}), 500
    if "image" not in request.files:
        return jsonify({"code": 400, "msg": "未上传图片"}), 400

    file = request.files["image"]
    conf = float(request.form.get("conf", 0.25))
    temp_path = os.path.join(TEMP_DIR, f"img_{datetime.datetime.now().timestamp()}.jpg")
    file.save(temp_path)

    try:
        results = yolo_model.predict(source=temp_path, conf=conf, imgsz=640, device=DEVICE)
        res = results[0]
        plot_img = res.plot()
        plot_img = cv2.cvtColor(plot_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(plot_img)
        img_bytes = io.BytesIO()
        pil_img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        return send_file(img_bytes, mimetype="image/jpeg")
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# ===================== 接口3：AI 对话问答 =====================
@app.route("/api/chat", methods=["POST"])
def ai_chat():
    data = request.get_json()
    user_input = data.get("message", "")
    history = data.get("history", [])

    if not user_input:
        return jsonify({"code": 400, "msg": "输入不能为空"}), 400

    messages = [
        {"role": "system",
         "content": "你是玉米病害农业专家，用户可咨询玉米种植、各类病害识别、防治、田间管理问题，回答简洁专业。"}
    ]
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.6, "num_predict": 1000}
    }

    try:
        resp = requests.post(OLLAMA_API, json=payload, timeout=OLLAMA_TIMEOUT)
        reply = resp.json()["message"]["content"]
        add_task_log("AI 对话", f"用户提问：{user_input[:50]}")
        return jsonify({"code": 200, "data": {"reply": reply}})
    except Exception as e:
        return jsonify({"code": 500, "msg": f"请求失败：{str(e)}"}), 500


# ===================== 接口4：语音转文字 =====================
@app.route("/api/speech-to-text", methods=["POST"])
def speech2text():
    if "audio" not in request.files:
        return jsonify({"code": 400, "msg": "未上传音频"}), 400

    file = request.files["audio"]
    temp_path = os.path.join(TEMP_DIR, f"audio_{datetime.datetime.now().timestamp()}.mp3")
    file.save(temp_path)

    try:
        result = speech_model.transcribe(temp_path, language="zh", fp16=torch.cuda.is_available())
        text = result["text"].strip()
        return jsonify({"code": 200, "data": {"text": text}})
    except Exception as e:
        return jsonify({"code": 500, "msg": f"识别失败：{str(e)}"}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# ===================== 接口5：文字转语音 =====================
@app.route("/api/text-to-speech", methods=["POST"])
def text2speech():
    data = request.get_json()
    text = data.get("text", "")
    if not text:
        return jsonify({"code": 400, "msg": "文本不能为空"}), 400

    clean_text = clean_tts_text(text)
    filename = f"tts_{int(datetime.datetime.now().timestamp() * 1000)}.mp3"
    save_path = os.path.join(AUDIO_STATIC_DIR, filename)

    try:
        import asyncio
        # Windows系统报错可取消下面注释
        # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        async def generate_tts():
            communicate = edge_tts.Communicate(clean_text, voice="zh-CN-YunyangNeural")
            await communicate.save(save_path)

        asyncio.run(generate_tts())

        audio_url = f"/static/audio/{filename}"
        return jsonify({
            "code": 200,
            "data": {"url": audio_url}
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"code": 500, "msg": f"语音合成失败：{str(e)}"}), 500


# ===================== 接口6：检测记录列表 =====================
@app.route("/api/records", methods=["GET"])
def get_records():
    if not os.path.exists(RECORD_FILE):
        return jsonify({"code": 200, "data": []})
    with open(RECORD_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)
    return jsonify({"code": 200, "data": records})


# ===================== 接口7：收藏方案管理 =====================
@app.route("/api/favorites", methods=["GET"])
def get_favorites():
    if not os.path.exists(FAVORITE_FILE):
        return jsonify({"code": 200, "data": []})
    with open(FAVORITE_FILE, "r", encoding="utf-8") as f:
        favs = json.load(f)
    return jsonify({"code": 200, "data": favs})


@app.route("/api/favorites/add", methods=["POST"])
def add_favorite():
    data = request.get_json()
    title = data.get("title", "")
    content = data.get("content", "")
    if not title or not content:
        return jsonify({"code": 400, "msg": "标题和内容不能为空"}), 400

    favs = []
    if os.path.exists(FAVORITE_FILE):
        with open(FAVORITE_FILE, "r", encoding="utf-8") as f:
            favs = json.load(f)
    favs.append({
        "title": title,
        "content": content,
        "add_time": str(datetime.datetime.now())
    })
    with open(FAVORITE_FILE, "w", encoding="utf-8") as f:
        json.dump(favs, f, ensure_ascii=False, indent=2)
    return jsonify({"code": 200, "msg": "收藏成功"})


@app.route("/api/favorites/delete", methods=["POST"])
def del_favorite():
    data = request.get_json()
    idx = data.get("index", 0)
    if not os.path.exists(FAVORITE_FILE):
        return jsonify({"code": 200, "msg": "成功"})
    with open(FAVORITE_FILE, "r", encoding="utf-8") as f:
        favs = json.load(f)
    if 0 <= idx < len(favs):
        favs.pop(idx)
    with open(FAVORITE_FILE, "w", encoding="utf-8") as f:
        json.dump(favs, f, ensure_ascii=False, indent=2)
    return jsonify({"code": 200, "msg": "删除成功"})


# ===================== 接口8：批量图片检测 =====================
@app.route("/api/batch-detect", methods=["POST"])
def batch_detect():
    if yolo_model is None:
        return jsonify({"code": 500, "msg": "模型未加载"}), 500

    files = request.files.getlist("images")
    conf = float(request.form.get("conf", 0.25))
    if not files:
        return jsonify({"code": 400, "msg": "未上传图片"}), 400

    all_counts = {}
    summary = []

    for file in files:
        temp_path = os.path.join(TEMP_DIR, f"batch_{datetime.datetime.now().timestamp()}_{file.filename}")
        file.save(temp_path)
        try:
            res = yolo_model.predict(source=temp_path, conf=conf, imgsz=640, device=DEVICE)[0]
            cnt = {}
            for box in res.boxes:
                cls_name = res.names[int(box.cls[0])]
                cnt[cls_name] = cnt.get(cls_name, 0) + 1
                all_counts[cls_name] = all_counts.get(cls_name, 0) + 1
            summary.append({"filename": file.filename, "result": cnt})
        except Exception as e:
            summary.append({"filename": file.filename, "error": str(e)})
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    add_task_log("批量检测", f"共 {len(files)} 张图片")
    return jsonify({
        "code": 200,
        "data": {
            "summary": summary,
            "total_counts": all_counts
        }
    })


# ===================== 接口9：模型精度评估 =====================
@app.route("/api/evaluate", methods=["GET"])
def evaluate_model():
    if yolo_model is None:
        return jsonify({"code": 500, "msg": "模型未加载"}), 500
    if not os.path.exists(DATA_YAML):
        return jsonify({"code": 500, "msg": "data.yaml 不存在"}), 500

    try:
        metrics = yolo_model.val(data=DATA_YAML, split="val", batch=1, device=DEVICE)
        map50 = clean_value(metrics.box.map50)
        map_all = clean_value(metrics.box.map)
        add_task_log("模型评估", f"mAP@0.5: {map50:.4f}")
        return jsonify({
            "code": 200,
            "data": {"map50": round(map50, 4), "map50_95": round(map_all, 4)}
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"code": 500, "msg": f"评估失败：{str(e)}"}), 500


# ===================== 启动服务 =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)