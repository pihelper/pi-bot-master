from PyQt5 import QtCore, QtGui, QtWidgets
import sys,platform

from sites.site_keys import chigaco_items, vilros_items, pihut_items, sbc_items, cool_items, pimoroni_items, pi3g_items


def no_abort(a, b, c):
    sys.__excepthook__(a, b, c)
sys.excepthook = no_abort

pi_sites = {'ThePiHut': 'http://thepihut.com/',
                         'Vilros': 'http://vilros.com/',
                         'Chicago Dist.': 'http://chicagodist.com/',
                         'Pimoroni (UK)' : 'http://shop.pimoroni.com/',
                         'SBComponents (UK)' : 'http://shop.sb-components.co.uk/',
                         'pi3g (DE)': 'http://buyzero.de/',
                         'Cool Components (UK)' : 'http://coolcomponents.co.uk/',
                         'PiShop (US)' : 'https://www.pishop.us/',
                         'Sparkfun': 'https://www.sparkfun.com/',
                         'OKDO (US)': 'https://www.odko.com/us/'}

def get_shopify_url(name):
    return pi_sites[name]

class CreateDialog(QtWidgets.QDialog):
    def __init__(self,parent=None):
        super(CreateDialog, self).__init__(parent)
        self.setupUi(self)
        self.show()
    def setupUi(self, CreateDialog):
        self.CreateDialog = CreateDialog
        CreateDialog.setFixedSize(647, 160)
        CreateDialog.setStyleSheet("QComboBox::drop-down {    border: 0px;}QComboBox::down-arrow {    image: url(:/images/down_icon.png);    width: 14px;    height: 14px;}QComboBox{    padding: 1px 0px 1px 3px;}QLineEdit:focus {   border: none;   outline: none;} QSpinBox::up-button {subcontrol-origin: border;subcontrol-position: top right;width: 8px; border-image: url(:/images/uparrow_icon.png) 1;border-width: 1px;}QSpinBox::down-button {subcontrol-origin: border;subcontrol-position: bottom right;width: 8px;border-image: url(:/images/downarrow_icon.png) 1;border-width: 1px;border-top-width: 0;}")
        CreateDialog.setWindowTitle("Create Tasks")
        self.background = QtWidgets.QWidget(CreateDialog)
        self.background.setGeometry(QtCore.QRect(0, 0, 691, 391))
        self.background.setStyleSheet("background-color: #1E1E1E;")
        font = QtGui.QFont()
        font.setPointSize(13) if platform.system() == "Darwin" else font.setPointSize(13*.75)
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
        self.info_edit.setPlaceholderText("KW / Link / Variant")
        self.info_edit.setFont(font)
        self.info_edit.setVisible(False)

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

        self.captcha_box = QtWidgets.QComboBox(self.background)
        self.captcha_box.setGeometry(QtCore.QRect(50, 90, 151, 21))
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
        self.monitor_label.setGeometry(QtCore.QRect(470, 54, 151, 21))
        self.monitor_label.setScaledContents(True)
        self.monitor_label.setFont(font)
        self.monitor_label.setStyleSheet("color: rgb(212, 214, 214);border:  none;")
        self.monitor_label.setText('Monitor Delay')

        self.error_label = QtWidgets.QLabel(self.background)
        self.error_label.setGeometry(QtCore.QRect(482, 84, 151, 21))
        self.error_label.setScaledContents(True)
        self.error_label.setFont(font)
        self.error_label.setStyleSheet("color: rgb(212, 214, 214);border:  none;")
        self.error_label.setText('Error Delay')

        self.qty_label = QtWidgets.QLabel(self.background)
        self.qty_label.setGeometry(QtCore.QRect(501, 24, 151, 21))
        self.qty_label.setScaledContents(True)
        self.qty_label.setFont(font)
        self.qty_label.setStyleSheet("color: rgb(212, 214, 214);border:  none;")
        self.qty_label.setText('Quantity')
        self.qty_label.setVisible(False)

        self.qty_spinbox = QtWidgets.QSpinBox(self.background)
        self.qty_spinbox.setGeometry(QtCore.QRect(550, 25, 25, 21))
        self.qty_spinbox.setStyleSheet("border: 1px solid #60a8ce;border-width: 0 0 2px;color: #FFFFFF;")
        self.qty_spinbox.setMinimum(1)
        self.qty_spinbox.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.qty_spinbox.setVisible(False)

        self.monitor_edit = QtWidgets.QLineEdit(self.background)
        self.monitor_edit.setGeometry(QtCore.QRect(550, 55, 25, 21))
        self.monitor_edit.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.monitor_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.monitor_edit.setPlaceholderText("Monitor")
        self.monitor_edit.setFont(font)
        self.monitor_edit.setText("5.0")
        self.only_float = QtGui.QDoubleValidator()
        self.monitor_edit.setValidator(self.only_float)
        self.error_edit = QtWidgets.QLineEdit(self.background)
        self.error_edit.setGeometry(QtCore.QRect(550, 85, 25, 21))
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
        font.setPointSize(13) if platform.system() == "Darwin" else font.setPointSize(13*.75)
        font.setFamily("Arial")
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(14) if platform.system() == "Darwin" else font.setPointSize(14*.75)
        self.addtask_btn.setFont(font)
        self.addtask_btn.setStyleSheet("border-radius: 10px;background-color: #60a8ce;color: #FFFFFF;")
        self.addtask_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.taskcount_spinbox = QtWidgets.QSpinBox(self.background)
        self.taskcount_spinbox.setGeometry(QtCore.QRect(420, 115, 41, 21))
        self.taskcount_spinbox.setStyleSheet("border: 1px solid #60a8ce;border-width: 0 0 2px;color: #FFFFFF;")
        self.taskcount_spinbox.setMinimum(1)
        self.taskcount_spinbox.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)

        pi_site_list = sorted(pi_sites.keys(), key=str.lower)
        item_list = sorted(chigaco_items.keys(), key=str.lower)
        self.shopify_select.addItems(item_list)
        self.shopify_select.setCurrentText(item_list[0])
        self.site_box.addItems(pi_site_list)
        self.site_box.setCurrentText(pi_site_list[0])


        self.site_box.activated.connect(self.on_site_click)
        QtCore.QMetaObject.connectSlotsByName(CreateDialog)

    def load_data(self, task_tab):
        self.site_box.setCurrentText(task_tab.site)
        self.site_box.setEditable(False)
        self.shopify_select.setVisible(False)
        self.info_edit.setVisible(False)
        self.qty_label.setVisible(True)
        self.qty_spinbox.setVisible(True)

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
        elif 'Okdo' in self.site_box.currentText():
            self.captcha_box.setVisible(False)
            self.account_user.setVisible(False)
            self.account_pass.setVisible(False)
            self.link.setVisible(True)
            self.link.setText(task_tab.product)
            self.link.setPlaceholderText('Product Link')
        else:
            self.shopify_select.setVisible(True)
            self.link.setVisible(False)
            self.qty_label.setVisible(False)
            self.qty_spinbox.setVisible(False)
            if self.site_box.currentText() == 'Chicago Dist.':
                mode = chigaco_items
            elif self.site_box.currentText() == 'Vilros':
                mode = vilros_items
            elif self.site_box.currentText() == 'ThePiHut':
                mode = pihut_items
            elif self.site_box.currentText() == 'SBComponents (UK)':
                mode = sbc_items
            elif self.site_box.currentText() == 'Pimoroni (UK)':
                mode = pimoroni_items
            elif self.site_box.currentText() == 'Cool Components (UK)':
                mode = cool_items
            elif self.site_box.currentText() == 'pi3g (DE)':
                mode = pi3g_items
            item_list = sorted(mode.keys(), key=str.lower)
            self.info_edit.setText(get_shopify_url(task_tab.site))
            self.shopify_select.addItems(item_list)
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
        self.CreateDialog.setFixedSize(647, 160)
        self.account_user.setVisible(False)
        self.account_pass.setVisible(False)

        if 'PiShop' in self.site_box.currentText():
            self.info_edit.setVisible(False)
            self.shopify_select.setVisible(False)
            self.link.setVisible(True)
            self.qty_spinbox.setVisible(True)
            self.qty_label.setVisible(True)
            self.captcha_box.setVisible(True)
            self.link.setPlaceholderText('Product Link')
        elif 'Sparkfun' in self.site_box.currentText():
            self.info_edit.setVisible(False)
            self.shopify_select.setVisible(False)
            self.link.setVisible(True)
            self.qty_spinbox.setVisible(True)
            self.qty_label.setVisible(True)
            self.captcha_box.setVisible(False)
            self.link.setPlaceholderText('Sparkfun PID')
            self.CreateDialog.setFixedSize(647, 175)
            self.addtask_btn.setGeometry(QtCore.QRect(250, 125, 151, 32))
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
        else:
            self.shopify_select.setVisible(True)
            self.link.setVisible(False)
            self.qty_spinbox.setVisible(False)
            self.qty_label.setVisible(False)
            self.captcha_box.setVisible(False)

            if 'Chicago Dist.' == self.site_box.currentText():
                item_list = sorted(chigaco_items.keys(), key=str.lower)
            elif 'Vilros' == self.site_box.currentText():
                item_list = sorted(vilros_items.keys(), key=str.lower)
            elif 'ThePiHut' == self.site_box.currentText():
                item_list = sorted(pihut_items.keys(), key=str.lower)
            elif 'SBComponents (UK)' == self.site_box.currentText():
                item_list = sorted(sbc_items.keys(), key=str.lower)
            elif 'Cool Components (UK)' == self.site_box.currentText():
                item_list = sorted(cool_items.keys(), key=str.lower)
            elif 'Pimoroni (UK)' == self.site_box.currentText():
                item_list = sorted(pimoroni_items.keys(), key=str.lower)
            elif 'pi3g (DE)' == self.site_box.currentText():
                item_list = sorted(pi3g_items.keys(), key=str.lower)

            self.shopify_select.addItems(item_list)
            self.shopify_select.setCurrentText(item_list[0])

