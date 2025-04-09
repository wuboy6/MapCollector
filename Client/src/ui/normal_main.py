import sys
import os
import json
import base64
import requests
import numpy as np
import cv2
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QToolButton, QMenu, QLineEdit, QCheckBox, QTableWidget,
    QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QSplitter, QTableWidgetItem,
    QScrollArea, QFrame, QStackedWidget, QTextEdit, QSizePolicy, QMessageBox,
    QTreeWidget, QTreeWidgetItem, QDialog, QFileDialog, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QFont, QImage
from src.mat_reader import MatReader

SERVER_URL = "http://127.0.0.1:8000"

def base64_to_nparray(b64str):
    """将base64图像解码为numpy数组"""
    try:
        img_data = base64.b64decode(b64str)
        np_arr = np.frombuffer(img_data, np.uint8)
        mat = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)
        return mat
    except Exception:
        return None

class NormalMainWindow(QMainWindow):
    search_requested = pyqtSignal(str, dict)  # (关键词, 过滤条件)
    comment_submitted = pyqtSignal(str)       # 评论内容
    navigation_requested = pyqtSignal(int)    # 切换方向(-1/1)

    def __init__(self, user_uid: str, parent=None):
        super().__init__(parent)
        self.uid = user_uid  # 当前登录用户UID
        self.user_name = None
        self.email = None
        self.setWindowTitle("地图收藏家")
        self.setMinimumSize(1000, 700)

        # 获取用户名称（如需显示）
        self._fetch_user_details()

        self._init_ui()
        self.prev_btn.clicked.connect(self._handle_prev)
        self.next_btn.clicked.connect(self._handle_next)

        # 若有当前地图就尝试刷新
        self._refresh_display()

    def _fetch_user_details(self):
        """获取并缓存用户名称"""
        try:
            resp = requests.get(f"{SERVER_URL}/user/{self.uid}/name")
            if resp.status_code == 200:
                self.user_name = resp.json().get("name", "未命名用户")
            else:
                self.user_name = "未命名用户"
        except:
            self.user_name = "未命名用户"

    def _refresh_display(self):
        """统一刷新显示"""
        try:
            # 尝试获取当前地图详情
            details_resp = requests.get(f"{SERVER_URL}/user/{self.uid}/current_map/details")
            if details_resp.status_code == 200:
                details_json = details_resp.json()
                # 解码地图图像
                b64_image = details_json.get("image", "")
                mapid = details_json.get("mapid", "")
                detail_dict = details_json.get("details", {})

                mat_data = base64_to_nparray(b64_image)
                self.update_map_display(mat_data)
                self.update_map_info(detail_dict)
            else:
                # 当前地图不存在则不更新
                pass
        except Exception as e:
            QMessageBox.warning(self, "刷新错误", f"无法刷新地图信息:\n{str(e)}")

    def _init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(self._create_left_panel())

        splitter2 = QSplitter(Qt.Horizontal, self)
        splitter2.addWidget(self._create_right_stack())
        splitter2.addWidget(self._create_map_list_panel())
        splitter2.setSizes([800, 200])

        splitter.addWidget(splitter2)
        splitter.setSizes([200, 1000])

        layout = QHBoxLayout(main_widget)
        layout.addWidget(splitter)

        self._add_toolbar()

    def _create_map_list_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        self.map_tree = QTreeWidget()
        self.map_tree.setHeaderLabel("地图类型 / 名称")
        layout.addWidget(self.map_tree)

        self.map_list_timer = QTimer(self)
        self.map_list_timer.setInterval(60000)  # 每60s更新
        self.map_list_timer.timeout.connect(self._update_map_list)
        self.map_list_timer.start()

        self._update_map_list()
        self.map_tree.itemClicked.connect(self._handle_map_item_clicked)

        return panel

    def _update_map_list(self):
        self.map_tree.clear()
        try:
            resp = requests.get(f"{SERVER_URL}/maps")
            if resp.status_code == 200:
                data = resp.json()
                map_list = data.get("maps", [])
            else:
                map_list = []
        except:
            map_list = []

        from collections import defaultdict
        type_dict = defaultdict(list)
        for m in map_list:
            mtype = m.get("map_type", "未分类")
            type_dict[mtype].append(m)

        for t in type_dict:
            type_item = QTreeWidgetItem([t])
            self.map_tree.addTopLevelItem(type_item)
            for m in type_dict[t]:
                child_item = QTreeWidgetItem([m.get("map_name", "未命名")])
                child_item.setData(0, Qt.UserRole, m.get("mapid", ""))
                type_item.addChild(child_item)
        self.map_tree.expandAll()

    def _handle_map_item_clicked(self, item, column):
        mapid = item.data(0, Qt.UserRole)
        if mapid:
            # 调用 'PUT /user/{uid}/maps/{mapid}' 仅进行 arcs={} 切换 (or use user_change_map?)
            # Actually: There's no official "set current map" endpoint except user_change_map etc.
            # We can do an empty arcs: user_change_map(uid, mapid, arcs=None)
            # Or we could attempt a different approach if you have a specific route. For now, do user_change_map:
            try:
                put_data = {"uid": self.uid, "mapid": mapid}  # 空arcs只切换地图
                requests.put(f"{SERVER_URL}/user/{self.uid}/current_map/{mapid}", json=put_data)
                self._refresh_display()
                # if resp.status_code == 200:
                #     self._refresh_display()
                # else:
                #     detail_msg = resp.json().get("detail", "切换地图失败")
                #     QMessageBox.warning(self, "切换地图失败", f"无法加载地图 {mapid}:\n{detail_msg}")
            except Exception as e:
                QMessageBox.warning(self, "切换地图失败", f"无法加载地图 {mapid}:\n{str(e)}")

    def _add_toolbar(self):
        toolbar = self.addToolBar("MainToolbar")

        menu_btn = QToolButton()
        if os.path.exists("../res/logo.png"):
            menu_btn.setIcon(QIcon("../res/logo.png"))
        menu_btn.setPopupMode(QToolButton.InstantPopup)
        menu_btn.setMenu(self._create_main_menu())
        toolbar.addWidget(menu_btn)

        if os.path.exists("../res/search_sign.png"):
            search_btn = QPushButton(QIcon("../res/search_sign.png"), "")
        else:
            search_btn = QPushButton("搜索")

        search_btn.clicked.connect(self._emit_search)
        toolbar.addWidget(search_btn)

    def _create_main_menu(self):
        menu = QMenu(self)
        menu.addAction("添加地图", self._open_add_map_dialog)
        menu.addAction("用户设置", self._open_user_settings_dialog)
        menu.addAction("地图检索", lambda: self.right_stack.setCurrentIndex(0))
        menu.addAction("地图浏览", lambda: self.right_stack.setCurrentIndex(1))
        return menu

    def _open_user_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("用户设置")
        dialog.setModal(True)

        main_layout = QVBoxLayout(dialog)

        user_name_label = QLabel(f"当前用户名: {self.user_name or ''}")
        user_email_label = QLabel(f"当前邮箱: {self.email or ''}")

        main_layout.addWidget(user_name_label)
        main_layout.addWidget(user_email_label)

        new_name_label = QLabel("新用户名：")
        new_name_edit = QLineEdit()
        new_email_label = QLabel("新邮箱地址：")
        new_email_edit = QLineEdit()

        main_layout.addWidget(new_name_label)
        main_layout.addWidget(new_name_edit)
        main_layout.addWidget(new_email_label)
        main_layout.addWidget(new_email_edit)

        btn_layout = QHBoxLayout()
        confirm_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")

        def on_confirm():
            new_name = new_name_edit.text().strip()
            if new_name:
                body = {"new_name": new_name}
                resp = requests.put(f"{SERVER_URL}/user/{self.uid}/name", json=body)
                if resp.status_code == 200:
                    QMessageBox.information(self, "成功", f"用户名已修改为: {new_name}")
                    self.user_name = new_name
                else:
                    msg = resp.json().get("detail", "未知错误")
                    QMessageBox.warning(self, "失败", f"修改用户名失败: {msg}")

            new_email = new_email_edit.text().strip()
            if new_email:
                body = {"new_email": new_email}
                resp = requests.put(f"{SERVER_URL}/user/{self.uid}/email", json=body)
                if resp.status_code == 200:
                    QMessageBox.information(self, "成功", f"邮箱已修改为: {new_email}")
                    self.email = new_email
                else:
                    msg = resp.json().get("detail", "未知错误")
                    QMessageBox.warning(self, "失败", f"修改邮箱失败: {msg}")

            dialog.close()

        def on_cancel():
            dialog.close()

        confirm_btn.clicked.connect(on_confirm)
        cancel_btn.clicked.connect(on_cancel)

        btn_layout.addWidget(confirm_btn)
        btn_layout.addWidget(cancel_btn)
        main_layout.addLayout(btn_layout)

        dialog.exec_()

    def _open_add_map_dialog(self):
        dialog = AddMapDialog(self.uid, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._refresh_display()

    def _create_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 20, 10, 20)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索关键词...")
        self.search_input.returnPressed.connect(self._emit_search)
        layout.addWidget(self.search_input)

        self.filters = {
            'name': QCheckBox("地图名称"),
            'type': QCheckBox("地图类型"),
            'media': QCheckBox("地图媒介"),
            'desc': QCheckBox("地图描述")
        }
        for cb in self.filters.values():
            layout.addWidget(cb)

        layout.addStretch()
        return panel

    def _create_right_stack(self):
        self.right_stack = QStackedWidget()
        self.right_stack.addWidget(self._create_map_view())
        self.right_stack.addWidget(self._create_comment_view())
        return self.right_stack

    def _create_map_view(self):
        view = QWidget()
        layout = QVBoxLayout(view)

        self.map_display = QLabel()
        self.map_display.setAlignment(Qt.AlignCenter)
        self.map_display.setStyleSheet("background: #f8f9fa;")
        layout.addWidget(self.map_display, 3)

        nav_bar = QHBoxLayout()
        self.prev_btn = self._create_icon_btn("../res/left_arrow.png", "上一张")
        self.next_btn = self._create_icon_btn("../res/right_arrow.png", "下一张")
        self.comment_btn = self._create_text_btn("显示评论", "#3498db")
        self.history_btn = self._create_text_btn("显示历史修改数据", "#9b59b6")  # 新增按钮

        self.prev_btn.clicked.connect(lambda: self.navigation_requested.emit(-1))
        self.next_btn.clicked.connect(lambda: self.navigation_requested.emit(1))
        self.comment_btn.clicked.connect(self._show_comments)
        self.history_btn.clicked.connect(self._show_change_history)  # 按钮点击事件

        nav_bar.addWidget(self.prev_btn)
        nav_bar.addWidget(self.comment_btn)
        nav_bar.addWidget(self.history_btn)  # 添加到导航栏
        nav_bar.addWidget(self.next_btn)
        layout.addLayout(nav_bar)

        self.info_panel = self._create_info_panel()
        layout.addWidget(self.info_panel, 1)

        return view

    def _show_change_history(self):
        """显示地图的历史修改数据"""
        try:
            url = f"{SERVER_URL}/user/{self.uid}/changes/curr"
            response = requests.get(url)

            if response.status_code == 200:
                changes = response.json().get("arcs")
                if changes:
                    dialog = ChangeHistoryDialog(changes, self)
                    dialog.exec_()
                else:
                    QMessageBox.critical(self, "info", "无任何修改信息")
            else:
                error_msg = response.json().get("detail", "未知错误")
                QMessageBox.critical(self, "错误", f"无法获取修改数据: {error_msg}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取修改数据时发生异常:\n{str(e)}")

    def _create_comment_view(self):
        view = QWidget()
        layout = QVBoxLayout(view)

        self.comment_scroll = QScrollArea()
        self.comment_content = QWidget()
        self.comment_layout = QVBoxLayout(self.comment_content)
        self.comment_scroll.setWidget(self.comment_content)
        self.comment_scroll.setWidgetResizable(True)
        layout.addWidget(self.comment_scroll)

        input_bar = QHBoxLayout()
        self.comment_input = QLineEdit()
        self.comment_input.setPlaceholderText("输入您的评论...")
        submit_btn = self._create_text_btn("发送", "#2ecc71")
        submit_btn.clicked.connect(self._submit_comment)

        input_bar.addWidget(self.comment_input, 4)
        input_bar.addWidget(submit_btn, 1)
        layout.addLayout(input_bar)

        return view

    def _load_comments(self):
        for i in reversed(range(self.comment_layout.count())):
            self.comment_layout.itemAt(i).widget().deleteLater()

        try:
            resp = requests.get(f"{SERVER_URL}/user/{self.uid}/current_map/notes")
            if resp.status_code == 200:
                notes = resp.json()
                # sort by time desc
                sorted_notes = sorted(notes, key=lambda x: x["time"], reverse=True)
                for note in sorted_notes:
                    self._add_comment_item(note["uid"], note["time"], note["context"])
            else:
                QMessageBox.critical(self, "加载失败", f"无法加载评论: {resp.text}")
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"无法加载评论:\n{str(e)}")

    def _add_comment_item(self, uid: str, time: str, content: str):
        try:
            resp = requests.get(f"{SERVER_URL}/user/{uid}/name")
            if resp.status_code == 200:
                username = resp.json().get("name", "未知用户")
            else:
                username = "未知用户"
        except:
            username = "未知用户"

        display_time = time.split("T")[0] if "T" in time else "未知时间"
        comment_frame = QFrame()
        comment_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
                margin: 5px 0;
                background: white;
            }
        """)

        layout = QVBoxLayout(comment_frame)
        user_line = QHBoxLayout()
        user_label = QLabel(f"<b>{username}</b>")
        time_label = QLabel(f"<small>{display_time}</small>")
        user_line.addWidget(user_label)
        user_line.addStretch()
        user_line.addWidget(time_label)

        content_label = QLabel(content)
        content_label.setWordWrap(True)

        layout.addLayout(user_line)
        layout.addWidget(content_label)

        self.comment_layout.addWidget(comment_frame)

    def _submit_comment(self):
        content = self.comment_input.text().strip()
        if not content:
            QMessageBox.warning(self, "输入错误", "评论内容不能为空")
            return

        body = {"note": content}
        try:
            resp = requests.post(f"{SERVER_URL}/user/{self.uid}/current_map/notes", json=body)
            if resp.status_code == 200:
                self.comment_input.clear()
                self._load_comments()
                QMessageBox.information(self, "成功", "评论已添加")
            else:
                QMessageBox.critical(self, "错误", f"评论提交失败，错误: {resp.text}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"提交评论时发生异常:\n{str(e)}")

    def _show_comments(self):
        self.right_stack.setCurrentIndex(1)
        self._load_comments()

    def _create_info_panel(self):
        panel = QScrollArea()
        panel.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)

        self.info_labels = {
            'map_name': self._create_info_row('map_name', "地图名称", "未命名"),
            'map_type': self._create_info_row('map_type', "地图类型", "未分类"),
            'media_type': self._create_info_row('media_type', "媒介类型", "未知"),
            'public_time': self._create_info_row('public_time', "发行时间", "-"),
            'collect_time': self._create_info_row('collect_time', "收录时间", "-"),
            'description': self._create_info_row('description', "地图描述", "暂无描述"),
            'stars': self._create_info_row('stars', "地图星级", "5")
        }

        for widget in self.info_labels.values():
            layout.addWidget(widget)

        panel.setWidget(content)
        return panel

    def _create_info_row(self, field_key, title, default=""):
        row = QWidget()
        layout = QHBoxLayout(row)

        title_label = QLabel(f"{title}：")
        content_label = QLabel(default)
        content_label.setObjectName(f"info_{field_key}")

        layout.addWidget(title_label)
        layout.addWidget(content_label)
        return row

    def _create_icon_btn(self, icon_path, tooltip):
        btn = QPushButton()
        if os.path.exists(icon_path):
            btn.setIcon(QIcon(icon_path))
        btn.setToolTip(tooltip)
        btn.setStyleSheet("""
            QPushButton {
                padding: 8px;
                border-radius: 4px;
                background: #e9ecef;
            }
            QPushButton:hover {
                background: #dee2e6;
            }
        """)
        return btn

    def _create_text_btn(self, text, color):
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                padding: 6px 15px;
                background: {color};
                color: white;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {self._darken_color(color)};
            }}
        """)
        return btn

    def _darken_color(self, hex_color, factor=0.15):
        hex_color = hex_color.replace('#', '')
        try:
            rgb = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
        except:
            # fallback
            return "#888888"
        darker = [max(0, int(c * (1 - factor))) for c in rgb]
        return "#{:02x}{:02x}{:02x}".format(*darker)

    def _emit_search(self):
        search_term = self.search_input.text()
        filter_status = {key: cb.isChecked() for key, cb in self.filters.items()}

        # 使用POST /user/{uid}/search
        # {
        #   "query_name": str,
        #   "query_type": str,
        #   "query_media": str,
        #   "query_desc": str,
        #   "top_n": int
        # }
        payload = {
            "query_name": search_term if filter_status['name'] else "",
            "query_type": search_term if filter_status['type'] else "",
            "query_media": search_term if filter_status['media'] else "",
            "query_desc": search_term if filter_status['desc'] else "",
            "top_n": 10
        }
        try:
            resp = requests.post(f"{SERVER_URL}/user/{self.uid}/search", json=payload)
            if resp.status_code != 200:
                err_msg = resp.json().get("detail", "搜索出现未知错误")
                QMessageBox.critical(self, "搜索错误", f"执行搜索时发生错误:\n{err_msg}")
            else:
                # 如果搜索成功，会把地图切换到最近一次搜索结果
                # 再加载当前地图
                details = requests.get(f"{SERVER_URL}/user/{self.uid}/current_map/details")
                if details.status_code == 200:
                    details_json = details.json()
                    mat = base64_to_nparray(details_json.get("image", ""))
                    self.update_map_display(mat)
                    self.update_map_info(details_json.get("details", {}))
                else:
                    pass
        except Exception as e:
            QMessageBox.critical(self, "搜索错误", f"执行搜索时发生错误:\n{str(e)}")

        filters = {k: v.isChecked() for k, v in self.filters.items()}
        self.search_requested.emit(self.search_input.text(), filters)

    def _handle_prev(self):
        # POST /user/{uid}/before
        try:
            resp = requests.post(f"{SERVER_URL}/user/{self.uid}/before")
            if resp.status_code == 200:
                self._refresh_display()
            else:
                QMessageBox.warning(self, "导航错误", f"无法切换到前一张地图:\n{resp.text}")
        except Exception as e:
            QMessageBox.warning(self, "导航错误", f"无法切换到前一张地图:\n{str(e)}")

    def _handle_next(self):
        # POST /user/{uid}/next
        try:
            resp = requests.post(f"{SERVER_URL}/user/{self.uid}/next")
            if resp.status_code == 200:
                self._refresh_display()
            else:
                QMessageBox.warning(self, "导航错误", f"无法切换到下一张地图:\n{resp.text}")
        except Exception as e:
            QMessageBox.warning(self, "导航错误", f"无法切换到下一张地图:\n{str(e)}")

    def update_map_display(self, image_data):
        if image_data is None or not isinstance(image_data, np.ndarray):
            self.map_display.clear()
            return
        h, w, ch = image_data.shape
        if ch == 3:
            fmt = QImage.Format_RGB888
            # OpenCV 默认 BGR，需要转换到 RGB
            image_data = cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB)
        else:
            fmt = QImage.Format_RGBA8888
        q_img = QImage(image_data.data, w, h, ch * w, fmt)
        pixmap = QPixmap.fromImage(q_img)
        self.map_display.setPixmap(pixmap.scaledToHeight(500, Qt.SmoothTransformation))

    def update_map_info(self, info_data: dict):
        field_mapping = [
            ('map_name', '地图名称'),
            ('map_type', '地图类型'),
            ('media_type', '媒介类型'),
            ('public_time', '发行时间'),
            ('collect_time', '收录时间'),
            ('description', '地图描述'),
            ('stars', '地图星级')
        ]
        for field_key, _ in field_mapping:
            label = self.findChild(QLabel, f"info_{field_key}")
            if label:
                label.setText(str(info_data.get(field_key, "")))


class AddMapDialog(QDialog):
    def __init__(self, uid: str, parent=None):
        super().__init__(parent)
        self.uid = uid
        self.setWindowTitle("添加地图")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        self._init_ui()
        self.preview_mat = None
        self.base64_image = None

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # 地图文件部分
        file_layout = QHBoxLayout()
        self.file_edit = QLineEdit()
        file_btn = QPushButton("选择地图文件")
        file_btn.clicked.connect(self._choose_map_file)
        file_layout.addWidget(self.file_edit)
        file_layout.addWidget(file_btn)

        self.map_preview_label = QLabel("地图预览区域")
        self.map_preview_label.setAlignment(Qt.AlignCenter)
        self.map_preview_label.setStyleSheet("background: #f2f2f2; border: 1px solid #ccc;")

        # JSON描述文件部分
        desc_layout = QHBoxLayout()
        self.desc_file_edit = QLineEdit()
        desc_btn = QPushButton("选择描述文件")
        desc_btn.clicked.connect(self._choose_desc_file)
        desc_layout.addWidget(self.desc_file_edit)
        desc_layout.addWidget(desc_btn)

        form_layout = QVBoxLayout()
        self.map_name_edit = QLineEdit()
        self.map_type_edit = QLineEdit()
        self.media_type_edit = QLineEdit()
        self.desc_edit = QLineEdit()
        self.public_time_edit = QLineEdit()

        form_layout.addWidget(QLabel("地图名称:"))
        form_layout.addWidget(self.map_name_edit)
        form_layout.addWidget(QLabel("地图类型:"))
        form_layout.addWidget(self.map_type_edit)
        form_layout.addWidget(QLabel("媒介类型:"))
        form_layout.addWidget(self.media_type_edit)
        form_layout.addWidget(QLabel("地图描述:"))
        form_layout.addWidget(self.desc_edit)
        form_layout.addWidget(QLabel("发行时间(ISO):"))
        form_layout.addWidget(self.public_time_edit)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("添加")
        cancel_btn = QPushButton("取消")

        add_btn.clicked.connect(self._handle_add_map)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(cancel_btn)

        main_layout.addLayout(file_layout)
        main_layout.addWidget(self.map_preview_label)
        main_layout.addLayout(desc_layout)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(btn_layout)

    def _choose_map_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择地图文件", "", "All Files (*)")
        if file_path:
            self.file_edit.setText(file_path)
            try:
                mat_reader = MatReader()  # 使用 MatReader
                mat_data = mat_reader.read_data(file_path)
                self.preview_mat = mat_data

                if mat_data is None:
                    self.map_preview_label.setText("无法预览该文件")
                else:
                    # 将图片数据转化为 Base64 字符串
                    _, buffer = cv2.imencode('.png', mat_data)
                    self.base64_image = base64.b64encode(buffer).decode('utf-8')

                    # 更新预览
                    h, w, ch = mat_data.shape
                    if ch == 3:
                        mat_data = cv2.cvtColor(mat_data, cv2.COLOR_BGR2RGB)
                        fmt = QImage.Format_RGB888
                    else:
                        fmt = QImage.Format_RGBA8888
                    q_img = QImage(mat_data.data, w, h, ch * w, fmt)
                    pixmap = QPixmap.fromImage(q_img)
                    self.map_preview_label.setPixmap(pixmap.scaledToHeight(200, Qt.SmoothTransformation))
            except Exception as e:
                QMessageBox.warning(self, "错误", f"加载地图文件失败: {str(e)}")

    def _choose_desc_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择地图描述文件", "", "JSON Files (*.json);;All Files (*)")
        if file_path:
            self.desc_file_edit.setText(file_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.map_name_edit.setText(data.get("map_name", ""))
                self.map_type_edit.setText(data.get("map_type", ""))
                self.media_type_edit.setText(data.get("mediatype", ""))
                self.desc_edit.setText(data.get("description", ""))
                self.public_time_edit.setText(data.get("public_time", ""))
            except Exception as e:
                QMessageBox.warning(self, "错误", f"加载描述文件失败: {str(e)}")

    def _handle_add_map(self):
        map_name = self.map_name_edit.text().strip()

        if not self.base64_image or not map_name:
            QMessageBox.warning(self, "输入不完整", "地图文件与地图名称不能为空！")
            return

        # 调用添加地图的 API
        try:
            add_map_payload = {
                "map_name": map_name,
                "file": self.base64_image
            }
            resp = requests.post(f"{SERVER_URL}/maps", json=add_map_payload)
            if resp.status_code == 200:
                result = resp.json()
                map_id = result.get("mapid", "")
                requests.put(f"{SERVER_URL}/user/{self.uid}/current_map/{map_id}")

                # 调用修改地图信息的 API
                self._update_map_info(map_id)
            else:
                detail_msg = resp.json().get("detail", "未知错误")
                QMessageBox.critical(self, "错误", f"添加地图失败: {detail_msg}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加地图时发生异常:\n{str(e)}")

    def _update_map_info(self, map_id):
        map_type = self.map_type_edit.text().strip()
        media_type = self.media_type_edit.text().strip()
        description = self.desc_edit.text().strip()
        public_time = self.public_time_edit.text().strip()

        # 调用更新地图信息的 API
        try:
            update_payload = {
                "map_type": map_type,
                "media_type": media_type,
                "description": description,
                "public_time": public_time
            }
            resp = requests.put(f"{SERVER_URL}/user/{self.uid}/maps/{map_id}", json=update_payload)
            if resp.status_code == 200:
                QMessageBox.information(self, "成功", "地图已成功添加并更新信息")
                self.accept()
            else:
                detail_msg = resp.json().get("detail", "未知错误")
                QMessageBox.warning(self, "警告", f"更新地图信息失败: {detail_msg}")
        except Exception as e:
            QMessageBox.warning(self, "警告", f"更新地图信息失败: {str(e)}")

class ChangeHistoryDialog(QDialog):
    def __init__(self, changes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("地图修改历史")
        self.setMinimumSize(800, 400)
        self._init_ui(changes)

    def _init_ui(self, changes):
        layout = QVBoxLayout(self)

        # 表格标题
        title = QLabel("地图修改历史记录")
        title.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        layout.addWidget(title)

        # 表格
        table = QTableWidget()
        table.setColumnCount(6)  # 设置列数
        table.setHorizontalHeaderLabels([
            "用户名", "地图名称", "修改时间", "新地图名称", "新地图类型", "新媒介类型"
        ])
        layout.addWidget(table)

        # 填充表格数据
        changes.sort(key=lambda x: x["change_time"], reverse=True)  # 按修改时间排序
        table.setRowCount(len(changes))

        for row, change in enumerate(changes):
            table.setItem(row, 0, QTableWidgetItem(change.get("user_name", "未知用户")))
            table.setItem(row, 1, QTableWidgetItem(change.get("map_name", "未知地图")))
            table.setItem(row, 2, QTableWidgetItem(change.get("change_time", "")))
            table.setItem(row, 3, QTableWidgetItem(change.get("new_map_name", "")))
            table.setItem(row, 4, QTableWidgetItem(change.get("new_map_type", "")))
            table.setItem(row, 5, QTableWidgetItem(change.get("new_media_type", "")))

        # 设置表格属性
        table.resizeColumnsToContents()
        table.resizeRowsToContents()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 假设你在登陆后获取了一个 uid="test_user"
    uid = "test_user"
    win = NormalMainWindow(user_uid=uid)
    win.show()
    sys.exit(app.exec_())