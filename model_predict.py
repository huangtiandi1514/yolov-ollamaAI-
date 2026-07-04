import os
# ===================== GPU稳定关键环境配置 =====================
os.environ["QT_OPENGL"] = "software"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

import sys
import cv2
import numpy as np
from collections import Counter
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from ultralytics import YOLO
import threading
import warnings
warnings.filterwarnings('ignore')

logging = __import__('logging')
logging.getLogger('ultralytics').setLevel(logging.WARNING)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLO 智能目标检测系统")
        self.setFixedSize(1520, 780)

        self.model = None
        self.conf_threshold = 0.25
        self.current_annotated_image = None
        self.result = None

        # 视频控制
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.is_paused = False
        self.is_video_running = False

        # 视频保存
        self.video_writer = None
        self.is_saving_video = False

        # 训练相关
        self.train_thread = None
        self.is_training = False

        self.init_ui()
        self.bind_events()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        left_widget = QWidget()
        left_widget.setStyleSheet("""
            QWidget {
                background-color: #f7f8fa;
                border-radius: 12px;
            }
        """)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(20, 24, 20, 24)
        left_layout.setSpacing(14)

        title = QLabel("控制面板")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font: 700 20px 'Microsoft YaHei';
            color: #2c3e50;
            padding-bottom: 6px;
        """)
        left_layout.addWidget(title)

        button_style = """
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4361EE, stop:1 #4CC9F0);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px;
                font: 600 14px 'Microsoft YaHei';
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3553E0, stop:1 #3BB8E0);
            }
            QPushButton:pressed {
                background-color: #2A43C6;
            }
        """

        self.btn_model = QPushButton("📁 加载检测模型")
        self.btn_img = QPushButton("🖼️ 单图检测")
        self.btn_folder = QPushButton("📂 文件夹检测")
        self.btn_video = QPushButton("🎥 视频检测")
        self.btn_camera = QPushButton("📷 摄像头检测")
        self.btn_pause = QPushButton("⏸️ 暂停播放")
        self.btn_save_video = QPushButton("💽 保存检测视频")
        self.btn_stop = QPushButton("⏹️ 停止播放")
        self.btn_save_img = QPushButton("💾 保存检测图片")
        self.btn_train = QPushButton("🚀 开始模型训练")
        self.btn_exit = QPushButton("❌ 退出系统")

        btns = [
            self.btn_model, self.btn_img, self.btn_folder,
            self.btn_video, self.btn_camera, self.btn_pause,
            self.btn_save_video, self.btn_stop, self.btn_save_img,
            self.btn_train, self.btn_exit
        ]
        for btn in btns:
            btn.setMinimumHeight(44)
            btn.setStyleSheet(button_style)
            left_layout.addWidget(btn)

        left_layout.addStretch()

        info_group = QGroupBox("日志信息")
        info_group.setStyleSheet("""
            QGroupBox {
                font: 600 15px 'Microsoft YaHei';
                color: #2c3e50;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                margin-top: 12px;
                padding: 10px;
                background-color: white;
            }
        """)
        info_layout = QVBoxLayout(info_group)
        self.text_info = QTextEdit()
        self.text_info.setReadOnly(True)
        self.text_info.setStyleSheet("""
            QTextEdit {
                border: none;
                font: 13px 'Consolas';
                color: #2d3748;
                padding: 10px;
                background-color: #fbfcfe;
                border-radius: 8px;
            }
        """)
        self.text_info.setMinimumHeight(220)
        info_layout.addWidget(self.text_info)
        left_layout.addWidget(info_group)

        right_layout = QHBoxLayout()
        right_layout.setSpacing(20)

        self.label_original = QLabel("原始画面")
        self.label_original.setAlignment(Qt.AlignCenter)
        self.label_original.setStyleSheet("""
            QLabel {
                background-color: #1E1E2E;
                border-radius: 12px;
                color: #AAAAAA;
                font: 16px 'Microsoft YaHei';
                border: 1px solid #383A56;
            }
        """)
        self.label_original.setFixedSize(680, 700)

        self.label_result = QLabel("检测结果")
        self.label_result.setAlignment(Qt.AlignCenter)
        self.label_result.setStyleSheet("""
            QLabel {
                background-color: #1E1E2E;
                border-radius: 12px;
                color: #AAAAAA;
                font: 16px 'Microsoft YaHei';
                border: 1px solid #383A56;
            }
        """)
        self.label_result.setFixedSize(680, 700)

        right_layout.addWidget(self.label_original)
        right_layout.addWidget(self.label_result)
        main_layout.addWidget(left_widget, 1)
        main_layout.addLayout(right_layout, 3)

    def bind_events(self):
        self.btn_model.clicked.connect(self.load_model)
        self.btn_img.clicked.connect(self.open_image)
        self.btn_folder.clicked.connect(self.open_folder)
        self.btn_video.clicked.connect(self.open_video)
        self.btn_camera.clicked.connect(self.open_camera)
        self.btn_pause.clicked.connect(self.toggle_pause)
        self.btn_save_video.clicked.connect(self.start_save_video)
        self.btn_stop.clicked.connect(self.stop_all)
        self.btn_save_img.clicked.connect(self.save_image_result)
        self.btn_train.clicked.connect(self.start_train)
        self.btn_exit.clicked.connect(self.close)

    # 模型训练 用GPU device=0
    def start_train(self):
        if self.is_training:
            QMessageBox.warning(self, "提示", "训练正在进行中！")
            return

        yaml_path, _ = QFileDialog.getOpenFileName(self, "选择数据集yaml", "", "YAML (*.yaml *.yml)")
        if not yaml_path:
            return

        epochs, ok = QInputDialog.getInt(self, "训练设置", "训练轮数 Epochs:", 50, 1, 1000, 1)
        if not ok:
            return

        batch, ok = QInputDialog.getInt(self, "训练设置", "Batch Size:", 8, 1, 64, 1)
        if not ok:
            return

        imgsz, ok = QInputDialog.getInt(self, "训练设置", "图像尺寸 IMGSZ:", 640, 320, 1280, 32)
        if not ok:
            return

        self.is_training = True
        self.btn_train.setText("🔄 训练中...")
        self.btn_train.setEnabled(False)
        self.text_info.append("=" * 60)
        self.text_info.append(f"📌 开始GPU训练：yaml={yaml_path} epochs={epochs} batch={batch} imgsz={imgsz}")

        self.train_thread = threading.Thread(
            target=self.run_train,
            args=(yaml_path, epochs, batch, imgsz),
            daemon=True
        )
        self.train_thread.start()

    def run_train(self, yaml_path, epochs, batch, imgsz):
        try:
            model = YOLO("yolov11s.pt")
            # GPU训练 device=0
            model.train(
                data=yaml_path,
                epochs=epochs,
                batch=batch,
                imgsz=imgsz,
                device=0,
                workers=0,
                amp=True
            )
            self.text_info.append("✅ GPU训练完成！最佳模型保存在 runs/detect/train/weights/best.pt")
        except Exception as e:
            self.text_info.append(f"❌ 训练失败：{str(e)}")
        finally:
            self.is_training = False
            self.btn_train.setText("🚀 开始模型训练")
            self.btn_train.setEnabled(True)

    def open_video(self):
        if not self.model:
            QMessageBox.warning(self, "提示", "请先加载模型")
            return
        path, _ = QFileDialog.getOpenFileName(self, "选择视频", "", "视频 (*.mp4 *.avi *.mov *.mkv)")
        if path:
            self.stop_all()
            self.cap = cv2.VideoCapture(path)
            self.is_video_running = True
            self.is_paused = False
            self.btn_pause.setText("⏸️ 暂停播放")
            self.timer.start(30)

    def open_camera(self):
        if not self.model:
            QMessageBox.warning(self, "提示", "请先加载模型")
            return
        self.stop_all()
        self.cap = cv2.VideoCapture(0)
        self.is_video_running = True
        self.is_paused = False
        self.btn_pause.setText("⏸️ 暂停播放")
        self.timer.start(30)

    def toggle_pause(self):
        if not self.is_video_running:
            return
        self.is_paused = not self.is_paused
        self.btn_pause.setText("▶ 继续播放" if self.is_paused else "⏸️ 暂停播放")

    def start_save_video(self):
        if not self.is_video_running:
            QMessageBox.warning(self, "提示", "请先打开视频或摄像头")
            return
        if self.video_writer:
            QMessageBox.information(self, "提示", "正在保存视频...")
            return

        path, _ = QFileDialog.getSaveFileName(self, "保存视频", "", "MP4 (*.mp4)")
        if not path:
            return

        fps = 30
        w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(path, fourcc, fps, (w, h))
        self.is_saving_video = True
        self.text_info.append(f"📹 开始保存视频：{path}")

    def update_frame(self):
        if not self.cap or not self.is_video_running or self.is_paused:
            return
        ret, frame = self.cap.read()
        if not ret:
            self.stop_all()
            self.text_info.append("✅ 视频播放完毕")
            return

        # GPU推理 device=0
        res = self.model.predict(frame, conf=self.conf_threshold, verbose=False, device=0)
        annotated = res[0].plot()
        self.result = res
        self.show_frame(frame, self.label_original)
        self.show_frame(annotated, self.label_result)
        self.show_statistics()

        if self.is_saving_video and self.video_writer:
            self.video_writer.write(annotated)

    def stop_all(self):
        self.timer.stop()
        self.is_video_running = False
        self.is_paused = False
        self.btn_pause.setText("⏸️ 暂停播放")

        if self.cap:
            self.cap.release()
            self.cap = None
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            self.is_saving_video = False
            self.text_info.append("✅ 视频保存完成")

        self.label_original.setText("原始画面")
        self.label_result.setText("检测结果")

    def load_model(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择模型", "", "模型 (*.pt *.onnx)")
        if path:
            try:
                self.model = YOLO(path)
                self.text_info.append(f"✅ 模型加载成功：{path} (GPU自动启用)")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"模型加载失败:{e}")

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "图片 (*.jpg *.jpeg *.png *.bmp)")
        if path:
            self.stop_all()
            self.detect_image(path)

    def detect_image(self, path):
        if not self.model:
            QMessageBox.warning(self, "提示", "请先加载模型")
            return
        img = cv2.imread(path)
        if img is None:
            return
        # GPU推理
        res = self.model.predict(img, conf=self.conf_threshold, verbose=False, device=0)
        self.result = res
        ann = res[0].plot()
        self.current_annotated_image = ann
        self.show_frame(img, self.label_original)
        self.show_frame(ann, self.label_result)
        self.show_statistics()

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory()
        if not folder:
            return
        self.stop_all()
        exts = ('.jpg', '.jpeg', '.png', '.bmp')
        imgs = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(exts)]
        for p in imgs:
            self.detect_image(p)
            cv2.waitKey(600)

    def save_image_result(self):
        if self.current_annotated_image is None:
            QMessageBox.warning(self, "提示", "暂无检测结果")
            return
        path, _ = QFileDialog.getSaveFileName(self, "保存图片", "", "JPG (*.jpg);;PNG (*.png)")
        if path:
            cv2.imwrite(path, self.current_annotated_image)
            self.text_info.append(f"💾 图片已保存：{path}")

    def show_frame(self, img, label):
        h, w, ch = img.shape
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        q_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(q_img).scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(pix)

    def show_statistics(self):
        if not self.result:
            self.text_info.setText("未检测到目标")
            return
        cnt = Counter()
        target = {0, 1}
        for r in self.result:
            if r.boxes.cls is not None:
                cls = r.boxes.cls.cpu().numpy().astype(int).tolist()
                cnt.update([c for c in cls if c in target])

        class_map = {0: "头盔", 1: "反光衣"}
        msg = "📊 检测统计：\n"
        for cid, num in cnt.items():
            msg += f"• {class_map.get(cid, '未知')}：{num} 个\n"
        self.text_info.setText(msg)

    def closeEvent(self, e):
        self.stop_all()
        # 释放CUDA资源
        if self.model:
            del self.model
        e.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())