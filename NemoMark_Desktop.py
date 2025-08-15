import sys
import os
import json
import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem,
                            QSplitter, QTextEdit, QTreeWidget, QTreeWidgetItem, QMenuBar, 
                            QMenu, QDialog, QFormLayout, QMessageBox, QFileDialog,
                            QToolBar, QInputDialog, QFrame, QGridLayout)
from PySide6.QtGui import QAction, QFont, QIcon, QTextCursor, QDesktopServices
from PySide6.QtCore import Qt, QSize, QUrl, QFile, QIODevice, QTextStream, QDateTime
import shutil
import markdown

# 软件基本信息
APP_NAME = "NemoMark"   
APP_VERSION = "Alpha-0.1_Release"
RELEASE_DATE = "2023-10-01"
APP_WEBSITE = "https://example.com/marknote"
GITEE_REPO = "https://gitee.com/kisina/nemo-mark"
QQ_GROUP = "https://qm.qq.com/q/uOvY1UZFqo"

class MarkdownEditor(QWidget):
    """Markdown编辑器组件，包含目录树、编辑区和预览区"""
    def __init__(self, file_path=None, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.is_modified = False
        
        # 初始化UI
        self.init_ui()
        
        # 如果有文件路径，加载文件内容
        if self.file_path and os.path.exists(self.file_path):
            self.load_file()
    
    def init_ui(self):
        # 主布局 - 保持垂直布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 添加这一行
        
        # 创建分隔器
        splitter1 = QSplitter(Qt.Orientation.Horizontal)
        splitter2 = QSplitter(Qt.Orientation.Horizontal)
        
        # 目录树
        self.toc_tree = QTreeWidget()
        self.toc_tree.setHeaderLabel("目录")
        self.toc_tree.setMinimumWidth(150)
        self.toc_tree.setMaximumWidth(250)
        
        # 编辑区
        self.editor = QTextEdit()
        self.editor.setAcceptRichText(False)
        self.editor.textChanged.connect(self.update_preview)
        self.editor.textChanged.connect(self.set_modified)
        
        # 预览区
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        
        # 添加到分隔器
        splitter1.addWidget(self.toc_tree)
        splitter2.addWidget(self.editor)
        splitter2.addWidget(self.preview)
        splitter1.addWidget(splitter2)
        
        # 设置分隔器比例
        splitter1.setSizes([200, 800])
        splitter2.setSizes([400, 400])
        
        # 创建快捷工具栏
        self.create_toolbar()
        
        # 主布局 - 先添加工具栏，再添加分隔器
        main_layout.addWidget(self.toolbar)
        main_layout.addWidget(splitter1)
        
        self.setLayout(main_layout)
    
    def create_toolbar(self):
        """创建Markdown快捷指令栏"""
        self.toolbar = QToolBar("Markdown Tools")
        self.toolbar.setIconSize(QSize(18, 18))
        self.toolbar.setStyleSheet(
            """
            QToolBar {background-color: white; border: 1px solid #e0e0e0; border-radius: 6px;}
            QPushButton {min-width: 24px; min-height: 36px; text-align: center; background-color: white; border: none; color: black;}
            QPushButton:hover {box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);}
            QPushButton:pressed {box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);}
            """)
        
        # 使用图标替代文本按钮
        self.add_tool_button("H1", "# ", "一级标题")
        self.add_tool_button("H2", "## ", "二级标题")
        self.add_tool_button("H3", "### ", "三级标题")
        
        self.toolbar.addSeparator()
        
        self.add_tool_button("B", "**", "加粗")
        self.add_tool_button("I", "*", "斜体")
        self.add_tool_button("S", "~~", "删除线")
        
        self.toolbar.addSeparator()
        
        self.add_tool_button("UL", "- ", "无序列表")
        self.add_tool_button("OL", "1. ", "有序列表")
        
        self.toolbar.addSeparator()
        
        self.add_tool_button("Link", "[链接文本](URL)", "链接")
        self.add_tool_button("Img", "![图片描述](URL)", "图片")
        
        self.toolbar.addSeparator()
        
        self.add_tool_button("Code", "```\n代码\n```", "代码块")
        self.add_tool_button("Quote", "> ", "引用")
        self.add_tool_button("HR", "---", "水平线")
    
    def add_tool_button(self, text, markdown_text, tooltip):
        """添加工具按钮到工具栏"""
        button = QPushButton(text)
        button.setToolTip(tooltip)
        button.clicked.connect(lambda: self.insert_markdown(markdown_text))
        self.toolbar.addWidget(button)
    
    def insert_markdown(self, text):
        """在编辑器中插入Markdown格式文本"""
        cursor = self.editor.textCursor()
        
        # 对于需要选择文本的格式（如加粗、斜体）
        if text in ["**", "*", "~~"]:
            if cursor.hasSelection():
                selected_text = cursor.selectedText()
                cursor.insertText(f"{text}{selected_text}{text}")
            else:
                cursor.insertText(text)
                # 移动光标到中间
                cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, len(text))
                self.editor.setTextCursor(cursor)
        else:
            cursor.insertText(text)
            
            # 对于有换行的内容，将光标移动到合适位置
            if "\n" in text:
                lines = text.split("\n")
                if len(lines) > 1:
                    cursor.movePosition(QTextCursor.MoveOperation.Up, QTextCursor.MoveMode.MoveAnchor, len(lines)-1)
                    cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.MoveAnchor)
                    self.editor.setTextCursor(cursor)
    
    def update_preview(self):
        """更新预览区内容"""
        text = self.editor.toPlainText()
        html = markdown.markdown(text)
        self.preview.setHtml(html)
        self.update_toc(text)
    
    def update_toc(self, text):
        """更新目录树"""
        self.toc_tree.clear()
        lines = text.split("\n")
        headers = []
        
        # 提取所有标题
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith("#"):
                level = 0
                while level < len(stripped_line) and stripped_line[level] == "#":
                    level += 1
                if level > 0 and level <= 6:
                    title = stripped_line[level:].strip()
                    headers.append((level, title, lines.index(line)))
        
        # 构建目录树
        nodes = {0: self.toc_tree.invisibleRootItem()}
        for level, title, line_num in headers:
            item = QTreeWidgetItem([title])
            item.setData(0, Qt.ItemDataRole.UserRole, line_num)
            # 移除这一行：item.clicked.connect(...)
            
            # 找到父节点
            parent_level = level - 1
            while parent_level not in nodes and parent_level > 0:
                parent_level -= 1
            
            nodes[parent_level].addChild(item)
            nodes[level] = item

        # 添加这段代码以连接 itemClicked 信号
        self.toc_tree.itemClicked.connect(lambda item, column: self.jump_to_line(item.data(0, Qt.ItemDataRole.UserRole)))
    
    def jump_to_line(self, line_num):
        """跳转到指定行"""
        cursor = self.editor.textCursor()
        block = self.editor.document().findBlockByLineNumber(line_num)
        if block.isValid():
            cursor.setPosition(block.position())
            self.editor.setTextCursor(cursor)
            self.editor.setFocus()
    
    def load_file(self):
        """加载文件内容"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.editor.setPlainText(content)
                self.is_modified = False
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法加载文件: {str(e)}")
    
    def save_file(self, file_path=None):
        """保存文件内容"""
        if file_path:
            self.file_path = file_path
        
        if not self.file_path:
            return False
        
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            self.is_modified = False
            return True
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法保存文件: {str(e)}")
            return False
    
    def set_modified(self):
        """设置文件为已修改状态"""
        self.is_modified = True
        # 通知主窗口更新标签标题
        if self.parent() and hasattr(self.parent(), 'update_tab_title'):
            index = self.parent().indexOf(self)
            self.parent().update_tab_title(index)


class HomeWidget(QWidget):
    """主页组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # 创建顶部区域
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 标题
        title_label = QLabel("NemoMark")
        title_font = QFont()
        title_font.setPointSize(36)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #4a90e2;")
        
        # 副标题
        subtitle_label = QLabel("现代化Markdown笔记应用")
        subtitle_font = QFont()
        subtitle_font.setPointSize(16)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #7f8c8d;")
        
        top_layout.addWidget(title_label)
        top_layout.addWidget(subtitle_label)
        
        # 创建中间内容区域
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # 左侧功能卡片区域
        features_widget = QWidget()
        features_layout = QGridLayout(features_widget)
        features_layout.setSpacing(20)
        
        # 功能卡片1: 创建笔记本
        create_notebook_card = self.create_feature_card(
            "创建笔记本", 
            "开始一个新的笔记本项目",
            QIcon.fromTheme("document-new", QIcon()),
            self.parent.create_new_notebook
        )
        
        # 功能卡片2: 新建文档
        create_doc_card = self.create_feature_card(
            "新建文档", 
            "创建一篇新的Markdown文档",
            QIcon.fromTheme("text-x-markdown", QIcon()),
            self.parent.create_new_document
        )
        
        # 功能卡片3: 打开笔记本
        open_notebook_card = self.create_feature_card(
            "打开笔记本", 
            "打开已有的笔记本项目",
            QIcon.fromTheme("folder-open", QIcon()),
            self.parent.open_notebook
        )
        
        # 功能卡片4: 打开文档
        open_doc_card = self.create_feature_card(
            "打开文档", 
            "打开已有的Markdown文件",
            QIcon.fromTheme("file-open", QIcon()),
            self.parent.open_document
        )
        
        # 添加卡片到布局
        features_layout.addWidget(create_notebook_card, 0, 0)
        features_layout.addWidget(create_doc_card, 0, 1)
        features_layout.addWidget(open_notebook_card, 1, 0)
        features_layout.addWidget(open_doc_card, 1, 1)
        
        # 右侧最近使用区域
        recent_widget = QWidget()
        recent_layout = QVBoxLayout(recent_widget)
        recent_layout.setSpacing(15)
        
        # 标题
        recent_title = QLabel("最近使用")
        recent_title_font = QFont()
        recent_title_font.setPointSize(16)
        recent_title_font.setBold(True)
        recent_title.setFont(recent_title_font)
        recent_title.setStyleSheet("color: #333333; border-bottom: 1px solid #e0e0e0; padding-bottom: 5px;")
        
        # 最近笔记本列表
        recent_notebooks_label = QLabel("最近笔记本")
        recent_notebooks_label.setStyleSheet("color: #555555; font-weight: bold;")
        
        self.recent_notebooks_list = QListWidget()
        self.recent_notebooks_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:hover {
                background-color: #f0f7ff;
            }
        """)
        
        # 填充最近笔记本数据
        self.update_recent_notebooks()
        
        # 最近文档列表
        recent_docs_label = QLabel("最近文档")
        recent_docs_label.setStyleSheet("color: #555555; font-weight: bold;")
        
        self.recent_docs_list = QListWidget()
        self.recent_docs_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:hover {
                background-color: #f0f7ff;
            }
        """)
        
        # 填充最近文档数据
        self.update_recent_docs()
        
        recent_layout.addWidget(recent_title)
        recent_layout.addWidget(recent_notebooks_label)
        recent_layout.addWidget(self.recent_notebooks_list)
        recent_layout.addWidget(recent_docs_label)
        recent_layout.addWidget(self.recent_docs_list)
        recent_layout.addStretch()
        
        # 添加左右区域到内容布局
        content_layout.addWidget(features_widget, 1)
        content_layout.addWidget(recent_widget, 1)
        
        # 创建底部区域
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        
        # 版权信息
        copyright_label = QLabel(f"© {datetime.datetime.now().year} NemoMark. 版本 {APP_VERSION}")
        copyright_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        
        # 链接
        links_label = QLabel(f'<a href="{APP_WEBSITE}">官方网站</a> | <a href="{GITEE_REPO}">Gitee仓库</a>')
        links_label.setOpenExternalLinks(True)
        links_label.setStyleSheet("color: #4a90e2; font-size: 12px;")
        
        bottom_layout.addWidget(copyright_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(links_label)
        
        # 添加所有区域到主布局
        main_layout.addWidget(top_widget)
        main_layout.addWidget(content_widget)
        main_layout.addWidget(bottom_widget)
    
    def create_feature_card(self, title, description, icon, callback):
        """创建功能卡片"""
        card = QFrame()  # 改为QFrame
        card.setObjectName("FeatureCard")  # 设置对象名称以应用全局样式
        card.setMinimumHeight(150)
        # 移除内联样式，使用全局样式表
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # 图标
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(QSize(48, 48)))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 标题
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #333333;")
        
        # 描述
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #7f8c8d;")
        desc_label.setWordWrap(True)
        
        # 按钮
        btn = QPushButton("开始")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border-radius: 6px;
                padding: 6px 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #357ac0;
            }
        """)
        btn.clicked.connect(callback)
        
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return card
    
    def update_recent_notebooks(self):
        """更新最近笔记本列表"""
        self.recent_notebooks_list.clear()
        # 使用父窗口的recent_notebooks数据
        for notebook_path in self.parent.recent_notebooks[:5]:  # 只显示最近5个
            item = QListWidgetItem(os.path.basename(notebook_path))
            item.setData(Qt.ItemDataRole.UserRole, notebook_path)
            self.recent_notebooks_list.addItem(item)
        
        # 连接双击事件
        self.recent_notebooks_list.itemDoubleClicked.connect(
            lambda item: self.parent.open_notebook(item.data(Qt.ItemDataRole.UserRole))
        )
    
    def update_recent_docs(self):
        """更新最近文档列表"""
        self.recent_docs_list.clear()
        # 这里需要实现从设置或历史记录中加载最近文档
        # 为了演示，我们添加一些示例项目
        sample_docs = [
            "README.md",
            "笔记1.md",
            "项目计划.md",
            "会议记录.md"
        ]
        
        for doc in sample_docs:
            item = QListWidgetItem(doc)
            self.recent_docs_list.addItem(item)

    
    def open_recent_notebook(self, item):
        """打开最近使用的笔记本"""
        notebook_path = item.toolTip()
        self.parent.open_notebook(notebook_path)

class CustomTabWidget(QTabWidget):
    """自定义标签页组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        
        # 主页标签不能关闭
        self.home_tab_index = -1
    
    def set_home_tab(self, index):
        """设置主页标签"""
        self.home_tab_index = index
    
    def close_tab(self, index):
        """关闭标签页"""
        if index == self.home_tab_index:
            return  # 不能关闭主页标签
        
        # 检查是否有未保存的更改
        widget = self.widget(index)
        if hasattr(widget, 'is_modified') and widget.is_modified:
            reply = QMessageBox.question(self, "保存更改", 
                                        "文档已修改，是否保存更改？",
                                        QMessageBox.StandardButton.Save | 
                                        QMessageBox.StandardButton.Discard | 
                                        QMessageBox.StandardButton.Cancel)
            
            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Save:
                if hasattr(widget, 'save_file'):
                    if not widget.save_file():
                        # 如果保存失败，尝试另存为
                        file_path, _ = QFileDialog.getSaveFileName(self, "另存为", "", "Markdown文件 (*.md)")
                        if file_path and not widget.save_file(file_path):
                            return
        
        # 关闭标签
        self.removeTab(index)
    
    def update_tab_title(self, index):
        """更新标签标题，添加*表示已修改"""
        if index == self.home_tab_index:
            return
            
        widget = self.widget(index)
        if hasattr(widget, 'is_modified') and widget.is_modified:
            original_title = self.tabText(index).replace("*", "")
            self.setTabText(index, f"{original_title}*")
        else:
            self.setTabText(index, self.tabText(index).replace("*", ""))

class AboutDialog(QDialog):
    """关于对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.setMinimumSize(300, 200)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        qq_label = QLabel("加入QQ群: 123456789")
        qq_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qq_label.setWordWrap(True)
        layout.addWidget(qq_label)
        qq_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label = QLabel(f"<h1>{APP_NAME}</h1>")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        version_label = QLabel(f"版本: {APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        date_label = QLabel(f"发行日期: {RELEASE_DATE}")
        date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 描述
        desc_label = QLabel("一个最新出炉的Markdown笔记软件。")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)


        
        # 链接
        website_label = QLabel(f'<a href="{APP_WEBSITE}">官方网站</a>')
        website_label.setOpenExternalLinks(True)
        website_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        github_label = QLabel(f'<a href="{GITEE_REPO}">Gitee仓库</a>')
        github_label.setOpenExternalLinks(True)
        github_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        qq_group_label = QLabel(f'<a href="{QQ_GROUP}">加入QQ群</a>')
        qq_group_label.setOpenExternalLinks(True)
        qq_group_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(qq_label)
        layout.addWidget(name_label)
        layout.addWidget(version_label)
        layout.addWidget(date_label)
        layout.addSpacing(20)
        layout.addWidget(desc_label)
        layout.addSpacing(20)
        layout.addWidget(website_label)
        layout.addWidget(github_label)
        layout.addStretch()
        
        self.setLayout(layout)

class MarkdownNotebook(QMainWindow):
    """主窗口类"""
    def __init__(self):
        super().__init__()
        self.recent_notebooks = []
        self.load_settings()
        self.init_ui()
    
    def init_ui(self):
        # 设置窗口
        self.setWindowTitle("NemoMark")
        self.setGeometry(100, 100, 1200, 800)
        
        # 添加全局样式表
        self.setStyleSheet("""
            /* 全局样式 */
            QWidget {
                background-color: #f5f7fa;
                color: #333333;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            /* 按钮样式 */
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border-radius: 6px;
                padding: 6px 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #357ac0;
            }
            QPushButton:pressed {
                background-color: #2d68a8;
            }
            
            /* 标签页样式 */
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                color: #555555;
                padding: 8px 16px;
                border-radius: 0;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #4a90e2;
                border-top: 3px solid #4a90e2;
                font-weight: bold;
            }
            
            /* 卡片样式（在HomeWidget类中） */
            QFrame#FeatureCard {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
                padding: 10px;
            }
            QFrame#FeatureCard:hover {
                border: 1px solid #4a90e2;
                background-color: #f9fbff;
            }
            
            /* 工具栏样式 */
            QToolBar {
                background-color: white;
                border-bottom: 1px solid #e0e0e0;
                padding: 6px;
                spacing: 6px;
            }
            
            /* 文本编辑区样式 */
            QTextEdit {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
            }
            
            /* 树状组件样式 */
            QTreeWidget {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
                padding: 4px;
            }
            QTreeWidget::item:hover {
                background-color: #f0f7ff;
            }
            QTreeWidget::item:selected {
                background-color: #e1effe;
                color: #4a90e2;
            }
            
            /* 列表组件样式 */
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
                padding: 4px;
            }
            QListWidget::item:hover {
                background-color: #f0f7ff;
            }
            QListWidget::item:selected {
                background-color: #e1effe;
                color: #4a90e2;
            }
        """)
        
        # 创建中心部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # 添加这一行
        
        # 创建标签页组件
        self.tab_widget = CustomTabWidget(self)
        self.main_layout.addWidget(self.tab_widget)

        




        # 将水印布局添加到主布局
        

        
        # 创建主页标签
        self.home_widget = HomeWidget(self)
        self.home_tab_index = self.tab_widget.addTab(self.home_widget, "主页")  # 恢复文本标签
        self.tab_widget.set_home_tab(self.home_tab_index)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        # 新的笔记本
        new_notebook_action = QAction("新的笔记本", self)
        new_notebook_action.setShortcut("Ctrl+Shift+N")
        new_notebook_action.triggered.connect(self.create_new_notebook)
        file_menu.addAction(new_notebook_action)
        
        # 新的Markdown文档
        new_doc_action = QAction("新的Markdown文档", self)
        new_doc_action.setShortcut("Ctrl+N")
        new_doc_action.triggered.connect(self.create_new_document)
        file_menu.addAction(new_doc_action)
        
        file_menu.addSeparator()
        
        # 打开笔记本
        open_notebook_action = QAction("打开笔记本", self)
        open_notebook_action.setShortcut("Ctrl+Shift+O")
        open_notebook_action.triggered.connect(self.open_notebook)
        file_menu.addAction(open_notebook_action)
        
        # 打开Markdown文件
        open_doc_action = QAction("打开Markdown文件", self)
        open_doc_action.setShortcut("Ctrl+O")
        open_doc_action.triggered.connect(self.open_document)
        file_menu.addAction(open_doc_action)
        
        file_menu.addSeparator()
        
        # 保存更改
        save_action = QAction("保存更改", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_document)
        file_menu.addAction(save_action)
        
        # 另存为
        save_as_action = QAction("另存为", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_document_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # 退出程序
        exit_action = QAction("退出程序", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        
        # 撤销
        undo_action = QAction("撤销", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo_edit)
        edit_menu.addAction(undo_action)
        
        # 重做
        redo_action = QAction("重做", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo_edit)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        # 复制
        copy_action = QAction("复制", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy_text)
        edit_menu.addAction(copy_action)
        
        # 粘贴
        paste_action = QAction("粘贴", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste_text)
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        # 插入Markdown组件的子菜单
        markdown_menu = edit_menu.addMenu("插入Markdown组件")
        
        components = [
            ("一级标题", "# "),
            ("二级标题", "## "),
            ("三级标题", "### "),
            ("加粗", "**"),
            ("斜体", "*"),
            ("删除线", "~~"),
            ("无序列表", "- "),
            ("有序列表", "1. "),
            ("链接", "[链接文本](URL)"),
            ("图片", "![图片描述](URL)"),
            ("代码块", "```\n代码\n```"),
            ("引用", "> "),
            ("水平线", "---")
        ]
        
        for name, text in components:
            action = QAction(name, self)
            action.triggered.connect(lambda checked, t=text: self.insert_markdown_component(t))
            markdown_menu.addAction(action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        # 查看程序官网
        website_action = QAction("查看程序官网", self)
        website_action.triggered.connect(self.open_website)
        help_menu.addAction(website_action)
        
        # GitHub仓库
        github_action = QAction("Gitee仓库", self)
        github_action.triggered.connect(self.open_github)
        help_menu.addAction(github_action)
        
        # 加入QQ群


        help_menu.addSeparator()
  
    
        # 打开关于窗口
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.open_about_dialog)
        help_menu.addAction(about_action)

        # 加入QQ群
        qq_group_action = QAction("加入QQ群", self)
        qq_group_action.triggered.connect(self.open_qq_group)
        help_menu.addAction(qq_group_action)
  
    def create_new_notebook(self):
        """创建新的笔记本"""
        # 获取笔记本名称
        name, ok = QInputDialog.getText(self, "创建新笔记本", "请输入笔记本名称:")
        if not ok or not name:
            return
        
        # 选择保存位置
        path = QFileDialog.getExistingDirectory(self, "选择保存位置", os.path.expanduser("~"))
        if not path:
            return
        
        notebook_path = os.path.join(path, name)
        
        # 创建笔记本目录
        try:
            os.makedirs(notebook_path)
            # 创建一个默认的README.md
            readme_path = os.path.join(notebook_path, "README.md")
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(f"# {name}\n\n这是{name}笔记本的说明文档。")
            
            # 添加到最近使用
            self.add_to_recent(notebook_path)
            
            # 打开笔记本
            self.open_notebook(notebook_path)
            
            self.statusBar().showMessage(f"已创建笔记本: {name}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"创建笔记本失败: {str(e)}")
    
    def create_new_document(self, notebook=None):
        """创建新的Markdown文档"""
        # 获取文档名称
        name, ok = QInputDialog.getText(self, "创建新文档", "请输入文档名称:")
        if not ok or not name:
            return
        
        # 确保文件名以.md结尾
        if not name.endswith(".md"):
            name += ".md"
        
        # 确定保存位置
        file_path = None
        if notebook and os.path.isdir(notebook):
            file_path = os.path.join(notebook, name)
        else:
            # 让用户选择保存位置
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存新文档", 
                os.path.join(os.path.expanduser("~"), name), 
                "Markdown文件 (*.md)"
            )
        
        if not file_path:
            return
        
        # 创建文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# {os.path.splitext(name)[0]}\n\n")
            
            # 打开文档
            self.open_document(file_path, notebook)
            
            self.statusBar().showMessage(f"已创建文档: {name}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"创建文档失败: {str(e)}")
    
    def open_notebook(self, notebook_path=None):
        """打开笔记本"""
        if not notebook_path:
            notebook_path = QFileDialog.getExistingDirectory(self, "打开笔记本", os.path.expanduser("~"))
        
        if not notebook_path or not os.path.isdir(notebook_path):
            return
        
        # 添加到最近使用
        self.add_to_recent(notebook_path)
        
        # 刷新主页的最近使用列表
        self.home_widget.update_recent_notebooks()
        self.home_widget.update_recent_docs()
        
        # 检查是否已经打开
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if hasattr(widget, 'notebook') and widget.notebook == notebook_path:
                self.tab_widget.setCurrentIndex(i)
                return
        
        # 查找笔记本中的Markdown文件
        md_files = []
        for root, _, files in os.walk(notebook_path):
            for file in files:
                if file.lower().endswith(".md"):
                    md_files.append(os.path.join(root, file))
        
        # 如果有README.md，优先打开它
        readme_path = os.path.join(notebook_path, "README.md")
        if os.path.exists(readme_path):
            self.open_document(readme_path, notebook_path)
        elif md_files:
            self.open_document(md_files[0], notebook_path)
        else:
            # 如果笔记本中没有任何Markdown文件，创建一个
            self.create_new_document(notebook_path)
    
    def open_document(self, file_path=None, notebook=None):
        """打开Markdown文件"""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "打开Markdown文件", 
                os.path.expanduser("~"), 
                "Markdown文件 (*.md);;所有文件 (*)"
            )
        
        if not file_path or not os.path.isfile(file_path):
            return
        
        # 如果没有指定笔记本，尝试从文件路径推断
        if not notebook:
            # 检查文件是否在最近打开的笔记本中
            for nb_path in self.recent_notebooks:
                if file_path.startswith(nb_path):
                    notebook = nb_path
                    break
        
        # 检查是否已经打开
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if hasattr(widget, 'file_path') and widget.file_path == file_path:
                self.tab_widget.setCurrentIndex(i)
                return
        
        # 创建编辑器并添加到标签页
        editor = MarkdownEditor(file_path, self.tab_widget)
        file_name = os.path.basename(file_path)
        index = self.tab_widget.addTab(editor, file_name)
        self.tab_widget.setCurrentIndex(index)
        
        self.statusBar().showMessage(f"已打开文档: {file_name}")
    
    def save_document(self):
        """保存当前文档"""
        current_widget = self.tab_widget.currentWidget()
        if hasattr(current_widget, 'save_file'):
            if current_widget.save_file():
                file_name = os.path.basename(current_widget.file_path)
                self.statusBar().showMessage(f"已保存文档: {file_name}")
                index = self.tab_widget.currentIndex()
                self.tab_widget.update_tab_title(index)
    
    def save_document_as(self):
        """另存为当前文档"""
        current_widget = self.tab_widget.currentWidget()
        if hasattr(current_widget, 'save_file'):
            default_path = current_widget.file_path if hasattr(current_widget, 'file_path') else os.path.expanduser("~")
            file_path, _ = QFileDialog.getSaveFileName(self, "另存为", default_path, "Markdown文件 (*.md)")
            if file_path:
                if current_widget.save_file(file_path):
                    # 更新标签标题
                    file_name = os.path.basename(file_path)
                    index = self.tab_widget.currentIndex()
                    self.tab_widget.setTabText(index, file_name)
                    self.statusBar().showMessage(f"已保存文档: {file_name}")
    
    def add_to_recent(self, notebook_path):
        """添加到最近使用的笔记本列表"""
        # 如果已经在列表中，移到前面
        if notebook_path in self.recent_notebooks:
            self.recent_notebooks.remove(notebook_path)
        
        # 添加到开头
        self.recent_notebooks.insert(0, notebook_path)
        
        # 限制最多10个最近使用的笔记本
        if len(self.recent_notebooks) > 10:
            self.recent_notebooks = self.recent_notebooks[:10]
        
        # 保存设置
        self.save_settings()
    
    def load_settings(self):
        """加载设置"""
        try:
            config_dir = os.path.join(os.path.expanduser("~"), ".marknote")
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            config_path = os.path.join(config_dir, "settings.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.recent_notebooks = settings.get('recent_notebooks', [])
        except Exception as e:
            print(f"加载设置失败: {str(e)}")
            self.recent_notebooks = []
    
    def save_settings(self):
        """保存设置"""
        try:
            config_dir = os.path.join(os.path.expanduser("~"), ".marknote")
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            config_path = os.path.join(config_dir, "settings.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'recent_notebooks': self.recent_notebooks,
                    'last_save_time': datetime.datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存设置失败: {str(e)}")
    
    def open_about_dialog(self):
        """打开关于对话框"""
        about_dialog = AboutDialog(self)
        about_dialog.exec()
    
    def open_website(self):
        """打开官方网站"""
        import webbrowser
        webbrowser.open(APP_WEBSITE)
    
    def open_github(self):
        """打开GitHub仓库"""
        import webbrowser
        webbrowser.open(GITHUB_REPO)

    def open_qq_group(self):
        """打开QQ群"""
        import webbrowser
        webbrowser.open(QQ_GROUP)
    
    # 编辑相关功能
    def undo_edit(self):
        """撤销编辑"""
        current_widget = self.tab_widget.currentWidget()
        if hasattr(current_widget, 'editor') and hasattr(current_widget.editor, 'undo'):
            current_widget.editor.undo()
    
    def redo_edit(self):
        """重做编辑"""
        current_widget = self.tab_widget.currentWidget()
        if hasattr(current_widget, 'editor') and hasattr(current_widget.editor, 'redo'):
            current_widget.editor.redo()
    
    def copy_text(self):
        """复制文本"""
        current_widget = self.tab_widget.currentWidget()
        if hasattr(current_widget, 'editor') and hasattr(current_widget.editor, 'copy'):
            current_widget.editor.copy()
    
    def paste_text(self):
        """粘贴文本"""
        current_widget = self.tab_widget.currentWidget()
        if hasattr(current_widget, 'editor') and hasattr(current_widget.editor, 'paste'):
            current_widget.editor.paste()
    
    def insert_markdown_component(self, text):
        """插入Markdown组件"""
        current_widget = self.tab_widget.currentWidget()
        if hasattr(current_widget, 'insert_markdown'):
            current_widget.insert_markdown(text)
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 检查是否有未保存的更改
        for i in range(self.tab_widget.count()):
            if i == self.home_tab_index:
                continue
                
            widget = self.tab_widget.widget(i)
            if hasattr(widget, 'is_modified') and widget.is_modified:
                reply = QMessageBox.question(self, "保存更改", 
                                            f"文档 '{self.tab_widget.tabText(i)}' 已修改，是否保存更改？",
                                            QMessageBox.StandardButton.Cancel)
                
                if reply == QMessageBox.StandardButton.Cancel:
                    event.ignore()
                    return
                elif reply == QMessageBox.StandardButton.Save:
                    if not widget.save_file():
                        event.ignore()
                        return
        
        # 保存设置
        self.save_settings()
        event.accept()

if __name__ == "__main__":
    # 确保中文显示正常
    
   
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 使用Fusion风格，跨平台一致性更好
    
    # 设置全局字体，确保中文显示
    font = QFont()
    font.setFamily("Segoe UI, Microsoft YaHei, SimHei")
    font.setPointSize(12)
    app.setFont(font)
    
    window = MarkdownNotebook()
    window.show()
    sys.exit(app.exec())
