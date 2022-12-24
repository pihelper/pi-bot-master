import json
import threading

import requests
from PyQt5 import QtCore, QtGui, QtWidgets

import pages.createdialog
from pages import createdialog
from utils import return_data,write_data
import sys,platform
def no_abort(a, b, c):
    sys.__excepthook__(a, b, c)
sys.excepthook = no_abort

class CustomPage(QtWidgets.QWidget):
    def __init__(self,parent=None):
        super(CustomPage, self).__init__(parent)
        self.setupUi(self)
    def setupUi(self, custompage):
        self.custompage = custompage
        self.custompage.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.custompage.setGeometry(QtCore.QRect(60, 0, 1041, 601))
        self.custompage.setStyleSheet("QComboBox::drop-down {    border: 0px;}QComboBox::down-arrow {    image: url(:/images/down_icon.png);    width: 14px;    height: 14px;}")
        self.custom_card = QtWidgets.QWidget(self.custompage)
        self.custom_card.setGeometry(QtCore.QRect(30, 70, 471, 501))
        font = QtGui.QFont()
        font.setPointSize(13) if platform.system() == "Darwin" else font.setPointSize(9)
        font.setFamily("Arial")
        self.custom_card.setFont(font)
        self.custom_card.setStyleSheet("background-color: #232323;border-radius: 20px;border: 1px solid #2e2d2d;")
        QtCore.QMetaObject.connectSlotsByName(custompage)

        self.custom_card_site = QtWidgets.QWidget(self.custompage)
        self.custom_card_site.setGeometry(QtCore.QRect(550, 70, 471, 501))
        font = QtGui.QFont()
        font.setPointSize(13) if platform.system() == "Darwin" else font.setPointSize(9)
        font.setFamily("Arial")
        self.custom_card_site.setFont(font)
        self.custom_card_site.setStyleSheet("background-color: #232323;border-radius: 20px;border: 1px solid #2e2d2d;")
        QtCore.QMetaObject.connectSlotsByName(custompage)

        self.site_list = QtWidgets.QComboBox(self.custom_card_site)
        self.site_list.setGeometry(QtCore.QRect(30, 20, 150, 21))
        self.site_list.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.site_list.setStyleSheet(
            "outline: 0;border: 0px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.site_list.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.site_list.setPlaceholderText("Item")
        self.site_list.setFont(font)
        self.site_list.addItem('Select a site')
        self.site_list.setCurrentIndex(0)
        self.site_list.activated.connect(self.load_items)
        self.load_sites()

        self.item_list = QtWidgets.QComboBox(self.custom_card_site)
        self.item_list.setGeometry(QtCore.QRect(200, 20, 250, 21))
        self.item_list.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.item_list.setStyleSheet(
            "outline: 0;border: 0px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.item_list.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.item_list.setFont(font)
        self.item_list.addItem('No custom items')
        self.item_list.setCurrentIndex(0)

        self.search_list = QtWidgets.QComboBox(self.custom_card_site)
        self.search_list.setGeometry(QtCore.QRect(290, 80, 160, 21))
        self.search_list.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.search_list.setStyleSheet(
            "outline: 0;border: 0px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.search_list.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.search_list.setFont(font)
        self.search_list.addItems(['Select search method', 'Brute Force Search', 'Quick [Title]', 'Quick [Handle]'])
        self.search_list.setCurrentIndex(0)

        self.search_info = QtWidgets.QLineEdit(self.custom_card_site)
        self.search_info.setGeometry(QtCore.QRect(30, 80, 235, 21))
        self.search_info.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.search_info.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.search_info.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.search_info.setPlaceholderText("Item Link")
        self.search_info.setFont(font)

        self.product_edit = QtWidgets.QLineEdit(self.custom_card_site)
        self.product_edit.setGeometry(QtCore.QRect(30, 200, 420, 21))
        self.product_edit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.product_edit.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.product_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.product_edit.setPlaceholderText("Product JSON Endpoint")
        self.product_edit.setFont(font)

        self.handle_edit = QtWidgets.QLineEdit(self.custom_card_site)
        self.handle_edit.setGeometry(QtCore.QRect(270, 140, 180, 21))
        self.handle_edit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.handle_edit.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.handle_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.handle_edit.setPlaceholderText("Handle")
        self.handle_edit.setFont(font)

        self.title_edit = QtWidgets.QLineEdit(self.custom_card_site)
        self.title_edit.setGeometry(QtCore.QRect(30, 140, 215, 21))
        self.title_edit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.title_edit.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.title_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.title_edit.setPlaceholderText("Item Name")
        self.title_edit.setFont(font)

        self.size_edit = QtWidgets.QLineEdit(self.custom_card_site)
        self.size_edit.setGeometry(QtCore.QRect(30, 260, 215, 21))
        self.size_edit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.size_edit.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.size_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.size_edit.setPlaceholderText("Size")
        self.size_edit.setFont(font)

        self.size_select = QtWidgets.QComboBox(self.custom_card_site)
        self.size_select.setGeometry(QtCore.QRect(270, 260, 180, 21))
        self.size_select.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.size_select.setStyleSheet(
            "outline: 0;border: 0px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.size_select.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.size_select.setFont(font)
        self.size_select.addItem("Available Sizes")

        self.fetch_button = QtWidgets.QPushButton(self.custom_card_site)
        self.fetch_button.setGeometry(QtCore.QRect(30, 350, 120, 32))
        self.fetch_button.setFont(font)
        self.fetch_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.fetch_button.setStyleSheet(
            "color: #FFFFFF;background-color: #60a8ce;border-radius: 10px;border: 1px solid #2e2d2d;")
        self.fetch_button.setText("Fetch Item")
        self.fetch_button.clicked.connect(self.fetch_item)

        self.delete_item = QtWidgets.QPushButton(self.custom_card_site)
        self.delete_item.setGeometry(QtCore.QRect(330, 350, 120, 32))
        self.delete_item.setFont(font)
        self.delete_item.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.delete_item.setStyleSheet(
            "color: #FFFFFF;background-color: #60a8ce;border-radius: 10px;border: 1px solid #2e2d2d;")
        self.delete_item.setText("Delete")
        self.delete_item.clicked.connect(self.del_item)

        self.save_button = QtWidgets.QPushButton(self.custom_card_site)
        self.save_button.setGeometry(QtCore.QRect(180, 350, 120, 32))
        self.save_button.setFont(font)
        self.save_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.save_button.setStyleSheet(
            "color: #FFFFFF;background-color: #60a8ce;border-radius: 10px;border: 1px solid #2e2d2d;")
        self.save_button.setText("Save")
        self.save_button.clicked.connect(self.add_item)

        self.custom_site_list = QtWidgets.QComboBox(self.custom_card)
        self.custom_site_list.setGeometry(QtCore.QRect(30, 20, 420, 21))
        self.custom_site_list.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.custom_site_list.setStyleSheet(
            "outline: 0;border: 0px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.custom_site_list.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.custom_site_list.setFont(font)

        self.custom_site_edit = QtWidgets.QLineEdit(self.custom_card)
        self.custom_site_edit.setGeometry(QtCore.QRect(30, 80, 210, 21))
        self.custom_site_edit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.custom_site_edit.setStyleSheet(
            "outline: 0;border: 0px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.custom_site_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.custom_site_edit.setFont(font)
        self.custom_site_edit.setPlaceholderText('Custom Site URL')

        self.custom_site_name = QtWidgets.QLineEdit(self.custom_card)
        self.custom_site_name.setGeometry(QtCore.QRect(260, 80, 190, 21))
        self.custom_site_name.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.custom_site_name.setStyleSheet(
            "outline: 0;border: 0px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.custom_site_name.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.custom_site_name.setFont(font)
        self.custom_site_name.setPlaceholderText('Custom Site Name')

        self.delete_site = QtWidgets.QPushButton(self.custom_card)
        self.delete_site.setGeometry(QtCore.QRect(250, 350, 180, 32))
        self.delete_site.setFont(font)
        self.delete_site.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.delete_site.setStyleSheet(
            "color: #FFFFFF;background-color: #60a8ce;border-radius: 10px;border: 1px solid #2e2d2d;")
        self.delete_site.setText("Delete")
        self.delete_site.clicked.connect(self.del_site)

        self.save_site = QtWidgets.QPushButton(self.custom_card)
        self.save_site.setGeometry(QtCore.QRect(50, 350, 180, 32))
        self.save_site.setFont(font)
        self.save_site.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.save_site.setStyleSheet(
            "color: #FFFFFF;background-color: #60a8ce;border-radius: 10px;border: 1px solid #2e2d2d;")
        self.save_site.setText("Save")
        self.save_site.clicked.connect(self.add_site)

        self.item_status = QtWidgets.QLabel(self.custom_card_site)
        self.item_status.setGeometry(QtCore.QRect(30, 300, 420, 31))
        self.item_status.setFont(font)
        self.item_status.setStyleSheet("color: rgb(234, 239, 239); border:  none;")
        self.item_status.setText("Waiting for site addition")
        self.item_status.setAlignment(QtCore.Qt.AlignCenter)

        self.site_status = QtWidgets.QLabel(self.custom_card)
        self.site_status.setGeometry(QtCore.QRect(30, 250, 420, 31))
        self.site_status.setFont(font)
        self.site_status.setStyleSheet("color: rgb(234, 239, 239); border:  none;")
        self.site_status.setText("Waiting for item addition")
        self.site_status.setAlignment(QtCore.Qt.AlignCenter)

        self.load_custom_sites()


        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(22) if platform.system() == "Darwin" else font.setPointSize(16)
        font.setWeight(50)

        self.custom_header = QtWidgets.QLabel(self.custompage)
        self.custom_header.setGeometry(QtCore.QRect(30, 10, 150, 31))
        self.custom_header.setFont(font)
        self.custom_header.setStyleSheet("color: rgb(234, 239, 239);")
        self.custom_header.setText("Custom Items")

        self.status_signal = QtCore.pyqtSignal("PyQt_PyObject")

    def load_custom_sites(self):
        base_sites = json.loads(open('./data/base_items.json', 'r').read())
        custom_sites = json.loads(open('./data/custom_items.json', 'r').read())
        ind = 0
        self.custom_site_list.clear()
        for site in custom_sites:
            if site not in base_sites:
                self.custom_site_list.addItem(site)
                ind += 1
        if ind == 0:
            self.custom_site_list.addItem('No custom sites found')
        self.custom_site_list.setCurrentIndex(0)

    def add_site(self):
        custom_sites = json.loads(open('./data/custom_items.json', 'r').read())
        name = self.custom_site_name.text()
        site = self.custom_site_edit.text() + ('/' if not self.custom_site_edit.text().endswith('/') else '')
        if self.custom_site_name not in custom_sites:
            custom_sites[name] = {'site': site, 'items': {}}
            createdialog.CreateDialog.custom_items = custom_sites
            f = open('./data/custom_items.json', 'w')
            f.write(json.dumps(custom_sites))
            self.site_status.setText(f'Added {name} to site list')
            f.close()
            self.load_sites()
            self.load_custom_sites()
        else:
            self.site_status.setText(f'{name} already in list!')

    def add_item(self):
        custom_sites = json.loads(open('./data/custom_items.json', 'r').read())
        item_name = self.title_edit.text().strip()
        if not item_name:
            self.item_status.setText(f'Item name is empty')
            return
        if not self.product_edit.text().strip():
            self.item_status.setText(f'Product JSON Endpoint is empty')
            return
        if not self.handle_edit.text().strip():
            self.item_status.setText(f'Handle is empty')
            return
        if not self.size_edit.text().strip():
            self.item_status.setText(f'Size is empty')
            return
        desc = f'{self.product_edit.text()}|{self.handle_edit.text()}|{self.size_edit.text()}'
        site_name = self.site_list.currentText()
        if site_name:
            custom_sites[site_name]['items'][item_name] = desc
            f = open('./data/custom_items.json', 'w')
            f.write(json.dumps(custom_sites))
            self.item_status.setText(f'Added {item_name} to item list')
            f.close()
            self.load_sites()
            self.load_custom_sites()
            createdialog.CreateDialog.custom_items = custom_sites
        else:
            self.item_status.setText(f'Please select a site')

    def load_sites(self):
        self.site_list.clear()
        sites = json.loads(open('./data/custom_items.json', 'r').read())
        for site in sites:
            self.site_list.addItem(site)

    def load_items(self):
        sites = json.loads(open('./data/custom_items.json', 'r').read())
        self.item_list.clear()
        if self.site_list.currentIndex() != 0:
            if len(sites[self.site_list.currentText()]['items']) > 0:
                for item in sites[self.site_list.currentText()]['items']:
                    self.item_list.addItem(item)
            else:
                self.item_list.addItem('No custom items')
        else:
            self.item_list.addItem('No custom items')
    def get_site(self):
        sites = json.loads(open('./data/custom_items.json', 'r').read())
        return sites[self.site_list.currentText()]['site']
    def start_search(self):
        threading.Thread(target=self.fetch_item).start()

    def get_handle(self):
        to_return = self.search_info.text().split('?')[0]
        print(to_return)
        if to_return.split('/')[-1]:
            return to_return.split('/')[-1]
        else:
            return to_return.split('/')[-2]

    def del_site(self):
        if self.custom_site_list.currentText():
            custom_sites = json.loads(open('./data/custom_items.json', 'r').read())
            del custom_sites[self.custom_site_list.currentText()]
            createdialog.CreateDialog.custom_items = custom_sites
            f = open('./data/custom_items.json', 'w')
            f.write(json.dumps(custom_sites))
            f.close()
            self.load_sites()
            self.load_custom_sites()
            self.site_status.setText(f'{self.custom_site_list.currentText()} deleted')

        else:
            self.site_status.setText(f'Please select a site')

    def del_item(self):
        if self.site_list.currentText() and self.item_list.currentText() and self.item_list.currentText() != 'No custom items':
            custom_sites = json.loads(open('./data/custom_items.json', 'r').read())
            del custom_sites[self.site_list.currentText()]['items'][self.item_list.currentText()]
            createdialog.CreateDialog.custom_items = custom_sites
            f = open('./data/custom_items.json', 'w')
            f.write(json.dumps(custom_sites))
            f.close()
            self.item_status.setText(f'{self.item_list.currentText()} deleted')
            self.load_items()
        else:
            self.item_status.setText(f'Please select a site')

    def fetch_item(self):
        self.size_select.clear()
        site_to_use = self.get_site()
        if 'Brute Force Search' == self.search_list.currentText():
            all_collections = requests.get(f'{site_to_use}collections.json?limit=250').json()['collections']
            handle = self.get_handle()
            self.handle_edit.setText(handle)
            for col in all_collections:
                print(f'Checking collection: {col["title"]}')
                col_to_search = f'collections/{col["handle"]}/products.json?limit=250'
                link_to_search = f'{site_to_use}{col_to_search}'
                prod_json = requests.get(link_to_search).json()['products']
                for prod in prod_json:
                    if handle == prod['handle']:
                        var_list = []
                        for var in prod['variants']:
                            self.size_select.addItem(var['title'])
                        self.product_edit.setText(col_to_search)
                        self.size_edit.setText(self.size_select.currentText())
                        self.title_edit.setText(prod['title'])
                        self.item_status.setText(f'Item Found: {prod["title"]}')
                        return
            self.item_status.setText('Item not found')
        elif 'Title' in self.search_list.currentText():
            all_products = requests.get(f'{site_to_use}products.json?limit=250').json()['products']
            for prod in all_products:
                if self.search_info.text().lower().strip() == prod['title'].lower():
                    for var in prod['variants']:
                        self.size_select.addItem(var['title'])
                    self.product_edit.setText('products.json?limit=250')
                    self.size_edit.setText(self.size_select.currentText())
                    self.title_edit.setText(prod['title'])
                    self.handle_edit.setText(prod['handle'])
                    self.item_status.setText(f'Item Found: {prod["title"]}')
                    return
            self.item_status.setText('Item not found')
        elif 'Handle' in self.search_list.currentText():
            all_products = requests.get(f'{site_to_use}products.json?limit=250').json()['products']
            for prod in all_products:
                if self.search_info.text().lower().strip() == prod['handle'].lower():
                    for var in prod['variants']:
                        self.size_select.addItem(var['title'])
                    self.product_edit.setText('products.json?limit=250')
                    self.size_edit.setText(self.size_select.currentText())
                    self.title_edit.setText(prod['title'])
                    self.handle_edit.setText(prod['handle'])
                    self.item_status.setText(f'Item Found: {prod["title"]}')
                    return
            self.item_status.setText('Item not found')
    def update_label(self, word):
        self.custom_header.setText(f"Custom Items [{word}]")

