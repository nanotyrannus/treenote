import re
import sys
from os.path import abspath, join, dirname
from PyQt5.QtWidgets import QLineEdit, QTextEdit, QApplication, QDialog, QMainWindow, QCompleter, QTreeWidgetItem, QTreeWidget, QSizePolicy, QLabel, QPlainTextEdit
from main_window.MainWindow import Ui_MainWindow
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QItemSelectionModel, QEvent, QSize
from MultiCompleter import MultiCompleter
from json import loads, dumps
import pprint
import requests
import os
import shutil
from time import time
from glob import glob
from SlideshowUtil import ImageWriter

# Path of main.py
EXEC_DIR = dirname(abspath(__file__))

IMAGE_DIR = join(EXEC_DIR, "images")
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

def walk_path(node: QTreeWidgetItem):
    path = []
    while (node is not None):
        path.insert(0, node.text(0))
        node = node.parent()
    return path

def getWidgets(layout):
    return (layout.itemAt(i).widget() for i in range(layout.count()))

def getWidgetData(widget):
    if type(widget) is QLineEdit:
        return widget.text()
    elif type(widget) is QTextEdit or type(widget) is QPlainTextEdit:
        return widget.toPlainText()
    else:
        raise Exception("{} not supported".format(type(widget)))

def setWidgetData(widget, data):
    if type(widget) is QLineEdit:
        widget.setText(data)
    elif type(widget) is QTextEdit or type(widget) is QPlainTextEdit:
        widget.setPlainText(data)
    else:
        raise Exception("{} not supported".format(type(widget)))

class MyItem(QTreeWidgetItem):

    def __init__(self, cols):
        self.values = {'name':'New'}
        super().__init__(cols)

    def addChild(self, child):
        if 'children' not in self.values:
            self.values['children'] = []    
        self.values['children'].append(child.values)
        super().addChild(child)

    def removeChild(self, child):
        index = self.indexOfChild(child)
        self.values['children'].pop(index)
        super().removeChild(child)

    def setItemData(self, layout):
        for widget in getWidgets(layout):
            key = widget.objectName().split("_")[0]
            if "list" in widget.objectName():
                values = list(filter(lambda x: len(x) > 0, getWidgetData(widget).split(", ")))
                if len(values) > 0:
                    self.values[key] = values
            elif getWidgetData(widget):
                self.values[key] = getWidgetData(widget) 

    def getItemData(self, layout):
        for widget in getWidgets(layout):
            key = widget.objectName().split("_")[0]
            if "list" in widget.objectName():
                setWidgetData(widget, ", ".join(self.values.get(key, "")))
            else:
                setWidgetData(widget, self.values.get(key, ""))

class DroppableLabel(QLabel):

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        # print("DragMove")
        pass

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            window = self.window()
            current_item = window.previous_selection
            if not current_item:
                window.set_status_text("Select item before dropping.")
                return
            path_dirs = walk_path(current_item)
            image_path = os.path.join(*path_dirs)

            for url in event.mimeData().urls():
                url = url.toString()

                if os.path.isdir(url[7:]):
                    window.set_status_text("Error: Cannot drop a directory.")
                    return

                if not os.path.exists(join(IMAGE_DIR, image_path)):
                    os.makedirs(join(IMAGE_DIR, image_path))

                name = url.split("/")[-1]
                
                if os.path.isfile(join(IMAGE_DIR, image_path, name)):
                    attempt = 1
                    new_name = "({}) ".format(attempt) + name
                    while os.path.isfile(join(IMAGE_DIR, image_path, new_name)):
                        attempt += 1
                        new_name = "({}) ".format(attempt) + name
                    name = new_name

                if url.startswith("file"):
                    try:
                        print("file: {}".format(name))
                        shutil.copy2(url[7:], join(IMAGE_DIR, image_path, name))
                    except IOError as e:
                        print("IOError Occured", e)
                        return 
                    except OSError as e:
                        print("OSError Occured", e)
                        return

                elif url.startswith("http"):
                    try:
                        print("http {}".format(name))
                        r = requests.get(url, stream=True)
                        request_length = r.headers.get('content-length')
                            
                        window.set_status_text("Downloading {}:".format(name))
                        downloaded = 0
                        with open(join(IMAGE_DIR, image_path, name), "wb") as f:
                            if request_length is None:
                                window.set_status_text("File has no content-length header.")
                                f.write(r.content)
                            else:
                                progress_visible = 0
                                for chunk in r.iter_content(chunk_size= 2 ** 17):
                                    downloaded += len(chunk)
                                    progress = int((downloaded / int(request_length)) * 100)
                                    if progress > progress_visible:
                                        progress_visible = progress
                                        print("Download status: {}%".format(progress_visible))
                                    else:
                                        print("{} of {}".format(progress_visible, progress))
                                    f.write(chunk)

                        window.set_status_text("Finished downloading {}".format(name))
                    except IOError as e:
                        print("IOError occured", e)
                        return
                else:
                    raise Exception("Dropped item not supported: {}".format(url))
                window.set_slideshow()

class Window(QMainWindow):

    def eventFilter(self, source, event):
        return QMainWindow.eventFilter(self, source, event)

    def exit(self):
        sys.exit(0)

    def set_status_text(self, text):
        self.ui.status_label.setText(text)

    def traverse(self, root: dict):
        for i in sorted(root['children'], key=lambda child: child['name']):
            top_level_node = i
            top_level_item = self.traverse_helper(top_level_node)
            self.ui.tree_widget.addTopLevelItem(top_level_item)

    def traverse_helper(self, node: dict):
        import copy
        item = MyItem([node['name']])
        item.values = copy.deepcopy(node)
        item.values.pop("children", None)
        if 'children' in node and len(node['children']) > 0:
            for i in sorted(node['children'], key=lambda child: child['name']):
                item.addChild(self.traverse_helper(i))
            return item
        else:
            return item

    def __init__(self):
        super().__init__()
        self.previous_selection = None

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Tree Note")
        # self.dynamic_view.setText("Whatever")

        self.pixmap_cache = {}

        self.ui.actionExport.triggered.connect(self.export_handler)

        dynamic_view = DroppableLabel()
        self.dynamic_view = dynamic_view
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(dynamic_view.sizePolicy().hasHeightForWidth())
        dynamic_view.setSizePolicy(sizePolicy)
        dynamic_view.setMinimumSize(QSize(500, 500))
        dynamic_view.setBaseSize(QSize(180, 180))
        dynamic_view.setAlignment(Qt.AlignCenter)
        dynamic_view.setObjectName("dynamic_view")
        dynamic_view.setAcceptDrops(True)
        self.pixmap = QPixmap()
        self.pixmap_list = []
        self.slideshow_index = 0

        self.ui.prev_button.clicked.connect(self.prev_button_handler)
        self.ui.next_button.clicked.connect(self.next_button_handler)

        self.ui.center_layout.insertWidget(0, dynamic_view)
        self.ui.center_layout.removeWidget(self.ui.center_view)

        self.ui.desc_edit.installEventFilter(self)

        self.ui.tree_widget.clicked.connect(self.clicked_handler)
        self.ui.tree_widget.itemSelectionChanged.connect(self.selection_changed_handler)
        self.ui.tree_widget.itemPressed.connect(self.item_pressed_handler)

        self.ui.find_line.setPlaceholderText('find...')
        self.ui.synonym_list_line.setPlaceholderText('synonymy')
        self.ui.vendor_list_line.setPlaceholderText('vendors')
        self.ui.name_line.setPlaceholderText('name')
        self.ui.commonname_list_line.setPlaceholderText('common name')

        tags_completer = MultiCompleter(['xeric', 'mesic', 'nitrogen fixer'])
        tags_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.ui.tag_list_line.setPlaceholderText('tags')
        self.ui.tag_list_line.setCompleter(tags_completer)

        locality_completer = MultiCompleter(['California', 'Nevada'])
        locality_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.ui.locality_list_line.setPlaceholderText("locality")
        self.ui.locality_list_line.setCompleter(locality_completer)
        self.show()

        self.ui.save_button.clicked.connect(self.save_handler)
        self.ui.add_entry_button.clicked.connect(self.add_entry_handler)

        self.ui.delete_entry_button.clicked.connect(self.delete_entry_handler)

        self.load_handler()

    def resizeEvent(self, event):
        self.resizeView()
        QMainWindow.resizeEvent(self, event)

    def resizeView(self):
        size = self.dynamic_view.size()
        if not self.pixmap.isNull():
            self.dynamic_view.setPixmap(self.pixmap.scaled(size.width(), size.height(), Qt.KeepAspectRatio))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and event.modifiers() == Qt.ControlModifier:
            print("Escaped")
            self.exit()
        if event.key() == Qt.Key_E and event.modifiers() == Qt.ControlModifier:
            self.set_status_text("Exported")


    def export_handler(self):
        count = self.ui.tree_widget.topLevelItemCount()
        root = {'children':[]}
        with open(join(EXEC_DIR, "save_file.json"), "w") as f:
            for i in range(count):
                root['children'].append(self.ui.tree_widget.topLevelItem(i).values)
            f.write(dumps(root, indent=2, skipkeys=True, sort_keys=True))
        self.ui.tree_widget.clear()
        self.load_handler()
        self.setWindowTitle("Tree Note")

    def load_handler(self):
        with open(join(EXEC_DIR, "save_file.json")) as f:
            data = f.read()
            self.traverse(loads(data))

    def add_entry_handler(self):
        items = self.ui.tree_widget.selectedItems()
        new_entry = MyItem(["New"])
        if len(items) > 0:
            item = items[0]
            item.addChild(new_entry)
            self.ui.tree_widget.expandItem(item)
            item.setSelected(False)
        else:
            self.ui.tree_widget.addTopLevelItem(new_entry)
        self.setWindowTitle("Tree Note*")
        new_entry.setSelected(True)
        self.read_entry(new_entry)
        self.ui.name_line.setFocus()

    def delete_entry_handler(self):
        items = self.ui.tree_widget.selectedItems()
        if len(items) > 0:
            self.setWindowTitle("Tree Note*")
            item = items[0]
            if item.childCount() == 0 and item.parent():
                index = item.parent().indexOfChild(item)
                item.parent().removeChild(item)
                self.set_status_text("Deleted {}".format(item.values['name']))
            elif item.childCount() == 0:
                index = self.ui.tree_widget.indexOfTopLevelItem(item)
                self.ui.tree_widget.takeTopLevelItem(index)
        else:
            self.set_status_text("Nothing to remove.")

    def selection_changed_handler(self):
        print("SELECTION CHANGED")
        pass

    def prev_button_handler(self):
        if len(self.pixmap_list) > 0:
            self.set_status_text("Previous")
            if self.slideshow_index == 0:
                self.slideshow_index = len(self.pixmap_list) - 1
            else:
                self.slideshow_index -= 1
            print(self.slideshow_index)
            self.pixmap = self.pixmap_list[self.slideshow_index]
            self.dynamic_view.setPixmap(self.pixmap)
            self.resizeView()

    def next_button_handler(self):
        if len(self.pixmap_list) > 0:
            self.set_status_text("Next")
            if self.slideshow_index == len(self.pixmap_list) - 1:
                self.slideshow_index = 0
            else:    
                self.slideshow_index += 1
            print(self.slideshow_index)
            self.pixmap = self.pixmap_list[self.slideshow_index]
            self.dynamic_view.setPixmap(self.pixmap)
            self.resizeView()

    def item_pressed_handler(self, item):
        if self.previous_selection is item:
            item.setSelected(False)
            self.previous_selection = None
        else: 
            self.previous_selection = item
            self.set_slideshow()
            self.read_entry(item)

    def set_slideshow(self):
        slideshow_source = glob(join(IMAGE_DIR, "/".join(walk_path(self.previous_selection)), "**/*.*"), recursive=True)
        self.pixmap_list = []
        self.slideshow_index = 0
        for url in slideshow_source:
            if url not in self.pixmap_cache:
                self.pixmap_cache[url] = QPixmap(url)
            self.pixmap_list.append(self.pixmap_cache[url])
        if len(self.pixmap_list) > 0:
            self.pixmap = self.pixmap_list[0]
        else:
            self.pixmap = QPixmap()
        self.dynamic_view.setPixmap(self.pixmap)
        self.resizeView()

    def clicked_handler(self):
        self.set_status_text("Clicked")

    def save_handler(self, event):
        items = self.ui.tree_widget.selectedItems()
        if len(items) > 0:
            item = items[0]
            item.setItemData(self.ui.metadata_layout)
            item.setText(0, item.values['name'])

            self.set_status_text("Entry saved")
        else:
            self.set_status_text("No entry selected.")

    def selected_handler(self, items, col):
        node = self.ui.tree_widget.selectedItems()[0]
        # read_entry(node)

    def read_entry(self, node: MyItem):
        node.getItemData(self.ui.metadata_layout)
        # values = node.values
        # self.ui.name_line.setText(values['name'] if 'name' in values else None)
        # self.ui.locality_line.setText(node.values['locality'] if 'locality' in values else None)
        # self.ui.tags_line.setText(", ".join(node.values['tags']) if 'tags' in values else None)
        # self.ui.desc_edit.setPlainText(node.values['desc'] if 'desc' in values else None)


entries = {}

def read_entry(node: QTreeWidgetItem):
    if node not in entries:
        entries[node] = "what"
    else:
        print(entries[node])


app = QApplication(sys.argv)
app.addLibraryPath(abspath('.'))
window = Window()

sys.exit(app.exec_())
