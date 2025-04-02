from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QToolButton, QMenu, QLineEdit, QCheckBox,
    QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QSplitter,
    QScrollArea, QFrame, QStackedWidget, QTextEdit, QSizePolicy, QMessageBox,
    QTreeWidget, QTreeWidgetItem, QDialog, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QFont, QImage

from api.base_api import UserServer, NormalUser, SuperUser, UserView, MapServer
from api.base_api import trace, info, warn, error, fatal
import numpy as np
import cv2
import json
from collections import defaultdict
from typing import Tuple, Optional, Dict


class NormalMainWindow(QMainWindow):
    # 界面操作信号
    search_requested = pyqtSignal(str, dict)  # (关键词, 过滤条件)
    comment_submitted = pyqtSignal(str)       # 评论内容
    navigation_requested = pyqtSignal(int)    # 切换方向(-1/1)

    def __init__(self, user_server: UserServer, map_server: MapServer, current_user: NormalUser, signals):
        super().__init__()
        self.user_server = user_server
        self.map_server = map_server
        self.current_user = current_user
        self.setWindowTitle("地图收藏家")
        self.setMinimumSize(1000, 700)

        self._init_ui()
        self.prev_btn.clicked.connect(self._handle_prev)
        self.next_btn.clicked.connect(self._handle_next)

        # 如果有当前地图，则先刷新显示
        if self.current_user.current_map:
            self._refresh_display()

    def _refresh_display(self):
        """统一刷新显示"""
        try:
            image_data, info_dict = self.current_user.get_map_details_now()
            self.update_map_display(image_data)
            self.update_map_info(info_dict)
        except Exception as e:
            QMessageBox.warning(self, "刷新错误", f"无法刷新地图信息:\n{str(e)}")

    def _init_ui(self):
        # 主窗口布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 整体分割布局 (左侧筛选 + 右侧区域)
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(self._create_left_panel())

        # 在右侧，再创建一个splitter，将主堆叠页面和地图类型列表各分一块
        splitter2 = QSplitter(Qt.Horizontal, self)
        splitter2.addWidget(self._create_right_stack())
        splitter2.addWidget(self._create_map_list_panel())
        splitter2.setSizes([800, 200])

        splitter.addWidget(splitter2)
        splitter.setSizes([200, 1000])

        layout = QHBoxLayout(main_widget)
        layout.addWidget(splitter)

        # 顶部工具栏
        self._add_toolbar()

    def _create_map_list_panel(self):
        """
        创建右侧地图类型树状列表面板，
        每60s更新一次，以适应map_server的变化
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        self.map_tree = QTreeWidget()
        self.map_tree.setHeaderLabel("地图类型 / 名称")
        layout.addWidget(self.map_tree)

        self.map_list_timer = QTimer(self)
        self.map_list_timer.setInterval(6000)  # 1s
        self.map_list_timer.timeout.connect(self._update_map_list)
        self.map_list_timer.start()

        self._update_map_list()
        self.map_tree.itemClicked.connect(self._handle_map_item_clicked)

        return panel

    def _update_map_list(self):
        """从map_server获取地图列表，根据map_type进行分组，再更新树结构"""
        self.map_tree.clear()
        map_list = self.map_server.get_map_list()

        type_dict = defaultdict(list)
        for m in map_list:
            type_dict[m["map_type"]].append(m)

        for t in type_dict:
            type_item = QTreeWidgetItem([t])
            self.map_tree.addTopLevelItem(type_item)
            for m in type_dict[t]:
                child_item = QTreeWidgetItem([m["map_name"]])
                child_item.setData(0, Qt.UserRole, m["mapid"])
                type_item.addChild(child_item)

        self.map_tree.expandAll()

    def _handle_map_item_clicked(self, item, column):
        """处理单击地图节点"""
        mapid = item.data(0, Qt.UserRole)
        if mapid:
            try:
                self.current_user.set_current_map(str(mapid))
                self._refresh_display()
            except Exception as e:
                QMessageBox.warning(self, "切换地图失败", f"无法加载地图 {mapid}:\n{str(e)}")

    def _add_toolbar(self):
        """创建顶部工具栏"""
        toolbar = self.addToolBar("MainToolbar")

        # 菜单按钮
        menu_btn = QToolButton()
        menu_btn.setIcon(QIcon("../res/logo.png"))
        menu_btn.setPopupMode(QToolButton.InstantPopup)
        menu_btn.setMenu(self._create_main_menu())
        toolbar.addWidget(menu_btn)

        # 搜索按钮
        search_btn = QPushButton(QIcon("../res/search_sign.png"), "")
        search_btn.clicked.connect(self._emit_search)
        toolbar.addWidget(search_btn)

    def _create_main_menu(self):
        """创建主菜单"""
        menu = QMenu(self)
        menu.addAction("添加地图", self._open_add_map_dialog)
        menu.addAction("用户设置", self._open_user_settings_dialog)
        menu.addAction("地图检索", lambda: self.right_stack.setCurrentIndex(0))
        menu.addAction("地图浏览", lambda: self.right_stack.setCurrentIndex(1))
        return menu

    def _open_user_settings_dialog(self):
        """弹出用户设置对话框，显示并允许修改用户名称和邮箱"""
        dialog = QDialog(self)
        dialog.setWindowTitle("用户设置")
        dialog.setModal(True)

        main_layout = QVBoxLayout(dialog)

        # 当前用户名、邮箱标签
        user_name_label = QLabel(f"当前用户名: {self.current_user.details.get('user_name', '')}")
        user_email_label = QLabel(f"当前邮箱: {self.current_user.details.get('user_email', '')}")

        main_layout.addWidget(user_name_label)
        main_layout.addWidget(user_email_label)

        # 输入框
        new_name_label = QLabel("新用户名：")
        new_name_edit = QLineEdit()
        new_email_label = QLabel("新邮箱地址：")
        new_email_edit = QLineEdit()

        main_layout.addWidget(new_name_label)
        main_layout.addWidget(new_name_edit)
        main_layout.addWidget(new_email_label)
        main_layout.addWidget(new_email_edit)

        # 按钮
        btn_layout = QHBoxLayout()
        confirm_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")

        def on_confirm():
            # 更新用户名
            new_name = new_name_edit.text().strip()
            if new_name:
                result = self.current_user.reset_user_name(new_name)
                if result == 0:
                    QMessageBox.information(self, "成功", f"用户名已修改为: {new_name}")
                elif result == 1016:
                    QMessageBox.warning(self, "失败", "修改用户名失败，错误码1016")
                else:
                    QMessageBox.warning(self, "失败", f"修改用户名返回未知错误码: {result}")

            # 更新邮箱
            new_email = new_email_edit.text().strip()
            if new_email:
                result = self.current_user.reset_user_email(new_email)
                if result == 0:
                    QMessageBox.information(self, "成功", f"邮箱已修改为: {new_email}")
                elif result == 2002:
                    QMessageBox.warning(self, "失败", "该邮箱已存在，错误码2002")
                elif result == 1016:
                    QMessageBox.warning(self, "失败", "修改邮箱失败，错误码1016")
                else:
                    QMessageBox.warning(self, "失败", f"修改邮箱返回未知错误码: {result}")

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
        """添加地图：弹出对话框，支持选择地图文件、json描述文件，预览并编辑后添加"""
        dialog = AddMapDialog(self.map_server, self.current_user, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            # 若添加成功，刷新主界面
            self._refresh_display()

    def _create_left_panel(self):
        """左侧筛选面板"""
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
        """右侧堆叠视图"""
        self.right_stack = QStackedWidget()
        self.right_stack.addWidget(self._create_map_view())
        self.right_stack.addWidget(self._create_comment_view())
        return self.right_stack

    def _create_map_view(self):
        """地图浏览视图"""
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

        self.prev_btn.clicked.connect(lambda: self.navigation_requested.emit(-1))
        self.next_btn.clicked.connect(lambda: self.navigation_requested.emit(1))
        self.comment_btn.clicked.connect(self._show_comments)

        nav_bar.addWidget(self.prev_btn)
        nav_bar.addWidget(self.comment_btn)
        nav_bar.addWidget(self.next_btn)
        layout.addLayout(nav_bar)

        self.info_panel = self._create_info_panel()
        layout.addWidget(self.info_panel, 1)

        return view

    def _create_comment_view(self):
        """评论交互视图"""
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
        """加载当前地图的评论"""
        for i in reversed(range(self.comment_layout.count())):
            self.comment_layout.itemAt(i).widget().deleteLater()

        try:
            notes = self.current_user.get_notes_of_current_map()
            sorted_notes = sorted(notes, key=lambda x: x["time"], reverse=True)
            for note in sorted_notes:
                self._add_comment_item(
                    uid=note["uid"],
                    time=note["time"],
                    content=note["context"]
                )
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"无法加载评论:\n{str(e)}")

    def _add_comment_item(self, uid: str, time: str, content: str):
        """添加单个评论项"""
        try:
            username = self.user_server.get_user_name(uid)
        except Exception as e:
            username = "未知用户"
            error(f"获取用户名称失败: {str(e)}")

        display_time = "未知时间"
        if "T" in time:
            display_time = time.split("T")[0]

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
        """提交评论处理"""
        content = self.comment_input.text().strip()
        if not content:
            QMessageBox.warning(self, "输入错误", "评论内容不能为空")
            return

        try:
            result = self.current_user.write_note(content)
            if result == 0:
                self.comment_input.clear()
                self._load_comments()
                QMessageBox.information(self, "成功", "评论已添加")
            else:
                QMessageBox.critical(self, "错误", f"评论提交失败，错误码: {result}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"提交评论时发生异常:\n{str(e)}")

    def _show_comments(self):
        """显示评论视图并加载数据"""
        self.right_stack.setCurrentIndex(1)
        self._load_comments()

    def _create_info_panel(self):
        """创建元信息面板"""
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
        btn = QPushButton(QIcon(icon_path), "")
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
        rgb = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]
        darker = [max(0, int(c * (1 - factor))) for c in rgb]
        return "#{:02x}{:02x}{:02x}".format(*darker)

    def _emit_search(self):
        """触发搜索信号"""
        search_term = self.search_input.text()
        filter_status = {key: cb.isChecked() for key, cb in self.filters.items()}

        try:
            self.current_user.search(
                query_name=search_term if filter_status['name'] else "",
                query_type=search_term if filter_status['type'] else "",
                query_media=search_term if filter_status['media'] else "",
                query_desc=search_term if filter_status['desc'] else ""
            )
            mat_data, details = self.current_user.get_map_details_now()
            self.update_map_display(mat_data)
            self.update_map_info(details)
        except Exception as e:
            QMessageBox.critical(self, "搜索错误", f"执行搜索时发生错误:\n{str(e)}")

        filters = {k: v.isChecked() for k, v in self.filters.items()}
        self.search_requested.emit(self.search_input.text(), filters)

    def _handle_prev(self):
        """向左导航处理"""
        try:
            self.current_user.before()
            self._refresh_display()
        except Exception as e:
            QMessageBox.warning(self, "导航错误", f"无法切换到前一张地图:\n{str(e)}")

    def _handle_next(self):
        """向右导航处理"""
        try:
            self.current_user.next()
            self._refresh_display()
        except Exception as e:
            QMessageBox.warning(self, "导航错误", f"无法切换到下一张地图:\n{str(e)}")

    # ==== 用户需要调用的更新接口 ====
    def update_map_display(self, image_data):
        """
        更新地图显示
        参数：numpy数组或QPixmap
        """
        if isinstance(image_data, QPixmap):
            pixmap = image_data
        else:
            h, w, ch = image_data.shape
            fmt = QImage.Format_RGB888 if ch == 3 else QImage.Format_RGBA8888
            q_img = QImage(image_data.data, w, h, ch * w, fmt)
            pixmap = QPixmap.fromImage(q_img)

        self.map_display.setPixmap(pixmap.scaledToHeight(500, Qt.SmoothTransformation))

    def update_map_info(self, info_data: dict):
        """更新地图元信息"""
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

    def add_comment(self, author: str, timestamp: str, content: str):
        """添加新评论"""
        comment_frame = QFrame()
        comment_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
                margin: 5px 0;
            }
        """)
        layout = QVBoxLayout(comment_frame)
        layout.addWidget(QLabel(f"<b>{author}</b> <small>{timestamp}</small>"))
        layout.addWidget(QLabel(content))
        self.comment_layout.addWidget(comment_frame)


class AddMapDialog(QDialog):
    """
    添加地图对话框，其中允许用户选择地图文件、json描述文件，并可进行预览及信息编辑
    """
    def __init__(self, map_server: MapServer, current_user: NormalUser, parent=None):
        super().__init__(parent)
        self.map_server = map_server
        self.current_user = current_user
        self.setWindowTitle("添加地图")
        self.setModal(True)
        self.setMinimumSize(600, 400)

        self._init_ui()

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

        # 地图信息输入区
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

        # 按钮区
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
        """选择地图文件，并预览"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择地图文件", "", "All Files (*)")
        if file_path:
            self.file_edit.setText(file_path)
            try:
                mat_data = self.map_server.load_mat(file_path)
                # 预览图加载
                if isinstance(mat_data, np.ndarray):
                    h, w, ch = mat_data.shape
                    fmt = QImage.Format_RGB888 if ch == 3 else QImage.Format_RGBA8888
                    q_img = QImage(mat_data.data, w, h, ch * w, fmt)
                    pixmap = QPixmap.fromImage(q_img)
                    self.map_preview_label.setPixmap(pixmap.scaledToHeight(200, Qt.SmoothTransformation))
                else:
                    self.map_preview_label.setText("无法预览该文件")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"加载地图文件失败: {str(e)}")

    def _choose_desc_file(self):
        """选择json描述文件，并填充各输入框"""
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
        """点击添加按钮后，整合数据并调用map_server接口"""
        file_path = self.file_edit.text().strip()
        map_name = self.map_name_edit.text().strip()
        map_type = self.map_type_edit.text().strip()
        media_type = self.media_type_edit.text().strip()
        description = self.desc_edit.text().strip()
        public_time = self.public_time_edit.text().strip()

        if not file_path or not map_name:
            QMessageBox.warning(self, "输入不完整", "地图文件与地图名称不能为空！")
            return

        # 添加到服务器
        try:
            status, map_id = self.map_server.add_map(file_path, map_name)
            if status != 0:
                QMessageBox.critical(self, "错误", f"添加地图失败，状态码: {status}")
                return
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加地图时发生异常:\n{str(e)}")
            return

        # 构建地图信息
        details_dict = {
            "map_name": map_name,
            "map_type": map_type,
            "media_type": media_type,
            "description": description,
            "public_time": public_time
        }

        # 更新地图信息
        try:
            change_status = self.map_server.change_map(map_id, arcs=details_dict)
            if change_status != 0:
                QMessageBox.critical(self, "错误", f"更新地图信息失败，状态码: {change_status}")
                return
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新地图信息时发生异常:\n{str(e)}")
            return

        # 切换当前地图并关闭
        try:
            self.current_user.set_current_map(map_id)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"设置当前地图失败: {str(e)}")

        self.accept()