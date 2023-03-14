from threading import Thread

from PyQt5 import QtCore, QtGui, QtWidgets

from harvester import Harvester
from pages import createdialog
from pages.custompage import CustomPage
from pages.homepage import TaskTab, HomePage
from pages.createdialog import CreateDialog, get_shopify_url
from pages.profilespage import ProfilesPage
from pages.proxiespage import ProxiesPage
from pages.settingspage import SettingsPage
import images.images, sys, os
from sites.site_keys import get_item_info


def no_abort(a, b, c):
    sys.__excepthook__(a, b, c)
sys.excepthook = no_abort
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent=parent)
        self.setupUi(self)
        self.show()
    def setupUi(self, MainWindow):
        self.version ='1.2'
        MainWindow.setFixedSize(1109, 600)
        MainWindow.setStyleSheet("background-color: #1E1E1E;")
        MainWindow.setWindowTitle(f"Pi Bot - Version {self.version}")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setStyleSheet("QMessageBox QLabel { color: #FFFFFF; }QMessageBox QPushButton { background-color: #60a8ce;color: #FFFFFF;}")
        self.sidebar = QtWidgets.QWidget(self.centralwidget)
        self.sidebar.setGeometry(QtCore.QRect(0, 0, 61, 601))
        self.sidebar.setStyleSheet("background-color: #232323;border-right: 1px solid #2e2d2d;")
        self.home_tab = QtWidgets.QWidget(self.sidebar)
        self.home_tab.setGeometry(QtCore.QRect(0, 85, 60, 45))
        self.home_tab.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.home_tab.setStyleSheet("background-color: #304e5e ;border: none;")
        self.home_active_tab = QtWidgets.QWidget(self.home_tab)
        self.home_active_tab.setGeometry(QtCore.QRect(0, 0, 4, 45))
        self.home_active_tab.setStyleSheet("background-color: #60a8ce;border: none;")
        self.home_active_tab.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.home_icon = QtWidgets.QLabel(self.home_tab)
        self.home_icon.setGeometry(QtCore.QRect(21, 13, 20, 20))
        self.home_icon.setStyleSheet("border: none;")
        self.home_icon.setText("")
        self.home_icon.setPixmap(QtGui.QPixmap("images/home_alt.png"))
        self.home_icon.setScaledContents(True)
        self.home_icon.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.profiles_tab = QtWidgets.QWidget(self.sidebar)
        self.profiles_tab.setGeometry(QtCore.QRect(0, 130, 60, 45))
        self.profiles_tab.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.profiles_tab.setStyleSheet("background-color: transparent;border: none;")
        self.profiles_active_tab = QtWidgets.QWidget(self.profiles_tab)
        self.profiles_active_tab.setGeometry(QtCore.QRect(0, 0, 4, 45))
        self.profiles_active_tab.setStyleSheet("background-color: transparent;border: none;")
        self.profiles_active_tab.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.profiles_icon = QtWidgets.QLabel(self.profiles_tab)
        self.profiles_icon.setGeometry(QtCore.QRect(21, 13, 20, 20))
        self.profiles_icon.setStyleSheet("border: none;")
        self.profiles_icon.setText("")
        self.profiles_icon.setPixmap(QtGui.QPixmap("images/profiles.png"))
        self.profiles_icon.setScaledContents(True)
        self.profiles_icon.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.proxies_tab = QtWidgets.QWidget(self.sidebar)
        self.proxies_tab.setGeometry(QtCore.QRect(0, 175, 60, 45))
        self.proxies_tab.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.proxies_tab.setStyleSheet("background-color: transparent;border: none;")
        self.proxies_active_tab = QtWidgets.QWidget(self.proxies_tab)
        self.proxies_active_tab.setGeometry(QtCore.QRect(0, 0, 4, 45))
        self.proxies_active_tab.setStyleSheet("background-color: transparent;border: none;")
        self.proxies_icon = QtWidgets.QLabel(self.proxies_tab)
        self.proxies_icon.setGeometry(QtCore.QRect(21, 13, 20, 20))
        self.proxies_icon.setStyleSheet("border: none;")
        self.proxies_icon.setPixmap(QtGui.QPixmap("images/proxies.png"))
        self.proxies_icon.setScaledContents(True)

        self.settings_tab = QtWidgets.QWidget(self.sidebar)
        self.settings_tab.setGeometry(QtCore.QRect(0, 220, 60, 45))
        self.settings_tab.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.settings_tab.setStyleSheet("background-color: transparent;border: none;")
        self.settings_active_tab = QtWidgets.QWidget(self.settings_tab)
        self.settings_active_tab.setGeometry(QtCore.QRect(0, 0, 4, 45))
        self.settings_active_tab.setStyleSheet("background-color: transparent;border: none;")
        self.settings_icon = QtWidgets.QLabel(self.settings_tab)
        self.settings_icon.setGeometry(QtCore.QRect(21, 13, 20, 20))
        self.settings_icon.setStyleSheet("border: none;")
        self.settings_icon.setPixmap(QtGui.QPixmap("images/settings.png"))
        self.settings_icon.setScaledContents(True)

        self.custom_tab = QtWidgets.QWidget(self.sidebar)
        self.custom_tab.setGeometry(QtCore.QRect(0, 265, 60, 45))
        self.custom_tab.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.custom_tab.setStyleSheet("background-color: transparent;border: none;")
        self.custom_active_tab = QtWidgets.QWidget(self.custom_tab)
        self.custom_active_tab.setGeometry(QtCore.QRect(0, 0, 4, 45))
        self.custom_active_tab.setStyleSheet("background-color: transparent;border: none;")
        self.custom_icon = QtWidgets.QLabel(self.custom_tab)
        self.custom_icon.setGeometry(QtCore.QRect(21, 13, 20, 20))
        self.custom_icon.setStyleSheet("border: none;")
        self.custom_icon.setPixmap(QtGui.QPixmap("images/custom.png"))
        self.custom_icon.setScaledContents(True)

        self.logo = QtWidgets.QLabel(self.sidebar)
        self.logo.setGeometry(QtCore.QRect(10, 23, 41, 41))
        self.logo.setStyleSheet("border: none;")
        self.logo.setText("")
        self.logo.setPixmap(QtGui.QPixmap("images/pibot.png"))
        self.logo.setScaledContents(True)
        self.homepage = HomePage(self.centralwidget)
        self.createdialog = CreateDialog(self)
        self.createdialog.addtask_btn.clicked.connect(self.create_task)
        self.createdialog.setWindowIcon(QtGui.QIcon("images/pibot.png"))
        self.createdialog.hide()
        self.profilespage = ProfilesPage(self.centralwidget)
        self.profilespage.hide()
        self.proxiespage = ProxiesPage(self.centralwidget)
        self.proxiespage.hide()
        self.settingspage = SettingsPage(self.centralwidget)
        self.settingspage.hide()
        self.custompage = CustomPage(self.centralwidget)
        self.custompage.hide()
        MainWindow.setCentralWidget(self.centralwidget)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        self.set_functions()

    def set_functions(self):
        self.current_page = "home"
        self.home_tab.mousePressEvent = lambda event: self.change_page(event,"home")
        self.profiles_tab.mousePressEvent = lambda event: self.change_page(event,"profiles")
        self.proxies_tab.mousePressEvent = lambda event: self.change_page(event,"proxies")
        self.settings_tab.mousePressEvent = lambda event: self.change_page(event,"settings")
        self.custom_tab.mousePressEvent = lambda event: self.change_page(event, "custom")
        self.homepage.newtask_btn.clicked.connect(self.createdialog.show)
    
    def change_page(self,event,current_page):
        eval('self.{}_active_tab.setStyleSheet("background-color: transparent;border: none;")'.format(self.current_page))
        eval('self.{}_icon.setPixmap(QtGui.QPixmap("images/{}.png"))'.format(self.current_page,self.current_page))
        eval('self.{}_tab.setStyleSheet("background-color: transparent;border: none;")'.format(self.current_page))
        eval("self.{}page.hide()".format(self.current_page))
        self.current_page = current_page
        eval('self.{}_active_tab.setStyleSheet("background-color: #60a8ce;border: none;")'.format(self.current_page))
        eval('self.{}_icon.setPixmap(QtGui.QPixmap("images/{}_alt.png"))'.format(self.current_page,self.current_page))
        eval('self.{}_tab.setStyleSheet("background-color: #304e5e ;border: none;")'.format(self.current_page))
        eval("self.{}page.show()".format(self.current_page))
    
    def create_task(self):
        site = self.createdialog.site_box.currentText()
        mode = ''
        if 'PiShop' in site:
            product = self.createdialog.link.text()
            size = ''
            info = self.createdialog.link.text()
            profile = self.createdialog.profile_box.currentText()

        elif 'Sparkfun' in site:
            product = self.createdialog.link.text()
            size = f'{self.createdialog.account_user.text()}|{self.createdialog.account_pass.text()}'
            info = self.createdialog.link.text()
            profile = self.createdialog.account_box.currentText()

        elif 'OKDO' in site:
            product = self.createdialog.link.text()
            size = ''
            info = self.createdialog.link.text()
            profile = self.createdialog.profile_box.currentText()

        elif 'Adafruit' in site:
            product = self.createdialog.link.text()
            size = ''
            info = self.createdialog.link.text()
            profile = self.createdialog.account_box.currentText()
        elif 'Shopify Drop' in site:
            product = self.createdialog.info_edit.text()
            size = self.createdialog.size_edit.text()
            info = self.createdialog.link.text()
            profile = self.createdialog.profile_box.currentText()

        else:
            product = self.createdialog.shopify_select.currentText()
            size = self.createdialog.base_items[site]['items'][product]
            info = self.createdialog.base_items[site]['site']
            mode = self.createdialog.mode_box.currentText()
            profile = self.createdialog.profile_box.currentText()

        captcha_type = self.createdialog.captcha_box.currentText()
        proxies = self.createdialog.proxies_box.currentText()
        monitor_delay = self.createdialog.monitor_edit.text()
        error_delay = self.createdialog.error_edit.text()
        qty = self.createdialog.qty_spinbox.value()
        if site != "Site" and product != "" and profile != "Profile" and profile != 'Account':
            for i in range(self.createdialog.taskcount_spinbox.value()):
                self.homepage.verticalLayout.takeAt(self.homepage.verticalLayout.count()-1)
                tab = TaskTab(
                    site,
                    product,
                    info,
                    size,
                    profile,
                    proxies,
                    mode,
                    monitor_delay,
                    error_delay,
                    captcha_type,
                    qty,
                    self.homepage.stop_all_tasks,
                    self.homepage.scrollAreaWidgetContents)
                self.homepage.verticalLayout.addWidget(tab)
                spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
                self.homepage.verticalLayout.addItem(spacerItem) 
        
#(.*)
if __name__ == "__main__":
    ui_app = QtWidgets.QApplication(sys.argv)
    ui = MainWindow()
    ui.setWindowIcon(QtGui.QIcon("images/pibot.png"))
    os._exit(ui_app.exec_())


