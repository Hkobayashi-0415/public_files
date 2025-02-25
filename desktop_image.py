import sys
import os
import json
import random
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QSizePolicy,
    QMessageBox,
)
from PyQt6.QtGui import QPixmap, QMouseEvent
from PyQt6.QtCore import Qt, QTimer, QPoint

def resource_path(relative_path):
    """
    PyInstallerで実行時のリソースパスを取得するための関数。
    """
    try:
        # PyInstallerでパッケージ化された場合、リソースは一時フォルダに展開される
        base_path = sys._MEIPASS
    except AttributeError:
        # スクリプトとして実行されている場合
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

CONFIG_FILE = "config.json"
EXCLUDE_FOLDER = "00_original"

def get_config_path():
    """
    config.jsonの保存先をユーザーのデータディレクトリに設定。
    """
    if sys.platform == "win32":
        app_data = os.getenv("APPDATA")
    elif sys.platform == "darwin":
        app_data = os.path.expanduser("~/Library/Application Support")
    else:
        app_data = os.path.expanduser("~/.config")
    config_dir = os.path.join(app_data, "CharacterApp")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, CONFIG_FILE)

CONFIG_FILE_PATH = get_config_path()

def load_config():
    """
    設定ファイルを読み込む。存在しない場合はデフォルト設定を作成する。
    """
    if not os.path.exists(CONFIG_FILE_PATH):
        default_config = {
            "selected_character": "00_original",
            "window_x": 100,
            "window_y": 100,
        }
        try:
            with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            return default_config
        except Exception as e:
            QMessageBox.critical(
                None,
                "設定ファイルの作成エラー",
                f"設定ファイルの作成に失敗しました。\n{e}",
            )
            sys.exit(1)
    try:
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        # 設定内容の検証
        if not isinstance(config, dict):
            raise ValueError("設定ファイルの形式が不正です。")
        required_keys = {"selected_character", "window_x", "window_y"}
        if not required_keys.issubset(config.keys()):
            raise ValueError("設定ファイルに必要なキーが不足しています。")
        return config
    except Exception as e:
        QMessageBox.critical(
            None,
            "設定ファイルの読み込みエラー",
            f"設定ファイルの読み込みに失敗しました。\n{e}\nデフォルト設定を使用します。",
        )
        # デフォルト設定を返す
        return {
            "selected_character": "00_original",
            "window_x": 100,
            "window_y": 100,
        }

def save_config(config):
    """
    設定ファイルを保存する。
    """
    try:
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        QMessageBox.critical(
            None,
            "設定ファイルの保存エラー",
            f"設定ファイルの保存に失敗しました。\n{e}",
        )

class CharacterWindow(QMainWindow):
    STATES = ["01_normal", "02_smile", "03_oko", "04_sleep", "05_on"]

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.selected_character = self.config["selected_character"]
        self.setWindowTitle("キャラクター表示")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(
            self.config.get("window_x", 100),
            self.config.get("window_y", 100),
            300,
            300,
        )

        self.state = "01_normal"
        self.click_count = 0
        self.drag_position = QPoint()

        # メインウィジェットとレイアウト
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ツールバー（上部）とキャラクター選択ボタンを統合
        self.top_toolbar = QWidget(self)
        self.top_toolbar.setFixedHeight(30)
        self.top_toolbar.setStyleSheet("""
            background-color: rgba(50, 50, 50, 30); /* 半透明 */
        """)
        self.top_toolbar_layout = QHBoxLayout(self.top_toolbar)
        self.top_toolbar_layout.setContentsMargins(5, 0, 5, 0)
        self.top_toolbar_layout.setSpacing(10)

        # キャラクター選択コンボボックスの追加
        self.character_selector = QComboBox()
        self.character_selector.addItems(self.get_character_folders())
        self.character_selector.setCurrentText(self.selected_character)
        self.character_selector.currentTextChanged.connect(self.change_character)
        # スタイルシートで背景を白に設定
        self.character_selector.setStyleSheet("""
            QComboBox {
                background-color: white;
                color: black;
                border: 1px solid gray;
                border-radius: 5px;
                padding: 2px 4px;
            }
            QComboBox::drop-down {
                border-left-width: 1px;
                border-left-color: darkgray;
                border-left-style: solid; /* just a single line */
                border-top-right-radius: 3px; /* same radius as the QComboBox */
                border-bottom-right-radius: 3px;
            }
            QComboBox::drop-down:on {
                background: #B1B1B1;
            }
        """)
        self.top_toolbar_layout.addWidget(self.character_selector, alignment=Qt.AlignmentFlag.AlignLeft)

        # 閉じるボタンの追加
        self.close_button = QPushButton("×", self.top_toolbar)
        self.close_button.setFixedSize(20, 20)
        self.close_button.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: transparent;
                border: none;
                font-size: 25px;
            }
            QPushButton:hover {
                color: red;
            }
        """)
        self.close_button.clicked.connect(self.close)
        self.top_toolbar_layout.addWidget(self.close_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.main_layout.addWidget(self.top_toolbar)

        # 画像表示ラベルを追加（中央）
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFixedSize(280, 260)
        self.label.setStyleSheet("background: transparent;")
        self.label.mousePressEvent = self.handle_image_click
        self.label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.main_layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignCenter)

        # 画像リストとロード
        self.images = {state: [] for state in self.STATES}
        self.last_image = None
        self.load_images()
        self.show_random_image()

        # タイマー設定
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.reset_state)

        self.sleep_timer = QTimer(self)
        self.sleep_timer.timeout.connect(self.go_to_sleep)
        self.sleep_timer.start(15 * 60 * 1000)  # 15分後にスリープ状態

    def get_character_folders(self):
        """
        キャラクターフォルダを取得する。
        """
        # 修正: "app_desktop_image" を削除し、現在のフォルダ（スクリプトが存在する）から "desktop_image/image" を参照
        character_base_path = resource_path(os.path.join("desktop_image", "image"))
        if not os.path.exists(character_base_path):
            QMessageBox.warning(
                self,
                "フォルダが見つかりません",
                f"キャラクターフォルダが見つかりません。\nパス: {character_base_path}",
            )
            return []
        folders = [
            folder
            for folder in os.listdir(character_base_path)
            if os.path.isdir(os.path.join(character_base_path, folder))
            and folder != EXCLUDE_FOLDER
        ]
        if not folders:
            QMessageBox.warning(
                self,
                "キャラクターフォルダがありません",
                f"キャラクターフォルダが存在しません。\n除外フォルダ: {EXCLUDE_FOLDER}",
            )
        return folders

    def load_images(self):
        """
        各状態の画像をロードする。
        """
        for state in self.STATES:
            folder = resource_path(os.path.join("desktop_image", "image", self.selected_character, state))
            if os.path.exists(folder):
                try:
                    images = [
                        os.path.join(folder, f)
                        for f in os.listdir(folder)
                        if f.lower().endswith((".png", ".jpg", ".jpeg"))
                    ]
                    if not images:
                        print(f"警告: フォルダ '{folder}' に画像が存在しません。")
                    self.images[state] = images
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "画像の読み込みエラー",
                        f"フォルダ '{folder}' の画像読み込み中にエラーが発生しました。\n{e}",
                    )
            else:
                print(f"警告: フォルダ '{folder}' が存在しません。")

    def show_random_image(self):
        """
        現在の状態に応じたランダムな画像を表示する。
        """
        image_list = self.images.get(self.state, [])
        if not image_list:
            print(f"警告: 状態 '{self.state}' に対応する画像がありません。")
            self.label.clear()
            return
        available_images = [img for img in image_list if img != self.last_image]
        if not available_images:
            available_images = image_list
        new_image = random.choice(available_images)
        self.last_image = new_image
        try:
            pixmap = QPixmap(new_image)
            if pixmap.isNull():
                raise ValueError(f"画像 '{new_image}' を読み込めませんでした。")
            self.label.setPixmap(
                pixmap.scaled(
                    self.label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "画像表示エラー",
                f"画像 '{new_image}' の表示に失敗しました。\n{e}",
            )
            self.label.clear()

    def handle_image_click(self, event: QMouseEvent):
        """
        画像がクリックされたときの処理。
        左クリックのみで反応する。
        """
        if event.button() == Qt.MouseButton.LeftButton:
            try:
                if self.state == "01_normal":
                    self.click_count += 1
                    if self.click_count >= 5:
                        self.state = random.choice(["02_smile", "03_oko"])
                        self.click_count = 0
                        self.timer.start(10000)  # 10秒後に元に戻す
                elif self.state == "04_sleep":
                    self.state = "05_on"
                    self.timer.start(10000)
                self.show_random_image()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "クリック処理エラー",
                    f"画像クリック時の処理中にエラーが発生しました。\n{e}",
                )

    def reset_state(self):
        """
        タイマーで状態を元に戻す処理。
        """
        try:
            self.state = "01_normal"
            self.show_random_image()
            self.timer.stop()
        except Exception as e:
            QMessageBox.critical(
                self,
                "状態リセットエラー",
                f"状態のリセット中にエラーが発生しました。\n{e}",
            )

    def go_to_sleep(self):
        """
        タイマーでスリープ状態に移行する処理。
        """
        try:
            self.state = "04_sleep"
            self.show_random_image()
        except Exception as e:
            QMessageBox.critical(
                self,
                "スリープ状態エラー",
                f"スリープ状態への移行中にエラーが発生しました。\n{e}",
            )

    def change_character(self, character_name):
        """
        キャラクターが変更されたときの処理。
        """
        try:
            # 選択したキャラクターのフォルダが存在するか確認
            character_folder = resource_path(os.path.join("desktop_image", "image", character_name))
            if not os.path.exists(character_folder):
                QMessageBox.warning(
                    self,
                    "キャラクターフォルダが見つかりません",
                    f"選択したキャラクターのフォルダが見つかりません。\nフォルダ名: {character_name}",
                )
                return
            self.selected_character = character_name
            self.config["selected_character"] = character_name
            save_config(self.config)
            self.load_images()
            self.state = "01_normal"
            self.click_count = 0
            self.show_random_image()
        except Exception as e:
            QMessageBox.critical(
                self,
                "キャラクター変更エラー",
                f"キャラクター変更中にエラーが発生しました。\n{e}",
            )

    def closeEvent(self, event):
        """
        ウィンドウが閉じられるときの処理。
        """
        try:
            self.config["window_x"] = self.x()
            self.config["window_y"] = self.y()
            save_config(self.config)
            event.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                "ウィンドウクローズエラー",
                f"ウィンドウのクローズ処理中にエラーが発生しました。\n{e}",
            )
            event.ignore()

    def mousePressEvent(self, event: QMouseEvent):
        """
        マウスがクリックされたときの処理。
        左クリックでウィンドウのドラッグ。
        """
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                "マウスクリックエラー",
                f"マウスクリック時の処理中にエラーが発生しました。\n{e}",
            )

    def mouseMoveEvent(self, event: QMouseEvent):
        """
        マウスが移動されたときの処理。
        左クリックを押しながらドラッグでウィンドウを移動する。
        """
        try:
            if event.buttons() & Qt.MouseButton.LeftButton:
                self.move(event.globalPosition().toPoint() - self.drag_position)
                event.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                "マウス移動エラー",
                f"マウス移動時の処理中にエラーが発生しました。\n{e}",
            )

def main():
    app = QApplication(sys.argv)
    window = CharacterWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
