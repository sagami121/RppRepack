import sys
import os
import json
import traceback
from datetime import datetime
import pyzipper
import shutil

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QTextEdit, QMessageBox, QLabel,
    QProgressBar, QCheckBox, QLineEdit,
    QRadioButton, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor, QFont, QIcon, QAction

CONFIG_FILE = "config.json"
LOG_DIR = "log"
# 実行時の日時をファイル名に含める
_timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = os.path.join(LOG_DIR, f"log_{_timestamp_str}.txt")

# ログフォルダの作成
os.makedirs(LOG_DIR, exist_ok=True)

ERROR_CODES = {
    "RPP_NOT_SELECTED": "E001",
    "SAVE_DIR_NOT_SELECTED": "E002",
    "RPP_PARSE_FAIL": "E003",
    "ZIP_FAIL": "E004",
    "CONFIG_LOAD_FAIL": "E005",
    "CONFIG_SAVE_FAIL": "E006",
    "GENERAL_EXCEPTION": "E999"
}


class RppRepack(QWidget):
    def __init__(self):
        super().__init__()
        self.rpp_path = ""
        self.save_dir = ""
        self.assets_path = os.path.join(os.path.dirname(__file__), "assets") 
        self.init_ui()
        self.load_config()

    def init_ui(self):
        self.setWindowTitle("RppRepack v1.0")
        self.setGeometry(200, 200, 600, 500)

        layout = QVBoxLayout()

        self.drop_area = QLabel("ここに RPP ファイルをドラッグ & ドロップ")
        self.drop_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #666;
                border-radius: 8px;
                padding: 40px;
                color: #aaa;
                font-size: 14px;
            }
        """)
        self.drop_area.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.drop_area.mousePressEvent = self.select_rpp_via_click
        layout.addWidget(self.drop_area)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        btn_select_dir = QPushButton("📂 保存先フォルダを選択")
        btn_select_dir.clicked.connect(self.select_dir)
        layout.addWidget(btn_select_dir)

        output_layout = QHBoxLayout()
        self.radio_zip = QRadioButton("ZIP 出力")
        self.radio_folder = QRadioButton("フォルダ出力")
        self.radio_zip.setChecked(True)  # デフォルトはZIP
        output_layout.addWidget(self.radio_zip)
        output_layout.addWidget(self.radio_folder)
        layout.addLayout(output_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 6px;
                background-color: #2d2d2d;
                color: #ddd;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #007acc;
                width: 10px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.password_checkbox = QCheckBox("パスワードを設定する")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setEnabled(False)

        self.toggle_action = QAction(self)
        self.toggle_action.setCheckable(True)
        self.toggle_action.toggled.connect(self.toggle_password_visibility)
        self.password_input.addAction(self.toggle_action, QLineEdit.ActionPosition.TrailingPosition)
        self.toggle_action.setIcon(QIcon(os.path.join(self.assets_path, "visibility_off.png")))

        self.password_checkbox.stateChanged.connect(
            lambda state: self.password_input.setEnabled(state == Qt.CheckState.Checked.value)
        )

        layout.addWidget(self.password_checkbox)
        layout.addWidget(self.password_input)

        btn_make = QPushButton("実行")
        btn_make.clicked.connect(self.make_package)
        layout.addWidget(btn_make)

        self.setLayout(layout)
        self.setAcceptDrops(True)


    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith(".rpp"):
                event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith(".rpp"):
                self.rpp_path = path
                self.log_msg(f"[RppRepack] ドロップされたRPP: {path}")
                self.drop_area.setText(f"選択中: {os.path.basename(path)}")

    def select_rpp_via_click(self, event):
        try:
            path, _ = QFileDialog.getOpenFileName(self, "RPPファイルを選択", "", "Reaper Project (*.rpp)")
            if path:
                self.rpp_path = path
                self.log_msg(f"[RppRepack] 選択されたRPP: {path}")
                self.drop_area.setText(f"選択中: {os.path.basename(path)}")
        except Exception:
            self.write_log(traceback.format_exc(), ERROR_CODES["GENERAL_EXCEPTION"])

    def log_msg(self, msg):
        self.log.append(msg)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except Exception:
            pass

    def write_log(self, text, code="E999"):
        try:
            timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"{timestamp} [{code}] {text}\n")
            self.log_msg(f"[{code}] エラーが log.txt に記録されました")
        except Exception:
            pass

    def select_dir(self):
        try:
            path = QFileDialog.getExistingDirectory(self, "保存先フォルダを選択")
            if path:
                self.save_dir = path
                self.log_msg(f"[RppRepack] 保存先: {path}")
                self.save_config()
        except Exception:
            self.write_log(traceback.format_exc(), ERROR_CODES["GENERAL_EXCEPTION"])

    def load_config(self):
        if os.path.isfile(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.save_dir = data.get("save_dir", "")
                    if self.save_dir:
                        self.log_msg(f"[RppRepack] 前回の保存先: {self.save_dir}")
            except Exception:
                self.write_log(traceback.format_exc(), ERROR_CODES["CONFIG_LOAD_FAIL"])

    def save_config(self):
        data = {"save_dir": self.save_dir}
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception:
            self.write_log(traceback.format_exc(), ERROR_CODES["CONFIG_SAVE_FAIL"])


    def _parse_rpp_files(self):
        try:
            if not self.rpp_path:
                return []
            encodings = ["utf-8", "cp932", "latin1"]
            file_lines = None
            for enc in encodings:
                try:
                    with open(self.rpp_path, "r", encoding=enc) as f:
                        file_lines = f.readlines()
                    break
                except Exception:
                    continue
            if file_lines is None:
                self.write_log("RPPファイル解析失敗", ERROR_CODES["RPP_PARSE_FAIL"])
                return []

            project_dir = os.path.dirname(self.rpp_path)
            file_set = set()
            for line in file_lines:
                if "FILE \"" in line:
                    start = line.find("\"") + 1
                    end = line.rfind("\"")
                    if start < end:
                        file_path = line[start:end]
                        if not os.path.isabs(file_path):
                            file_path = os.path.join(project_dir, file_path)
                        file_set.add(file_path)
            return list(file_set)
        except Exception:
            self.write_log(traceback.format_exc(), ERROR_CODES["RPP_PARSE_FAIL"])
            return []

    def make_package(self):
        try:
            if not self.rpp_path:
                self.show_message(QMessageBox.Icon.Warning, "エラー",
                                  f"[{ERROR_CODES['RPP_NOT_SELECTED']}] RPPファイルが選択されていません")
                return
            if not self.save_dir:
                self.show_message(QMessageBox.Icon.Warning, "エラー",
                                  f"[{ERROR_CODES['SAVE_DIR_NOT_SELECTED']}] 保存先フォルダが選択されていません")
                return

            project_name = os.path.splitext(os.path.basename(self.rpp_path))[0]

            if self.radio_zip.isChecked():
                self._make_zip(project_name)
            else:
                self._make_folder(project_name)

        except Exception:
            self.write_log(traceback.format_exc(), ERROR_CODES["ZIP_FAIL"])

    def _make_zip(self, project_name):
        zip_path = os.path.join(self.save_dir, f"{project_name}.zip")
        if os.path.exists(zip_path):
            counter = 1
            while True:
                zip_path = os.path.join(self.save_dir, f"{project_name}_{counter}.zip")
                if not os.path.exists(zip_path):
                    break
                counter += 1

        password = None
        encryption = None
        if self.password_checkbox.isChecked():
            password = self.password_input.text().strip()
            if password:
                encryption = pyzipper.WZ_AES

        files_to_add = [self.rpp_path] + [f for f in self._parse_rpp_files() if os.path.isfile(f)]
        total_files = len(files_to_add)
        self.progress_bar.setMaximum(total_files)
        self.progress_bar.setValue(0)

        files_added = 0
        added_files = set()

        with pyzipper.AESZipFile(zip_path, "w", compression=pyzipper.ZIP_DEFLATED,
                                 encryption=encryption) as zipf:
            if password:
                zipf.setpassword(password.encode("utf-8"))

            for f in files_to_add:
                if f not in added_files:
                    zipf.write(f, os.path.basename(f))
                    self.log_msg(f"[RppRepack] 追加: {f}")
                    files_added += 1
                    added_files.add(f)
                    self.progress_bar.setValue(files_added)
                    QApplication.processEvents()

        self.show_message(QMessageBox.Icon.Information, "完了",
                          f"{files_added} 個のファイルをZIP化しました。\n\n保存先: {zip_path}")
        self.progress_bar.setValue(0)
        self.log_msg("[RppRepack] === ZIP作成完了 ===")
        self.open_in_explorer(zip_path)

    def _make_folder(self, project_name):
        folder_path = os.path.join(self.save_dir, project_name)
        if os.path.exists(folder_path):
            counter = 1
            while True:
                folder_path = os.path.join(self.save_dir, f"{project_name}_{counter}")
                if not os.path.exists(folder_path):
                    break
                counter += 1
        os.makedirs(folder_path, exist_ok=True)

        files_to_copy = [self.rpp_path] + [f for f in self._parse_rpp_files() if os.path.isfile(f)]
        total_files = len(files_to_copy)
        self.progress_bar.setMaximum(total_files)
        self.progress_bar.setValue(0)

        files_copied = 0
        for f in files_to_copy:
            dest = os.path.join(folder_path, os.path.basename(f))
            shutil.copy2(f, dest)
            self.log_msg(f"[RppRepack] コピー: {f} → {dest}")
            files_copied += 1
            self.progress_bar.setValue(files_copied)
            QApplication.processEvents()

        self.show_message(QMessageBox.Icon.Information, "完了",
                          f"{files_copied} 個のファイルをフォルダにコピーしました。\n\n保存先: {folder_path}")
        self.progress_bar.setValue(0)
        self.log_msg("[RppRepack] === フォルダ出力完了 ===")
        self.open_in_explorer(folder_path)

    def show_message(self, icon, title, text):
        try:
            msg = QMessageBox(self)
            msg.setIcon(icon)
            msg.setWindowTitle(title)
            msg.setText(text)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #222;
                    color: #fff;
                }
                QPushButton {
                    background-color: #444;
                    color: #fff;
                    border: 1px solid #666;
                    padding: 4px 8px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #555;
                }
            """)
            msg.exec()
        except Exception:
            self.write_log(traceback.format_exc(), ERROR_CODES["GENERAL_EXCEPTION"])

    def toggle_password_visibility(self, checked):
        if checked:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_action.setIcon(QIcon(os.path.join(self.assets_path, "visibility.png")))
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_action.setIcon(QIcon(os.path.join(self.assets_path, "visibility_off.png")))

    def open_in_explorer(self, path):
        try:
            if sys.platform.startswith("win"):
                os.startfile(os.path.dirname(path))
            elif sys.platform.startswith("darwin"):
                os.system(f"open '{os.path.dirname(path)}'")
            else:
                os.system(f"xdg-open '{os.path.dirname(path)}'")
        except Exception:
            self.write_log(traceback.format_exc(), ERROR_CODES["GENERAL_EXCEPTION"])

def apply_dark_theme(app):
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(60, 60, 60))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 122, 204))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

    app.setPalette(dark_palette)
    app.setStyleSheet("""
        QWidget {
            font-family: 'Yu Gothic UI';
        }
        QPushButton {
            background-color: #444;
            color: #eee;
            border: 1px solid #666;
            padding: 8px;
            border-radius: 6px;
        }
        QPushButton:hover { background-color: #555; }
        QPushButton:pressed { background-color: #222; }
        QTextEdit {
            background-color: #222;
            color: #ddd;
            border: 1px solid #555;
            border-radius: 6px;
        }
        QLineEdit {
            background-color: #222;
            color: #ddd;
            border: 1px solid #555;
            border-radius: 6px;
            padding: 4px;
        }
    """)

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        app.setFont(QFont("Yu Gothic UI", 10))
        apply_dark_theme(app)
        win = RppRepack()
        win.show()
        sys.exit(app.exec())
    except Exception:
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} [{ERROR_CODES['GENERAL_EXCEPTION']}] {traceback.format_exc()}\n")
