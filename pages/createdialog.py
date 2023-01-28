import json

from PyQt5 import QtCore, QtGui, QtWidgets
import sys,platform
def no_abort(a, b, c):
    sys.__excepthook__(a, b, c)
sys.excepthook = no_abort

pi_sites = {'PiShop (US)' : 'https://www.pishop.us/',
                         'Sparkfun': 'https://www.sparkfun.com/',
                         'OKDO': 'https://www.odko.com/',
                         'Adafruit': 'https://www.adafruit.com'}

def get_shopify_url(name):
    return pi_sites[name]

class CreateDialog(QtWidgets.QDialog):
    def __init__(self,parent=None):
        super(CreateDialog, self).__init__(parent)
        self.setupUi(self)
        self.show()
    def setupUi(self, CreateDialog):
        self.CreateDialog = CreateDialog
        CreateDialog.setFixedSize(647, 200)
        CreateDialog.setStyleSheet("QComboBox::drop-down {    border: 0px;}QComboBox::down-arrow {    image: url(:/images/down_icon.png);    width: 14px;    height: 14px;}QComboBox{    padding: 1px 0px 1px 3px;}QLineEdit:focus {   border: none;   outline: none;} QSpinBox::up-button {subcontrol-origin: border;subcontrol-position: top right;width: 8px; border-image: url(:/images/uparrow_icon.png) 1;border-width: 1px;}QSpinBox::down-button {subcontrol-origin: border;subcontrol-position: bottom right;width: 8px;border-image: url(:/images/downarrow_icon.png) 1;border-width: 1px;border-top-width: 0;}")
        CreateDialog.setWindowTitle("Create Tasks")

        self.background = QtWidgets.QWidget(CreateDialog)
        self.background.setGeometry(QtCore.QRect(0, 0, 691, 391))
        self.background.setStyleSheet("background-color: #1E1E1E;")
        font = QtGui.QFont()
        font.setPointSize(13) if platform.system() == "Darwin" else font.setPointSize(9)
        font.setFamily("Arial")
        self.site_box = QtWidgets.QComboBox(self.background)
        self.site_box.setGeometry(QtCore.QRect(50, 20, 151, 21))
        self.site_box.setStyleSheet("outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.site_box.setFont(font)

        self.shopify_select = QtWidgets.QComboBox(self.background)
        self.shopify_select.setGeometry(QtCore.QRect(250, 20, 350, 21))
        self.shopify_select.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.shopify_select.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.shopify_select.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.shopify_select.setPlaceholderText("Item")
        self.shopify_select.setFont(font)
        self.shopify_select.setVisible(True)

        self.info_edit = QtWidgets.QLineEdit(self.background)
        self.info_edit.setGeometry(QtCore.QRect(450, 20, 151, 21))
        self.info_edit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.info_edit.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.info_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.info_edit.setPlaceholderText("Product Keywords")
        self.info_edit.setFont(font)
        self.info_edit.setVisible(False)

        self.size_edit = QtWidgets.QLineEdit(self.background)
        self.size_edit.setGeometry(QtCore.QRect(450, 55, 151, 21))
        self.size_edit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.size_edit.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.size_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.size_edit.setPlaceholderText("Size Keywords")
        self.size_edit.setFont(font)
        self.size_edit.setVisible(False)

        self.account_box = QtWidgets.QComboBox(self.background)
        self.account_box.setGeometry(QtCore.QRect(50, 120, 151, 21))
        self.account_box.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.account_box.addItem("Account")
        self.account_box.setFont(font)
        self.account_box.setVisible(False)


        self.profile_box = QtWidgets.QComboBox(self.background)
        self.profile_box.setGeometry(QtCore.QRect(50, 55, 151, 21))
        self.profile_box.setStyleSheet("outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.profile_box.addItem("Profile")
        self.profile_box.setFont(font)
        self.proxies_box = QtWidgets.QComboBox(self.background)
        self.proxies_box.setGeometry(QtCore.QRect(250, 55, 151, 21))
        self.proxies_box.setStyleSheet("outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.proxies_box.addItem("Proxy List")
        self.proxies_box.addItem("None")
        self.proxies_box.setFont(font)

        self.mode_box = QtWidgets.QComboBox(self.background)
        self.mode_box.setGeometry(QtCore.QRect(450, 55, 151, 21))
        self.mode_box.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.mode_box.addItems(['Noraml', 'Brute Force'])
        self.mode_box.setFont(font)

        self.captcha_box = QtWidgets.QComboBox(self.background)
        self.captcha_box.setGeometry(QtCore.QRect(450, 20, 151, 21))
        self.captcha_box.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.captcha_box.addItems(['Manual Harvester', '2Captcha', 'CapMonster'])
        self.captcha_box.setFont(font)
        self.captcha_box.setVisible(False)

        self.account_user = QtWidgets.QLineEdit(self.background)
        self.account_user.setGeometry(QtCore.QRect(50, 90, 151, 21))
        self.account_user.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.account_user.setPlaceholderText('Email')
        self.account_user.setFont(font)
        self.account_user.setVisible(False)

        self.account_pass = QtWidgets.QLineEdit(self.background)
        self.account_pass.setGeometry(QtCore.QRect(250, 90, 151, 21))
        self.account_pass.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.account_pass.setPlaceholderText('Password')
        self.account_pass.setFont(font)
        self.account_pass.setVisible(False)
        self.account_pass.setEchoMode(QtWidgets.QLineEdit.Password)

        self.link = QtWidgets.QLineEdit(self.background)
        self.link.setGeometry(QtCore.QRect(250, 20, 151, 21))
        self.link.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.link.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.link.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.link.setPlaceholderText("PiShop.US Link")
        self.link.setFont(font)
        self.link.setVisible(False)

        self.monitor_label = QtWidgets.QLabel(self.background)
        self.monitor_label.setGeometry(QtCore.QRect(500, 84, 151, 21))
        self.monitor_label.setScaledContents(True)
        self.monitor_label.setFont(font)
        self.monitor_label.setStyleSheet("color: rgb(212, 214, 214);border:  none;")
        self.monitor_label.setText('Monitor Delay')

        self.error_label = QtWidgets.QLabel(self.background)
        self.error_label.setGeometry(QtCore.QRect(512, 114, 151, 21))
        self.error_label.setScaledContents(True)
        self.error_label.setFont(font)
        self.error_label.setStyleSheet("color: rgb(212, 214, 214);border:  none;")
        self.error_label.setText('Error Delay')

        self.qty_label = QtWidgets.QLabel(self.background)
        self.qty_label.setGeometry(QtCore.QRect(530, 55, 151, 21))
        self.qty_label.setScaledContents(True)
        self.qty_label.setFont(font)
        self.qty_label.setStyleSheet("color: rgb(212, 214, 214);border:  none;")
        self.qty_label.setText('Quantity')
        self.qty_label.setVisible(False)

        self.qty_spinbox = QtWidgets.QSpinBox(self.background)
        self.qty_spinbox.setGeometry(QtCore.QRect(585, 55, 25, 21))
        self.qty_spinbox.setStyleSheet("border: 1px solid #60a8ce;border-width: 0 0 2px;color: #FFFFFF;")
        self.qty_spinbox.setMinimum(1)
        self.qty_spinbox.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.qty_spinbox.setVisible(False)

        self.monitor_edit = QtWidgets.QLineEdit(self.background)
        self.monitor_edit.setGeometry(QtCore.QRect(585, 85, 25, 21))
        self.monitor_edit.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.monitor_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.monitor_edit.setPlaceholderText("Monitor")
        self.monitor_edit.setFont(font)
        self.monitor_edit.setText("5.0")
        self.only_float = QtGui.QDoubleValidator()
        self.monitor_edit.setValidator(self.only_float)
        self.error_edit = QtWidgets.QLineEdit(self.background)
        self.error_edit.setGeometry(QtCore.QRect(585, 115, 25, 21))
        self.error_edit.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.error_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.error_edit.setPlaceholderText("Error")
        self.error_edit.setFont(font)
        self.error_edit.setText("5.0")
        self.error_edit.setValidator(self.only_float)

        self.only_float = QtGui.QDoubleValidator()
        self.addtask_btn = QtWidgets.QPushButton(self.background)
        self.addtask_btn.setGeometry(QtCore.QRect(250, 110, 151, 32))
        self.addtask_btn.setText("Add Task")
        font = QtGui.QFont()
        font.setPointSize(13) if platform.system() == "Darwin" else font.setPointSize(9)
        font.setFamily("Arial")
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(14) if platform.system() == "Darwin" else font.setPointSize(10)
        self.addtask_btn.setFont(font)
        self.addtask_btn.setStyleSheet("border-radius: 10px;background-color: #60a8ce;color: #FFFFFF;")
        self.addtask_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.taskcount_spinbox = QtWidgets.QSpinBox(self.background)
        self.taskcount_spinbox.setGeometry(QtCore.QRect(420, 115, 41, 21))
        self.taskcount_spinbox.setStyleSheet("border: 1px solid #60a8ce;border-width: 0 0 2px;color: #FFFFFF;")
        self.taskcount_spinbox.setMinimum(1)
        self.taskcount_spinbox.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)

        self.refresh_button = QtWidgets.QPushButton(self.background)
        self.refresh_button.setGeometry(QtCore.QRect(50, 110, 151, 32))
        self.refresh_button.setText("Refresh Sites")
        self.refresh_button.setFont(font)
        self.refresh_button.setStyleSheet("border-radius: 10px;background-color: #60a8ce;color: #FFFFFF;")
        self.refresh_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.refresh_button.clicked.connect(self.update_items)

        self.shopify_select.setVisible(False)
        self.qty_spinbox.setVisible(True)
        self.captcha_box.setVisible(False)
        self.qty_label.setVisible(True)
        self.account_user.setVisible(False)
        self.account_pass.setVisible(False)
        self.link.setVisible(True)
        self.link.setPlaceholderText('Adafruit Link')
        self.mode_box.setVisible(False)
        self.update_items()
        self.site_box.activated.connect(self.on_site_click)
        QtCore.QMetaObject.connectSlotsByName(CreateDialog)

    def update_items(self):
        self.base_items = json.loads(open('./data/base_items.json', 'r').read())
        self.custom_items = json.loads(open('./data/custom_items.json', 'r').read())
        self.site_box.clear()
        for item in self.custom_items:
            if item not in self.base_items:
                self.base_items[item] = {'site': self.custom_items[item]['site'],
                                         'items': self.custom_items[item]['items']}
            else:
                for it in self.custom_items[item]['items']:
                    self.base_items[item]['items'][it] = self.custom_items[item]['items'][it]
        site_list = ['Adafruit', 'OKDO', 'PiShop (US)', 'Sparkfun', 'Shopify Drop']
        for site in self.base_items:
            if site not in site_list:
                site_list.append(site)
        site_list.sort(key=str.lower)
        self.site_box.addItems(site_list)
        self.on_site_click()
    def load_data(self, task_tab):
        self.site_box.setCurrentText(task_tab.site)
        self.site_box.setEditable(False)
        self.shopify_select.setVisible(False)
        self.info_edit.setVisible(False)
        self.qty_label.setVisible(True)
        self.qty_spinbox.setVisible(True)
        self.mode_box.setVisible(False)
        self.size_edit.setVisible(False)
        if 'Sparkfun' in self.site_box.currentText():
            self.captcha_box.setVisible(False)
            self.account_user.setVisible(True)
            self.account_user.setText(task_tab.size.split('|')[0])
            self.account_pass.setVisible(True)
            self.account_pass.setText(task_tab.size.split('|')[1])
            self.link.setVisible(True)
            self.link.setText(task_tab.product)
            self.link.setPlaceholderText('Sparkfun PID')
        elif 'PiShop' in self.site_box.currentText():
            self.captcha_box.setVisible(True)
            self.account_user.setVisible(False)
            self.account_pass.setVisible(False)
            self.link.setVisible(True)
            self.link.setText(task_tab.product)
            self.link.setPlaceholderText('Product Link')
        elif 'Adafruit' in self.site_box.currentText():
            self.captcha_box.setVisible(False)
            self.account_user.setVisible(False)
            self.account_pass.setVisible(False)
            self.link.setVisible(True)
            self.link.setText(task_tab.product)
            self.link.setPlaceholderText('Adafruit Link')
        elif 'OKDO' in self.site_box.currentText():
            self.captcha_box.setVisible(False)
            self.account_user.setVisible(False)
            self.account_pass.setVisible(False)
            self.link.setVisible(True)
            self.link.setText(task_tab.product)
            self.link.setPlaceholderText('Product Link')
        elif self.site_box.currentText() == 'Shopify Drop':
            self.captcha_box.setVisible(False)
            self.account_user.setVisible(False)
            self.account_pass.setVisible(False)
            self.link.setVisible(True)
            self.link.setText(task_tab.info)
            self.link.setPlaceholderText('Base Shopify URL')
            self.info_edit.setVisible(True)
            self.size_edit.setVisible(True)
            self.info_edit.setText(task_tab.product)
            self.size_edit.setText(task_tab.size)
        else:
            self.shopify_select.setVisible(True)
            self.link.setVisible(False)
            self.captcha_box.setVisible(False)
            for item in self.base_items[self.site_box.currentText()]['items']:
                self.shopify_select.addItem(item)
            self.shopify_select.setCurrentText(task_tab.product)
        self.profile_box.setCurrentText(task_tab.profile)
        self.proxies_box.setCurrentText(task_tab.proxies)
        #self.info_edit.setText(task_tab.info)
        self.monitor_edit.setText(task_tab.monitor_delay)
        self.error_edit.setText(task_tab.error_delay)
        self.addtask_btn.setText('Update Task')

    def on_site_click(self):
        self.shopify_select.clear()
        self.addtask_btn.setGeometry(QtCore.QRect(250, 110, 151, 32))
        self.refresh_button.setGeometry(QtCore.QRect(50, 110, 151, 32))

        self.monitor_label.setGeometry(QtCore.QRect(500, 84, 151, 21))
        self.error_label.setGeometry(QtCore.QRect(512, 114, 151, 21))
        self.qty_label.setGeometry(QtCore.QRect(530, 55, 151, 21))
        self.qty_spinbox.setGeometry(QtCore.QRect(585, 55, 25, 21))
        self.monitor_edit.setGeometry(QtCore.QRect(585, 85, 25, 21))
        self.error_edit.setGeometry(QtCore.QRect(585, 115, 25, 21))
        self.taskcount_spinbox.setGeometry(QtCore.QRect(420, 115, 41, 21))

        self.account_user.setVisible(False)
        self.account_pass.setVisible(False)
        self.mode_box.setVisible(False)
        self.size_edit.setVisible(False)
        self.info_edit.setVisible(False)
        if 'PiShop' in self.site_box.currentText():
            self.info_edit.setVisible(False)
            self.shopify_select.setVisible(False)
            self.link.setVisible(True)
            self.qty_spinbox.setVisible(True)
            self.qty_label.setVisible(True)
            self.captcha_box.setVisible(True)
            self.link.setPlaceholderText('Product Link')
        elif 'Adafruit' in self.site_box.currentText():
            self.info_edit.setVisible(False)
            self.shopify_select.setVisible(False)
            self.link.setVisible(True)
            self.qty_spinbox.setVisible(True)
            self.qty_label.setVisible(True)
            self.captcha_box.setVisible(False)
            self.link.setPlaceholderText('Adafruit Link')
        elif 'Sparkfun' in self.site_box.currentText():
            self.info_edit.setVisible(False)
            self.shopify_select.setVisible(False)
            self.link.setVisible(True)
            self.qty_spinbox.setVisible(True)
            self.qty_label.setVisible(True)
            self.captcha_box.setVisible(False)
            self.link.setPlaceholderText('Sparkfun PID')
            self.addtask_btn.setGeometry(QtCore.QRect(250, 125, 151, 32))
            self.refresh_button.setGeometry(QtCore.QRect(50, 125, 151, 32))
            self.monitor_label.setGeometry(QtCore.QRect(500, 99, 151, 21))
            self.error_label.setGeometry(QtCore.QRect(512, 129, 151, 21))
            self.qty_label.setGeometry(QtCore.QRect(530, 70, 151, 21))
            self.qty_spinbox.setGeometry(QtCore.QRect(585, 70, 25, 21))
            self.monitor_edit.setGeometry(QtCore.QRect(585, 100, 25, 21))
            self.error_edit.setGeometry(QtCore.QRect(585, 130, 25, 21))
            self.taskcount_spinbox.setGeometry(QtCore.QRect(420, 130, 41, 21))
            self.account_user.setVisible(True)
            self.account_pass.setVisible(True)
        elif 'OKDO' in self.site_box.currentText():
            self.info_edit.setVisible(False)
            self.shopify_select.setVisible(False)
            self.link.setVisible(True)
            self.qty_spinbox.setVisible(True)
            self.qty_label.setVisible(True)
            self.captcha_box.setVisible(False)
            self.link.setPlaceholderText('Product Link')
        elif self.site_box.currentText() == 'Shopify Drop':
            self.info_edit.setVisible(True)
            self.shopify_select.setVisible(False)
            self.link.setVisible(True)
            self.qty_spinbox.setVisible(True)
            self.qty_label.setVisible(True)
            self.captcha_box.setVisible(False)
            self.size_edit.setVisible(True)
            self.link.setPlaceholderText('Base Shopify URL')
            self.addtask_btn.setGeometry(QtCore.QRect(250, 125, 151, 32))
            self.refresh_button.setGeometry(QtCore.QRect(50, 125, 151, 32))
            self.monitor_label.setGeometry(QtCore.QRect(500, 109, 151, 21))
            self.error_label.setGeometry(QtCore.QRect(512, 139, 151, 21))
            self.qty_label.setGeometry(QtCore.QRect(530, 80, 151, 21))
            self.qty_spinbox.setGeometry(QtCore.QRect(585, 80, 25, 21))
            self.monitor_edit.setGeometry(QtCore.QRect(585, 110, 25, 21))
            self.error_edit.setGeometry(QtCore.QRect(585, 140, 25, 21))
            self.taskcount_spinbox.setGeometry(QtCore.QRect(420, 130, 41, 21))
        else:
            self.shopify_select.setVisible(True)
            self.link.setVisible(False)
            self.captcha_box.setVisible(False)
            #self.mode_box.setVisible(True)
            for item in self.base_items[self.site_box.currentText()]['items']:
                self.shopify_select.addItem(item)
            self.shopify_select.setCurrentIndex(0)

