import requests
from PyQt5 import QtCore, QtGui, QtWidgets
from plyer import notification
from utils import return_data, write_data, mac_notify
import sys,platform,settings
import subprocess as s
def no_abort(a, b, c):
    sys.__excepthook__(a, b, c)
sys.excepthook = no_abort

class SettingsPage(QtWidgets.QWidget):
    def __init__(self,parent=None):
        super(SettingsPage, self).__init__(parent)
        self.setupUi(self)
    def setupUi(self, settingspage):
        self.settingspage = settingspage
        self.settingspage.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.settingspage.setGeometry(QtCore.QRect(60, 0, 1041, 601))
        self.settingspage.setStyleSheet("QComboBox::drop-down {    border: 0px;}QComboBox::down-arrow {    image: url(:/images/down_icon.png);    width: 14px;    height: 14px;}QComboBox{    padding: 1px 0px 1px 3px;}QLineEdit:focus {   border: none;   outline: none;}")
        self.settings_card = QtWidgets.QWidget(self.settingspage)
        self.settings_card.setGeometry(QtCore.QRect(30, 70, 471, 501))
        font = QtGui.QFont()
        font.setPointSize(13) if platform.system() == "Darwin" else font.setPointSize(9)
        font.setFamily("Arial")
        self.settings_card.setFont(font)
        self.settings_card.setStyleSheet("background-color: #232323;border-radius: 20px;border: 1px solid #2e2d2d;")
        self.settings_card_2 = QtWidgets.QWidget(self.settingspage)
        self.settings_card_2.setGeometry(QtCore.QRect(550, 70, 471, 501))
        self.settings_card_2.setFont(font)
        self.settings_card_2.setStyleSheet("background-color: #232323;border-radius: 20px;border: 1px solid #2e2d2d;")

        self.webhook_edit = QtWidgets.QLineEdit(self.settings_card)
        self.webhook_edit.setGeometry(QtCore.QRect(30, 50, 340, 21))
        self.webhook_edit.setFont(font)
        self.webhook_edit.setStyleSheet("outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.webhook_edit.setPlaceholderText("Webhook Link")
        self.webhook_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.webhook_header = QtWidgets.QLabel(self.settings_card)
        self.webhook_header.setGeometry(QtCore.QRect(20, 10, 101, 31))

        self.webhook_test_btn = QtWidgets.QPushButton(self.settings_card)
        self.webhook_test_btn.setFont(font)
        self.webhook_test_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.webhook_test_btn.setStyleSheet(
            "color: #FFFFFF;background-color: #60a8ce;border-radius: 10px;border: 1px solid #2e2d2d;")
        self.webhook_test_btn.setText("Test")
        self.webhook_test_btn.setGeometry(QtCore.QRect(390, 45, 60, 31))
        self.webhook_test_btn.clicked.connect(self.test_webhook)

        self.notif_test_btn = QtWidgets.QPushButton(self.settings_card)
        self.notif_test_btn.setFont(font)
        self.notif_test_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.notif_test_btn.setStyleSheet(
            "color: #FFFFFF;background-color: #60a8ce;border-radius: 10px;border: 1px solid #2e2d2d;")
        self.notif_test_btn.setText("Test")
        self.notif_test_btn.setGeometry(QtCore.QRect(390, 360, 60, 31))
        self.notif_test_btn.clicked.connect(self.test_notif)

        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(18) if platform.system() == "Darwin" else font.setPointSize(13)
        font.setWeight(50)
        self.webhook_header.setFont(font)
        self.webhook_header.setStyleSheet("color: rgb(212, 214, 214);border:  none;")
        self.webhook_header.setText("Webhook")
        self.savesettings_btn = QtWidgets.QPushButton(self.settings_card)
        self.savesettings_btn.setGeometry(QtCore.QRect(190, 450, 86, 32))
        font = QtGui.QFont()
        font.setPointSize(13) if platform.system() == "Darwin" else font.setPointSize(9)
        font.setFamily("Arial")
        self.savesettings_btn.setFont(font)
        self.savesettings_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.savesettings_btn.setStyleSheet("color: #FFFFFF;background-color: #60a8ce;border-radius: 10px;border: 1px solid #2e2d2d;")
        self.savesettings_btn.setText("Save")
        self.savesettings_btn.clicked.connect(self.save_settings)

        self.webhook_success = QtWidgets.QCheckBox(self.settings_card)
        self.webhook_success.setGeometry(QtCore.QRect(30, 90, 140, 20))
        self.webhook_success.setStyleSheet("color: #FFFFFF;border: none;")
        self.webhook_success.setText("Successful checkout")

        self.webhook_failed = QtWidgets.QCheckBox(self.settings_card)
        self.webhook_failed.setGeometry(QtCore.QRect(30, 110, 140, 20))
        self.webhook_failed.setStyleSheet("color: #FFFFFF;border: none;")
        self.webhook_failed.setText("Failed checkout")

        self.webhook_carted = QtWidgets.QCheckBox(self.settings_card)
        self.webhook_carted.setGeometry(QtCore.QRect(30, 130, 140, 20))
        self.webhook_carted.setStyleSheet("color: #FFFFFF;border: none;")
        self.webhook_carted.setText("Item carted")

        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(18) if platform.system() == "Darwin" else font.setPointSize(13)
        font.setWeight(50)
        self.captcha_header = QtWidgets.QLabel(self.settings_card)
        self.captcha_header.setGeometry(QtCore.QRect(20, 180, 101, 31))
        self.captcha_header.setFont(font)
        self.captcha_header.setStyleSheet("color: rgb(212, 214, 214);border:  none;")
        self.captcha_header.setText("Captcha")

        self.notif_header = QtWidgets.QLabel(self.settings_card)
        self.notif_header.setGeometry(QtCore.QRect(20, 300, 101, 31))
        self.notif_header.setFont(font)
        self.notif_header.setStyleSheet("color: rgb(212, 214, 214);border:  none;")
        self.notif_header.setText("Notifications")

        self.twocaptcha_edit = QtWidgets.QLineEdit(self.settings_card)
        self.twocaptcha_edit.setGeometry(QtCore.QRect(30, 220, 340, 21))
        self.twocaptcha_edit.setPlaceholderText('2Captcha API Key')
        self.twocaptcha_edit.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")

        self.capmonster_edit = QtWidgets.QLineEdit(self.settings_card)
        self.capmonster_edit.setGeometry(QtCore.QRect(30, 260, 340, 21))
        self.capmonster_edit.setPlaceholderText('CapMonster API Key')
        self.capmonster_edit.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")

        self.notif_success = QtWidgets.QCheckBox(self.settings_card)
        self.notif_success.setGeometry(QtCore.QRect(30, 340, 221, 20))
        self.notif_success.setText("Successful checkout")
        self.notif_success.setStyleSheet("color: #FFFFFF;border: none;")

        self.notif_captcha = QtWidgets.QCheckBox(self.settings_card)
        self.notif_captcha.setGeometry(QtCore.QRect(30, 360, 221, 20))
        self.notif_captcha.setText("Manual captcha solve")
        self.notif_captcha.setStyleSheet("color: #FFFFFF;border: none;")

        self.notif_failed = QtWidgets.QCheckBox(self.settings_card)
        self.notif_failed.setGeometry(QtCore.QRect(30, 380, 221, 20))
        self.notif_failed.setText("Failed checkout")
        self.notif_failed.setStyleSheet("color: #FFFFFF;border: none;")
        self.proxies_header = QtWidgets.QLabel(self.settingspage)
        self.proxies_header.setGeometry(QtCore.QRect(30, 10, 81, 31))

        self.account_header = QtWidgets.QLabel(self.settings_card_2)
        self.account_header.setGeometry(QtCore.QRect(20, 10, 101, 31))
        self.account_header.setFont(font)
        self.account_header.setStyleSheet("color: rgb(212, 214, 214);border:  none;")
        self.account_header.setText("Accounts")

        font = QtGui.QFont()
        font.setPointSize(13) if platform.system() == "Darwin" else font.setPointSize(9)
        font.setFamily("Arial")

        self.account_box = QtWidgets.QComboBox(self.settings_card_2)
        self.account_box.setGeometry(QtCore.QRect(20, 50, 150, 21))
        self.account_box.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.account_box.addItems(['Adafruit', 'Sparkfun'])
        self.account_box.setFont(font)

        self.account_list = QtWidgets.QComboBox(self.settings_card_2)
        self.account_list.setGeometry(QtCore.QRect(200, 50, 250, 21))
        self.account_list.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.account_list.addItem('No accounts loaded')
        self.account_list.setFont(font)


        self.account_user = QtWidgets.QLineEdit(self.settings_card_2)
        self.account_user.setGeometry(QtCore.QRect(20, 90, 220, 21))
        self.account_user.setFont(font)
        self.account_user.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.account_user.setPlaceholderText("Account User")
        self.account_user.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)

        self.account_pw = QtWidgets.QLineEdit(self.settings_card_2)
        self.account_pw.setGeometry(QtCore.QRect(270, 90, 180, 21))
        self.account_pw.setFont(font)
        self.account_pw.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.account_pw.setPlaceholderText("Account Password")
        self.account_pw.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)

        self.account_otp = QtWidgets.QLineEdit(self.settings_card_2)
        self.account_otp.setGeometry(QtCore.QRect(20, 130, 430, 21))
        self.account_otp.setFont(font)
        self.account_otp.setStyleSheet(
            "outline: 0;border: 1px solid #60a8ce;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.account_otp.setPlaceholderText("Account 2FA Key")
        self.account_otp.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)

        self.account_save = QtWidgets.QPushButton(self.settings_card_2)
        self.account_save.setFont(font)
        self.account_save.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.account_save.setStyleSheet(
            "color: #FFFFFF;background-color: #60a8ce;border-radius: 10px;border: 1px solid #2e2d2d;")
        self.account_save.setText("Save")
        self.account_save.setGeometry(QtCore.QRect(100, 170, 100, 31))
        self.account_save.clicked.connect(self.save_account)

        self.account_del = QtWidgets.QPushButton(self.settings_card_2)
        self.account_del.setFont(font)
        self.account_del.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.account_del.setStyleSheet(
            "color: #FFFFFF;background-color: #60a8ce;border-radius: 10px;border: 1px solid #2e2d2d;")
        self.account_del.setText("Delete")
        self.account_del.setGeometry(QtCore.QRect(250, 170, 100, 31))
        self.account_del.clicked.connect(self.delete_account)

        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(22) if platform.system() == "Darwin" else font.setPointSize(16)
        font.setWeight(50)
        self.proxies_header.setFont(font)
        self.proxies_header.setStyleSheet("color: rgb(234, 239, 239);")
        self.proxies_header.setText("Settings")
        self.set_data()
        QtCore.QMetaObject.connectSlotsByName(settingspage)
        self.account_box.activated.connect(self.load_accounts)
        self.account_list.activated.connect(self.load_account_info)
        self.load_accounts()

    def load_accounts(self):
        f = open('./data/accounts.txt', 'r')
        self.account_otp.setPlaceholderText('2FA Key' if 'adafruit' in self.account_box.currentText().lower() else 'Phone Number')
        self.account_list.clear()
        found = False
        for line in f.readlines():
            if self.account_box.currentText().lower() == line.split('|')[0].lower():
                found = True
                self.account_list.addItem(line.split('|')[1])
        f.close()
        if not found:
            self.account_list.addItem('No accounts loaded')
            self.account_user.clear()
            self.account_pw.clear()
            self.account_otp.clear()
        else:
            self.load_account_info()

    def save_account(self):
        f = open('./data/accounts.txt', 'r')
        list_acc = []
        found = False
        for line in f.readlines():
            if self.account_box.currentText().lower() == line.split('|')[0].lower() and self.account_user.text() == line.split('|')[1]:
                found = True
                list_acc.append(f"{self.account_box.currentText().lower()}|{self.account_user.text()}|{self.account_pw.text()}|{self.account_otp.text()}")
            elif line.strip() != '':
                list_acc.append(line)
        f.close()
        if not found:
            f = open('./data/accounts.txt', 'a+')
            f.write(f"\n{self.account_box.currentText().lower()}|{self.account_user.text()}|{self.account_pw.text()}|{self.account_otp.text()}")
            f.close()
        else:
            f = open('./data/accounts.txt', 'w+')
            for acc in list_acc:
                f.write(f"\n{acc}")
            f.close()
        self.load_accounts()

    def delete_account(self):
        f = open('./data/accounts.txt', 'r')
        list_acc = []
        found = False
        for line in f.readlines():
            if self.account_box.currentText().lower() == line.split('|')[0].lower() and self.account_list.currentText() == line.split('|')[1]:
                found = True
            elif line.strip() != '':
                list_acc.append(line)
        f.close()
        if found:
            f = open('./data/accounts.txt', 'w+')
            for acc in list_acc:
                f.write(f"\n{acc}")
            f.close()
        self.load_accounts()
    def load_account_info(self):
        f = open('./data/accounts.txt', 'r')
        for line in f.readlines():
            if self.account_box.currentText().lower() == line.split('|')[0].lower() and self.account_list.currentText() == line.split('|')[1]:
                self.account_user.setText(line.split('|')[1])
                self.account_pw.setText(line.split('|')[2])
                self.account_otp.setText(line.split('|')[3])
                break
        f.close()

    def set_data(self):
        settings = return_data("./data/settings.json")
        self.webhook_edit.setText(settings["webhook"])
        self.twocaptcha_edit.setText(settings["2captchakey"])
        self.capmonster_edit.setText(settings["capmonsterkey"])
        if settings["webhooksuccess"]:
            self.webhook_success.setChecked(True)
        if settings["webhookcart"]:
            self.webhook_carted.setChecked(True)
        if settings["webhookfailed"]:
            self.webhook_failed.setChecked(True)
        if settings['notifsuccess']:
            self.notif_success.setChecked(True)
        if settings['notifcaptcha']:
            self.notif_captcha.setChecked(True)
        if settings['notiffailed']:
            self.notif_failed.setChecked(True)
        self.update_settings(settings)

    def save_settings(self):
        settings = {"webhook":self.webhook_edit.text(),
                    "webhooksuccess":self.webhook_success.isChecked(),
                    "webhookcart":self.webhook_carted.isChecked(),
                    "webhookfailed":self.webhook_failed.isChecked(),
                    "2captchakey":self.twocaptcha_edit.text(),
                    'capmonsterkey':self.capmonster_edit.text(),
                    'notifsuccess': self.notif_success.isChecked(),
                    'notifcaptcha': self.notif_captcha.isChecked(),
                    'notiffailed': self.notif_failed.isChecked()}
        write_data("./data/settings.json",settings)
        self.update_settings(settings)
        QtWidgets.QMessageBox.information(self, "Pi Bot", "Saved Settings")

    def update_settings(self,settings_data):
        global webhook, webhook_success, webhook_failed, webhook_cated, twocap_key,cap_key,notif_success, notif_captcha, notif_failed
        settings.webhook, settings.webhook_success, settings.webhook_failed, settings.webhook_cated, settings.twocap_key, settings.cap_key,settings.notif_success, settings.notif_captcha, settings.notif_failed = settings_data["webhook"], settings_data["webhooksuccess"], settings_data["webhookfailed"], settings_data["webhookcart"], settings_data["2captchakey"], settings_data['capmonsterkey'],settings_data["notifsuccess"], settings_data["notifcaptcha"], settings_data['notiffailed']

    def test_webhook(self):
        r = requests
        test_data = {'embeds': [{'title': 'Test Webhook Successful!', 'color': '6075075', 'footer': {'text': 'Pi Bot'}}]}
        r.post(self.webhook_edit.text(), json=test_data)

    def test_notif(self):
        current_os = platform.system().lower()
        if 'linux' in current_os:
            s.call(['notify-send', '[Pi Bot] Test Notification', "This is a test notification!"])
        elif 'darwin' in current_os:
            mac_notify('[Pi Bot] Test Notification', "This is a test notification!")
        elif 'window' in current_os:
            notification.notify(
                title='[Pi Bot] Test Notification',
                message='This is a test notification!',
                app_icon='icon.ico',
                timeout=5
            )









