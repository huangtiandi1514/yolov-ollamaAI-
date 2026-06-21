import matplotlib.pyplot as plt
import os
import json
import requests
import traceback
import gradio as gr
from ultralytics import YOLO
import numpy as np
import whisper
import asyncio
import edge_tts
from io import BytesIO
from PIL import Image
import torch
import tempfile
import shutil
import cv2
import re  # 新增：用于正则清洗文本

# ===================== 全局配置 =====================
# YOLO模型路径
MODEL_PATH = r"E:/ultralytics-8.3.33/runs/detect/数据2.0版/定量分析/模型增强前后的性能对比/new_train_static_enforce/weights/best.pt"
DATA_YAML = "./data.yaml"

# Ollama 配置
OLLAMA_API = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:3b"
OLLAMA_TIMEOUT = 45

# Matplotlib全局配置：解决中文乱码
plt.rcParams["font.sans-serif"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False

# 自动判断设备
DEVICE = "0" if torch.cuda.is_available() else "cpu"
print(f"推理设备自动选择: {DEVICE}")

# 临时音频文件夹（解决文件占用/找不到文件报错）
TEMP_AUDIO_DIR = "./temp_audio"
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

# ===================== 模型全局加载 =====================
print("正在加载 YOLO 玉米病害检测模型...")
yolo_model = None
try:
    if not os.path.exists(MODEL_PATH):
        print(f"❌ 模型文件不存在: {MODEL_PATH}")
    else:
        yolo_model = YOLO(MODEL_PATH)
        print("✅ YOLO 模型加载成功！")
except Exception as e:
    print(f"❌ YOLO 模型加载失败，请检查路径。错误信息: {e}")
    traceback.print_exc()

print("正在加载 Whisper语音识别模型(base)...")
speech_model = whisper.load_model("base")
print("✅ Whisper语音模型加载完成")


# ===================== 工具函数 =====================
def clean_value(val):
    if isinstance(val, (np.integer, np.int64, np.int32)):
        return int(val)
    if isinstance(val, (np.floating, np.float64, np.float32)):
        return float(val)
    return val


# 【新增】TTS文本净化函数：移除所有Markdown格式和emoji
def clean_tts_text(text):
    """净化Markdown格式文本，只保留纯文本，适配TTS朗读"""
    if not text:
        return ""

    # 1. 移除Markdown标题符号 # ## ###
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    # 2. 移除加粗/斜体符号 * ** ***
    text = re.sub(r'\*{1,3}', '', text)
    # 3. 移除无序列表前缀 - * +
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    # 4. 移除有序列表前缀 1. 2. 3.
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    # 5. 移除行内代码和代码块反引号
    text = re.sub(r'`{1,3}', '', text)
    # 6. 移除分割线 ---
    text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)

    # 7. 移除所有emoji表情符号
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # 表情
        u"\U0001F300-\U0001F5FF"  # 符号/物品
        u"\U0001F680-\U0001F6FF"  # 交通/工具
        u"\U0001F1E0-\U0001F1FF"  # 国旗
        u"\U00002500-\U00002BEF"  # 几何符号
        u"\U00002702-\U000027B0"  # 装饰符号
        u"\U0001f926-\U0001f937"  # 手势
        u"\U00010000-\U0010ffff"  # 扩展字符
        u"\u2640-\u2642"
        u"\u2600-\u2B55"
        u"\u200d"
        u"\ufe0f"
        u"\u3030"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)

    # 8. 合并多余空行和空格，优化朗读断句
    text = re.sub(r'\n+', '，', text)  # 换行换成逗号停顿
    text = re.sub(r'，{2,}', '。', text)  # 多个逗号换成句号
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


# ===================== Ollama AI 请求封装 =====================
def ask_ollama(messages):
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.5,
            "top_p": 0.9,
            "num_predict": 1500
        }
    }
    try:
        response = requests.post(OLLAMA_API, json=payload, timeout=OLLAMA_TIMEOUT)
        response.raise_for_status()
        return response.json()["message"]["content"]
    except requests.exceptions.Timeout:
        return f"⚠️ Ollama 请求超时，请降低提问长度或重启ollama服务"
    except requests.exceptions.ConnectionError:
        return f"⚠️ 无法连接Ollama，请执行 ollama serve 启动本地大模型服务"
    except Exception as e:
        err = str(e)
        traceback.print_exc()
        return f"⚠️ 本地Ollama AI调用失败，错误: {err}"


async def text_to_speech(text):
    """每次生成独立临时音频文件，杜绝文件冲突"""
    tmp_file = tempfile.NamedTemporaryFile(suffix=".mp3", dir=TEMP_AUDIO_DIR, delete=False)
    tmp_path = tmp_file.name
    tmp_file.close()
    communicate = edge_tts.Communicate(text, voice="zh-CN-YunyangNeural")
    await communicate.save(tmp_path)
    return tmp_path


# 【修改】朗读前先净化文本
async def read_diagnosis_text(text):
    if not text or not text.strip():
        return None
    try:
        # 先清洗Markdown格式，再生成语音
        clean_text = clean_tts_text(text)
        audio_path = await text_to_speech(clean_text)
        return audio_path
    except Exception as e:
        print(f"TTS朗读失败: {e}")
        traceback.print_exc()
        return None


# ===================== 图像病害检测主函数 =====================
def detect_image(image, conf=0.25):
    empty_chat = [{"role": "assistant", "content": "请先上传玉米叶片图片进行检测"}]
    empty_msg_state = []
    if yolo_model is None:
        error_msg = "YOLO 模型未成功加载，无法检测，请检查模型路径！"
        return None, None, f"""
        <div style="background:#ffebee;padding:15px;border-radius:12px;text-align:center;">
        <h2>❌ 模型加载失败</h2>
        <h3>{error_msg}</h3>
        </div>
        """, error_msg, empty_chat, empty_msg_state, ""

    if image is None:
        err = "未上传任何图像，请上传玉米叶片图片"
        return None, None, f"""
        <div style="background:#fff8e1;padding:15px;border-radius:12px;text-align:center;">
        <h2>⚠️ {err}</h2>
        </div>
        """, err, empty_chat, empty_msg_state, ""

    try:
        results = yolo_model.predict(source=image, conf=conf, imgsz=640, device=DEVICE)
        res = results[0]
    except Exception as e:
        err_msg = f"图像推理失败：{str(e)}"
        traceback.print_exc()
        return None, None, f"""
        <div style="background:#ffebee;padding:15px;border-radius:12px;text-align:center;">
        <h2>❌ {err_msg}</h2>
        </div>
        """, err_msg, empty_chat, empty_msg_state, ""

    detect_text = ""
    counts = {}
    total_disease = 0

    if len(res.boxes) == 0:
        detect_text += "✅ 未检测到玉米病害，植株状态正常。"
        level = "正常"
        risk = 0
    else:
        for box in res.boxes:
            cls_name = res.names[int(box.cls[0])]
            counts[cls_name] = counts.get(cls_name, 0) + 1
            total_disease += 1
        for cls_name, count in counts.items():
            detect_text += f"🌽 检测到【{cls_name}】: {count} 处\n"

        if total_disease <= 2:
            level = "轻度"
            risk = 30
        elif total_disease <= 5:
            level = "中度"
            risk = 60
        else:
            level = "重度"
            risk = 90

    raw_output_text = f"""
📊 玉米病害检测结果：
{detect_text}
🚨 病害等级：{level}
📈 风险指数：{risk}/100
    """

    if level == "正常":
        risk_card = """
<div style="background:#e8f5e9;padding:15px;border-radius:12px;text-align:center;">
<h2>✅ 植株健康</h2>
<h3>风险指数：0/100</h3>
</div>
        """
    elif level == "轻度":
        risk_card = """
<div style="background:#e8f5e9;padding:15px;border-radius:12px;text-align:center;">
<h2>🟢 轻度风险</h2>
<h3>风险指数：30/100</h3>
</div>
        """
    elif level == "中度":
        risk_card = """
<div style="background:#fff8e1;padding:15px;border-radius:12px;text-align:center;">
<h2>🟡 中度风险</h2>
<h3>风险指数：60/100</h3>
</div>
        """
    else:
        risk_card = """
<div style="background:#ffebee;padding:15px;border-radius:12px;text-align:center;">
<h2>🔴 重度风险</h2>
<h3>风险指数：90/100</h3>
</div>
        """

    system_role = {
        "role": "system",
        "content": "你是国家级玉米种植与植物病理学专家，精通玉米各类病害识别、成因分析、危害评估、防治方案。必须根据检测病害类型、数量给出专业可落地诊断报告。"
    }
    analysis_prompt = (
        f"玉米病害检测结果如下：\n{detect_text}\n\n"
        f"生成【玉米病害专业诊断报告】，必须包含5部分：\n"
        f"1. 🌱 病害确诊：病害名称、典型识别症状\n"
        f"2. 📊 发生程度：轻度/中度/重度判定依据\n"
        f"3. 🔍 发病诱因：气候、田间管理、病原菌传播\n"
        f"4. ⚠️ 产量危害：对生长、籽粒产量、品质影响\n"
        f"5. 🛡️ 全套防治：农业防治+化学药剂+日常田间管理（具体药剂名称、用量、周期）"
    )
    messages_state = [system_role, {"role": "user", "content": analysis_prompt}]
    ai_analysis = ask_ollama(messages_state)
    messages_state.append({"role": "assistant", "content": ai_analysis})

    chart = create_disease_chart(counts)
    chat_history = [
        {"role": "user", "content": "📂 上传玉米叶片图像\n\n" + raw_output_text},
        {"role": "assistant", "content": ai_analysis}
    ]

    # 修复：YOLO的plot()返回BGR格式，需转为RGB
    plot_img = res.plot()
    if isinstance(plot_img, np.ndarray):
        plot_img = cv2.cvtColor(plot_img, cv2.COLOR_BGR2RGB)

    return plot_img, chart, risk_card, raw_output_text, chat_history, messages_state, ai_analysis


# ===================== 语音识别 =====================
def speech_to_text(audio_path):
    if audio_path is None or not os.path.exists(audio_path):
        return ""
    try:
        result = speech_model.transcribe(audio_path, language="zh", fp16=torch.cuda.is_available())
        return result["text"].strip()
    except Exception as e:
        print(f"语音识别失败: {e}")
        return f"语音转文字失败：{str(e)}"


def voice_chat(audio_path, chat_history, messages_state):
    text = speech_to_text(audio_path)
    if not text:
        yield "", chat_history, messages_state
        return
    yield from chat_stream(text, chat_history, messages_state)


# ===================== 流式对话问答 =====================
def chat_stream(user_input, chat_history, messages_state):
    user_input = user_input.strip()
    if not user_input:
        yield "", chat_history, messages_state
        return
    if not messages_state:
        messages_state.insert(0, {
            "role": "system",
            "content": "你是玉米病害农业专家，用户可咨询玉米种植、各类病害识别、防治、田间管理问题，回答简洁专业。"
        })

    messages_state.append({"role": "user", "content": user_input})
    chat_history.append({"role": "user", "content": user_input})
    chat_history.append({"role": "assistant", "content": ""})

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages_state,
        "stream": True
    }
    try:
        response = requests.post(OLLAMA_API, json=payload, stream=True, timeout=OLLAMA_TIMEOUT)
        response.raise_for_status()
        assistant_reply = ""
        for line in response.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line.decode("utf-8"))
                if "message" in data:
                    token = data["message"]["content"]
                    assistant_reply += token
                    chat_history[-1]["content"] = assistant_reply
                    yield "", chat_history, messages_state
            except json.JSONDecodeError:
                continue
        messages_state.append({"role": "assistant", "content": assistant_reply})
    except Exception as e:
        err = f"对话请求异常：{str(e)}"
        chat_history[-1]["content"] = err
        yield "", chat_history, messages_state
        messages_state.append({"role": "assistant", "content": err})


# ===================== 模型评估 =====================
def evaluate_model():
    if yolo_model is None:
        return "❌ YOLO 模型未加载，无法执行精度评估"
    if not os.path.exists(DATA_YAML):
        return f"❌ data.yaml 不存在: {DATA_YAML}，请检查路径配置"
    try:
        metrics = yolo_model.val(data=DATA_YAML, split="val", batch=1, device=DEVICE)
        map50 = clean_value(metrics.box.map50)
        map_all = clean_value(metrics.box.map)
        return f"📈 玉米病害模型验证指标:\nmAP@0.5: {map50:.4f}\nmAP@0.5-0.95: {map_all:.4f}"
    except Exception as e:
        traceback.print_exc()
        return f"❌ 模型评估失败: {str(e)}"


# ===================== CSS样式 =====================
custom_css = """
* {box-sizing: border-box;}
body {background-color: #f8fbf9 !important; margin: 0 16px;}
.gradio-container {max-width: 1600px !important; margin: 0 auto !important; padding: 20px 10px;}
.header-wrap {border-radius: 18px; box-shadow: 0 6px 18px rgba(38,120,60,0.15); overflow:hidden;}
.stat-card {border-radius:16px; box-shadow:0 4px 12px rgba(0,0,0,0.06); padding:24px 12px !important; background:#fff;}
.panel-box {border-radius:16px !important; box-shadow:0 4px 14px rgba(0,0,0,0.05); background:#ffffff; padding:24px !important; margin-bottom:16px;}
.main-title {font-size:28px; font-weight:bold; color:white; margin:0;}
.sub-title {color:#e6f9ec; font-size:16px; margin-top:6px;}
.divider {height:2px; background:linear-gradient(90deg, transparent,#d1e7dd,transparent); margin:20px 0;}
.primary-btn {background:linear-gradient(135deg,#2e7d32,#38a169) !important; color:#fff !important; font-weight:600; border-radius:10px !important; border:none;}
.primary-btn:hover {filter:brightness(1.08);}
.voice-btn {background:#3182ce !important; color:white !important; border-radius:10px;}
.read-btn {background:#805ad5 !important; color:white !important; border-radius:10px;}
.chatbot-box {border-radius:14px !important; border:1px solid #e2e8f0 !important;}
input, textarea {border-radius:10px !important;}
.accordion-header {font-weight:600 !important; font-size:15px;}
"""

# ===================== Gradio界面 =====================
demo = gr.Blocks()
with demo:
    messages_state = gr.State([])
    last_report_text = gr.State("")

    # 顶部主标题栏
    gr.HTML("""
    <div class="header-wrap">
    <div style="text-align:center;padding:30px;background:linear-gradient(135deg,#1b5e20,#388e3c);">
        <h1 class="main-title">🌽 智慧农业玉米病害智能诊断平台</h1>
        <p class="sub-title">YOLOv11目标检测 + Ollama本地大模型 + 植物病理专家AI系统</p>
    </div>
    </div>
    """)

    with gr.Accordion("📖 项目功能简介", open=False):
        gr.Markdown("""
        ### 平台能力
        1. 玉米叶片图像病害自动识别、标记、数量统计
        2. AI自动生成标准化病害诊断报告（症状/诱因/危害/防治）
        3. 文字/麦克风语音两种交互方式咨询农业专家
        4. 病害统计可视化柱状图、病害风险等级可视化卡片
        5. 模型mAP精度一键评估、诊断文本语音朗读
        """)

    gr.HTML('<div class="divider"></div>')

    # 顶部统计三卡片
    with gr.Row():
        with gr.Column(scale=1, elem_classes="stat-card"):
            gr.Markdown(
                "<div align='center'><h3 style='color:#2e7d32;margin:0'>🌽 识别病害种类</h3><h1 style='font-size:42px;margin:8px 0'>4</h1><p style='color:#666'>全覆盖常见玉米叶部病害</p></div>")
        with gr.Column(scale=1, elem_classes="stat-card"):
            gr.Markdown(
                "<div align='center'><h3 style='color:#2e7d32;margin:0'>📈 模型综合精度</h3><h1 style='font-size:42px;margin:8px 0'>96%+</h1><p style='color:#666'>本地离线推理稳定可靠</p></div>")
        with gr.Column(scale=1, elem_classes="stat-card"):
            gr.Markdown(
                "<div align='center'><h3 style='color:#2e7d32;margin:0'>🧠 AI运行模式</h3><h1 style='font-size:42px;margin:8px 0'>本地离线</h1><p style='color:#666'>Ollama大模型本地部署</p></div>")

    gr.HTML('<div class="divider"></div>')

    # 主体左右分栏
    with gr.Row():
        with gr.Column(scale=3, elem_classes="panel-box"):
            gr.Markdown("## 📷 图像病害检测模块")
            image_input = gr.Image(type="pil", label="上传玉米叶片/植株图像", height=320)

            with gr.Row():
                conf_slider = gr.Slider(minimum=0.1, maximum=0.9, value=0.25, step=0.05, label="置信度过滤阈值")
                btn_detect = gr.Button("🔍 一键病害检测+生成诊断", elem_classes="primary-btn")

            gr.HTML('<div class="divider"></div>')
            gr.Markdown("### 📊 检测可视化结果")
            output_img = gr.Image(label="病害标记效果图", height=280)
            risk_html = gr.HTML(label="病害风险等级卡片")
            disease_chart = gr.Plot(label="病害数量统计柱状图")
            detect_output = gr.Textbox(label="原始检测数据摘要", lines=3, interactive=False)

            with gr.Accordion("⚙️ 模型评估工具", open=False):
                eval_btn = gr.Button("📈 运行模型mAP精度评估", variant="secondary")
                eval_output = gr.Textbox(label="评估输出", interactive=False)

        with gr.Column(scale=6, elem_classes="panel-box"):
            gr.Markdown("## 🧠 玉米病害专家问答系统")
            chatbot = gr.Chatbot(
                label="AI专家对话窗口",
                height=620,
                avatar_images=(None, "https://cdn-icons-png.flaticon.com/512/1075/1075168.png"),
                elem_classes="chatbot-box",

            )
            gr.HTML('<div class="divider"></div>')
            gr.Markdown("### 💬 交互输入区")
            with gr.Row():
                voice_input = gr.Audio(sources=["microphone"], type="filepath", label="🎤 麦克风语音提问", scale=3)
                voice_btn = gr.Button("语音发送", elem_classes="voice-btn", scale=1)
                read_btn = gr.Button("朗读最新诊断", elem_classes="read-btn", scale=1)
            with gr.Row():
                user_question = gr.Textbox(
                    label="文字咨询输入框",
                    placeholder="输入病害相关问题，例如：大斑病用什么农药？多雨天气如何预防锈病？",
                    lines=2, scale=6
                )
                send_btn = gr.Button("发送\n🚀", variant="primary", scale=1, elem_classes="primary-btn")
            audio_output = gr.Audio(label="诊断语音朗读音频", visible=True)

    # 事件绑定
    btn_detect.click(
        fn=detect_image,
        inputs=[image_input, conf_slider],
        outputs=[output_img, disease_chart, risk_html, detect_output, chatbot, messages_state, last_report_text]
    )
    eval_btn.click(fn=evaluate_model, outputs=[eval_output])
    send_btn.click(
        fn=chat_stream,
        inputs=[user_question, chatbot, messages_state],
        outputs=[user_question, chatbot, messages_state]
    )
    user_question.submit(
        fn=chat_stream,
        inputs=[user_question, chatbot, messages_state],
        outputs=[user_question, chatbot, messages_state]
    )
    voice_btn.click(
        fn=voice_chat,
        inputs=[voice_input, chatbot, messages_state],
        outputs=[user_question, chatbot, messages_state]
    )
    read_btn.click(
        fn=read_diagnosis_text,
        inputs=[last_report_text],
        outputs=[audio_output]
    )


# 清理临时音频文件
def clean_temp_audio():
    if os.path.exists(TEMP_AUDIO_DIR):
        shutil.rmtree(TEMP_AUDIO_DIR, ignore_errors=True)


if __name__ == "__main__":
    try:
        demo.launch(
            server_name="127.0.0.1",
            server_port=7860,
            inbrowser=True,
            share=False,
            debug=False,
            theme=gr.themes.Soft(primary_hue="green", neutral_hue="slate"),
            css=custom_css
        )
    finally:
        clean_temp_audio()