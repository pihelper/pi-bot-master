from PyQt5 import QtCore, QtGui, QtWidgets
from sites.okdo import Okdo
from sites.pishop import PiShop
from sites.shop import Shop
from pages.createdialog import CreateDialog
from sites.sparkfun import Sparkfun
from utils import get_profile, PiLogger, return_data, write_data, get_proxy_list, create_settings
import urllib.request,sys,platform

def no_abort(a, b, c):
    sys.__excepthook__(a, b, c)
sys.excepthook = no_abort
logger = PiLogger()
class HomePage(QtWidgets.QWidget):
    def __init__(self,parent=None):
        super(HomePage, self).__init__(parent)
        self.setupUi(self)
        create_settings()
        self.load_tasks()
    def setupUi(self, homepage):
        global tasks
        self.tasks = []
        tasks = self.tasks
        self.homepage = homepage
        self.homepage.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.homepage.setGeometry(QtCore.QRect(60, 0, 1041, 601))
        self.tasks_card = QtWidgets.QWidget(self.homepage)
        self.tasks_card.setGeometry(QtCore.QRect(30, 110, 991, 461))
        self.tasks_card.setStyleSheet("background-color: #232323;border-radius: 20px;border: 1px solid #2e2d2d;")
        self.scrollArea = QtWidgets.QScrollArea(self.tasks_card)
        self.scrollArea.setGeometry(QtCore.QRect(20, 30, 951, 421))
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setStyleSheet("border:none;")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 951, 421))
        self.verticalLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setContentsMargins(0, -1, 0, -1)
        self.verticalLayout.setSpacing(2)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        #self.image_table_header = QtWidgets.QLabel(self.tasks_card)
        #self.image_table_header.setGeometry(QtCore.QRect(40, 7, 51, 31))
        #self.image_table_header.setText("Image")
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(15) if platform.system() == "Darwin" else font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        #self.image_table_header.setFont(font)
        #self.image_table_header.setStyleSheet("color: rgb(234, 239, 239);border: none;")
        self.product_table_header = QtWidgets.QLabel(self.tasks_card)
        self.product_table_header.setGeometry(QtCore.QRect(190, 7, 61, 31))
        self.product_table_header.setFont(font)
        self.product_table_header.setStyleSheet("color: rgb(234, 239, 239);border: none;")
        self.product_table_header.setText("Product")
        self.profile_table_header = QtWidgets.QLabel(self.tasks_card)
        self.profile_table_header.setGeometry(QtCore.QRect(575, 7, 61, 31))
        self.profile_table_header.setFont(font)
        self.profile_table_header.setStyleSheet("color: rgb(234, 239, 239);border: none;")
        self.profile_table_header.setText("Profile")
        self.status_table_header = QtWidgets.QLabel(self.tasks_card)
        self.status_table_header.setGeometry(QtCore.QRect(651, 7, 61, 31))
        self.status_table_header.setFont(font)
        self.status_table_header.setStyleSheet("color: rgb(234, 239, 239);border: none;")
        self.status_table_header.setText("Status")
        self.actions_table_header = QtWidgets.QLabel(self.tasks_card)
        self.actions_table_header.setGeometry(QtCore.QRect(890, 7, 61, 31))
        self.actions_table_header.setFont(font)
        self.actions_table_header.setStyleSheet("color: rgb(234, 239, 239);border: none;")
        self.actions_table_header.setText("Actions")
        self.site_table_header = QtWidgets.QLabel(self.tasks_card)
        self.site_table_header.setGeometry(QtCore.QRect(66, 7, 61, 31))
        self.site_table_header.setFont(font)
        self.site_table_header.setStyleSheet("color: rgb(234, 239, 239);border: none;")
        self.site_table_header.setText("Site")
        self.id_header = QtWidgets.QLabel(self.tasks_card)
        self.id_header.setGeometry(QtCore.QRect(20, 7, 31, 31))
        self.id_header.setFont(font)
        self.id_header.setStyleSheet("color: rgb(234, 239, 239);border: none;")
        self.id_header.setText("ID")
        self.tasks_header = QtWidgets.QLabel(self.homepage)
        self.tasks_header.setGeometry(QtCore.QRect(30, 10, 61, 31))
        self.tasks_header.setText("Tasks")
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(22) if platform.system() == "Darwin" else font.setPointSize(16)
        font.setBold(False)
        font.setWeight(50)
        self.tasks_header.setFont(font)
        self.tasks_header.setStyleSheet("color: rgb(234, 239, 239);")
        self.checkouts_card = QtWidgets.QWidget(self.homepage)
        self.checkouts_card.setGeometry(QtCore.QRect(440, 45, 171, 51))
        self.checkouts_card.setStyleSheet("background-color: #232323;border-radius: 10px;border: 1px solid #2e2d2d;")
        self.checkouts_label = QtWidgets.QLabel(self.checkouts_card)
        self.checkouts_label.setGeometry(QtCore.QRect(78, 10, 81, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16) if platform.system() == "Darwin" else font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.checkouts_label.setFont(font)
        self.checkouts_label.setStyleSheet("color: rgb(234, 239, 239);border: none;")
        self.checkouts_label.setText("Checkouts")
        self.checkouts_icon = QtWidgets.QLabel(self.checkouts_card)
        self.checkouts_icon.setGeometry(QtCore.QRect(10, 10, 31, 31))
        self.checkouts_icon.setStyleSheet("border: none;")
        self.checkouts_icon.setText("")
        self.checkouts_icon.setPixmap(QtGui.QPixmap(":/images/success.png"))
        self.checkouts_icon.setScaledContents(True)
        global checkouts_count
        self.checkouts_count = QtWidgets.QLabel(self.checkouts_card)
        checkouts_count = self.checkouts_count
        self.checkouts_count.setGeometry(QtCore.QRect(43, 10, 31, 31))
        self.checkouts_count.setFont(font)
        self.checkouts_count.setStyleSheet("color: #34C693;border: none;")
        self.checkouts_count.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.checkouts_count.setText("0")
        self.tasks_total_card = QtWidgets.QWidget(self.homepage)
        self.tasks_total_card.setGeometry(QtCore.QRect(30, 45, 181, 51))
        self.tasks_total_card.setStyleSheet("background-color: #232323;border-radius: 10px;border: 1px solid #2e2d2d;")
        self.tasks_total_label = QtWidgets.QLabel(self.tasks_total_card)
        self.tasks_total_label.setGeometry(QtCore.QRect(80, 10, 91, 31))
        self.tasks_total_label.setFont(font)
        self.tasks_total_label.setStyleSheet("color: rgb(234, 239, 239);border: none;")
        self.tasks_total_label.setText("Total Tasks")
        self.tasks_total_icon = QtWidgets.QLabel(self.tasks_total_card)
        self.tasks_total_icon.setGeometry(QtCore.QRect(10, 10, 31, 31))
        self.tasks_total_icon.setStyleSheet("border: none;")
        self.tasks_total_icon.setText("")
        self.tasks_total_icon.setPixmap(QtGui.QPixmap("images/tasks.png"))
        self.tasks_total_icon.setScaledContents(True)
        global tasks_total_count
        self.tasks_total_count = QtWidgets.QLabel(self.tasks_total_card)
        tasks_total_count = self.tasks_total_count
        self.tasks_total_count.setGeometry(QtCore.QRect(43, 10, 31, 31))
        self.tasks_total_count.setFont(font)
        self.tasks_total_count.setStyleSheet("color: #60a8ce;border: none;")
        self.tasks_total_count.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.tasks_total_count.setText("0")
        self.carted_card = QtWidgets.QWidget(self.homepage)
        self.carted_card.setGeometry(QtCore.QRect(240, 45, 171, 51))
        self.carted_card.setStyleSheet("background-color: #232323;border-radius: 10px;border: 1px solid #2e2d2d;")
        self.carted_label = QtWidgets.QLabel(self.carted_card)
        self.carted_label.setGeometry(QtCore.QRect(80, 10, 90, 31))
        self.carted_label.setFont(font)
        self.carted_label.setStyleSheet("color: rgb(234, 239, 239);border: none;")
        self.carted_label.setText("Total Carts")
        self.carted_icon = QtWidgets.QLabel(self.carted_card)
        self.carted_icon.setGeometry(QtCore.QRect(10, 10, 31, 31))
        self.carted_icon.setStyleSheet("border: none;")
        self.carted_icon.setText("")
        self.carted_icon.setPixmap(QtGui.QPixmap(":/images/cart.png"))
        self.carted_icon.setScaledContents(True)
        global carted_count
        self.carted_count = QtWidgets.QLabel(self.carted_card)
        carted_count = self.carted_count
        self.carted_count.setGeometry(QtCore.QRect(43, 10, 31, 31))
        self.carted_count.setFont(font)
        self.carted_count.setStyleSheet("color: #F6905E;border: none;")
        self.carted_count.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.carted_count.setText("0")
        self.buttons_card = QtWidgets.QWidget(self.homepage)
        self.buttons_card.setGeometry(QtCore.QRect(640, 45, 381, 51))
        self.buttons_card.setStyleSheet("background-color: #232323;border-radius: 10px;border: 1px solid #2e2d2d;")
        self.startall_btn = QtWidgets.QPushButton(self.buttons_card)
        self.startall_btn.setGeometry(QtCore.QRect(103, 10, 86, 32))
        font = QtGui.QFont()
        font.setFamily("Arial")
        self.startall_btn.setFont(font)
        self.startall_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.startall_btn.setStyleSheet("color: #FFFFFF;background-color: #60a8ce;border: none;")
        self.startall_btn.setText("Start All")
        self.startall_btn.clicked.connect(self.start_all_tasks)
        self.stopall_btn = QtWidgets.QPushButton(self.buttons_card)
        self.stopall_btn.setGeometry(QtCore.QRect(197, 10, 81, 32))
        self.stopall_btn.setFont(font)
        self.stopall_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.stopall_btn.setStyleSheet("color: #FFFFFF;background-color: #60a8ce;border: none;")
        self.stopall_btn.setText("Stop All")
        self.stopall_btn.clicked.connect(self.stop_all_tasks)
        self.deleteall_btn = QtWidgets.QPushButton(self.buttons_card)
        self.deleteall_btn.setGeometry(QtCore.QRect(285, 10, 86, 32))
        self.deleteall_btn.setFont(font)
        self.deleteall_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.deleteall_btn.setStyleSheet("color: #FFFFFF;background-color: #60a8ce;border: none;")
        self.deleteall_btn.setText("Delete All")
        self.deleteall_btn.clicked.connect(self.delete_all_tasks)
        self.newtask_btn = QtWidgets.QPushButton(self.buttons_card)
        self.newtask_btn.setGeometry(QtCore.QRect(10, 10, 86, 32))
        self.newtask_btn.setFont(font)
        self.newtask_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.newtask_btn.setStyleSheet("color: #FFFFFF;background-color: #60a8ce;border: none;")
        self.newtask_btn.setText("New Task")
        QtCore.QMetaObject.connectSlotsByName(homepage)



    def load_tasks(self):
        tasks_data = return_data("./data/tasks.json")
        write_data("./data/tasks.json",[])
        try:
            for task in tasks_data:
                tab = TaskTab(task["site"],task["product"], task["info"], task["size"],task["profile"],task["proxies"],task["monitor_delay"], task["error_delay"], task["captcha_type"], task['qty'],self.stop_all_tasks,self.scrollAreaWidgetContents)
                self.verticalLayout.takeAt(self.verticalLayout.count()-1)
                self.verticalLayout.addWidget(tab)
                spacerItem = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
                self.verticalLayout.addItem(spacerItem)
        except:
            pass

    def set_settings_data(self,settings_data):
        global settings
        settings = settings_data

    def start_all_tasks(self):
        for task in self.tasks:
            try:
                task.start(None)
            except:
                pass
    def stop_all_tasks(self):
        for task in self.tasks:
            try:
                task.stop(None)
            except:
                pass

        from app import MainWindow
        MainWindow.spark_started = False
        MainWindow.pishop_started = False

    def delete_all_tasks(self):
        for task in self.tasks:
            try:
                task.delete(None)
            except:
                pass

class TaskTab(QtWidgets.QWidget):
    def __init__(self,site,product, info, size,profile,proxies,monitor_delay,error_delay,captcha_type,qty,stop_all,parent=None):
        super(TaskTab, self).__init__(parent)
        self.task_id = str(int(tasks_total_count.text())+1)
        tasks_total_count.setText(self.task_id)
        self.site,self.product,self.info, self.size, self.profile,self.proxies, self.monitor_delay, self.error_delay, self.captcha_type,self.qty, self.stop_all = site,product, info, size,profile,proxies,monitor_delay, error_delay,captcha_type, qty,stop_all
        self.setupUi(self)
        tasks.append(self)
        tasks_data = return_data("./data/tasks.json")
        task_data = {"task_id": self.task_id,"site":self.site,"product": self.product, "info" : self.info, "size" : self.size,"profile": self.profile,"proxies": self.proxies, "monitor_delay": self.monitor_delay, "error_delay": self.error_delay,"captcha_type":self.captcha_type, 'qty': self.qty}
        tasks_data.append(task_data)
        write_data("./data/tasks.json",tasks_data)
    def setupUi(self,TaskTab):
        self.running = False

        self.TaskTab = TaskTab
        self.TaskTab.setMinimumSize(QtCore.QSize(0, 32))
        self.TaskTab.setMaximumSize(QtCore.QSize(16777215, 50))
        self.TaskTab.setStyleSheet("border-radius: none;")
        self.product_label = QtWidgets.QLabel(self.TaskTab)
        self.product_label.setGeometry(QtCore.QRect(170, 10, 331, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(13) if platform.system() == "Darwin" else font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.product_label.setFont(font)
        self.product_label.setStyleSheet("color: rgb(234, 239, 239);")
        self.profile_label = QtWidgets.QLabel(self.TaskTab)
        self.profile_label.setGeometry(QtCore.QRect(555, 10, 70, 31))
        self.profile_label.setFont(font)
        self.profile_label.setStyleSheet("color: rgb(234, 239, 239);")
        self.status_label = QtWidgets.QLabel(self.TaskTab)
        self.status_label.setGeometry(QtCore.QRect(632, 10, 231, 31))
        self.status_label.setFont(font)
        self.status_label.setStyleSheet("color: rgb(234, 239, 239);")
        self.browser_label = QtWidgets.QLabel(self.TaskTab)
        self.browser_label.setGeometry(QtCore.QRect(632, 10, 231, 31))
        self.browser_label.setFont(font)
        self.browser_label.setStyleSheet("color: rgb(163, 149, 255);")
        self.browser_label.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.browser_label.hide()
        self.start_btn = QtWidgets.QLabel(self.TaskTab)
        self.start_btn.setGeometry(QtCore.QRect(870, 15, 16, 16))
        self.start_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.start_btn.setPixmap(QtGui.QPixmap("images/play.png"))
        self.start_btn.setScaledContents(True)
        self.start_btn.mousePressEvent = self.start
        self.stop_btn = QtWidgets.QLabel(self.TaskTab)
        self.stop_btn.setGeometry(QtCore.QRect(870, 15, 16, 16))
        self.stop_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.stop_btn.setPixmap(QtGui.QPixmap("images/stop.png"))
        self.stop_btn.setScaledContents(True)
        self.stop_btn.mousePressEvent = self.stop
        self.delete_btn = QtWidgets.QLabel(self.TaskTab)
        self.delete_btn.setGeometry(QtCore.QRect(920, 15, 16, 16))
        self.delete_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.delete_btn.setPixmap(QtGui.QPixmap("images/trash.png"))
        self.delete_btn.setScaledContents(True)
        self.delete_btn.mousePressEvent = self.delete
        self.edit_btn = QtWidgets.QLabel(self.TaskTab)
        self.edit_btn.setGeometry(QtCore.QRect(895, 15, 16, 16))
        self.edit_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.edit_btn.setPixmap(QtGui.QPixmap("images/edit.png"))
        self.edit_btn.setScaledContents(True)
        self.edit_btn.mousePressEvent = self.edit
        self.site_label = QtWidgets.QLabel(self.TaskTab)
        self.site_label.setGeometry(QtCore.QRect(45, 10, 100, 31))
        self.site_label.setFont(font)
        self.site_label.setStyleSheet("color: rgb(234, 239, 239);")
        self.id_label = QtWidgets.QLabel(self.TaskTab)
        self.id_label.setGeometry(QtCore.QRect(3, 10, 31, 31))
        self.id_label.setFont(font)
        self.id_label.setStyleSheet("color: rgb(234, 239, 239);")
        self.stop_btn.raise_()
        self.product_label.raise_()
        self.profile_label.raise_()
        self.browser_label.raise_()
        self.start_btn.raise_()
        self.delete_btn.raise_()
        #self.image.raise_()
        self.site_label.raise_()
        self.info_label = QtWidgets.QLabel(self.TaskTab)
        self.info_label.hide()
        self.captcha_label = QtWidgets.QLabel(self.TaskTab)
        self.captcha_label.hide()
        self.size_label = QtWidgets.QLabel(self.TaskTab)
        self.size_label.hide()
        self.monitor_label = QtWidgets.QLabel(self.TaskTab)
        self.monitor_label.hide()
        self.error_label = QtWidgets.QLabel(self.TaskTab)
        self.error_label.hide()
        self.proxies_label = QtWidgets.QLabel(self.TaskTab)
        self.proxies_label.hide()
        self.qty_label = QtWidgets.QLabel(self.TaskTab)
        self.qty_label.hide()
        self.load_labels()

    def load_labels(self):
        self.id_label.setText(self.task_id)
        self.product_label.setText(self.product)
        self.profile_label.setText(self.profile)
        self.proxies_label.setText(self.proxies)
        self.status_label.setText("Idle")
        self.browser_label.setText("Click To Open Browser")
        self.site_label.setText(self.site)
        self.info_label.setText(self.info)
        self.size_label.setText(self.size)
        self.monitor_label.setText(self.monitor_delay)
        self.error_label.setText(self.error_delay)
        self.captcha_label.setText(self.captcha_type)
        self.qty_label.setText(str(self.qty))
    def update_status(self,msg):
        self.status_label.setText(msg["msg"])
        # monitoring and checking are just 'idle' and 'normal' with no logging
        if msg["status"] == "monitoring":
            self.status_label.setStyleSheet("color: rgb(255, 255, 255);")
        elif msg["status"] == "checking":
            self.status_label.setStyleSheet("color: rgb(89, 162, 201);")
        elif msg["status"] == "idle":
            self.status_label.setStyleSheet("color: rgb(255, 255, 255);")
            logger.normal(self.task_id,msg["msg"])
        elif msg["status"] == "normal":
            self.status_label.setStyleSheet("color: rgb(89, 162, 201);")
            logger.normal(self.task_id,msg["msg"])
        elif msg["status"] == "alt":
            self.status_label.setStyleSheet("color: rgb(242, 166, 137);")
            logger.alt(self.task_id,msg["msg"])
        elif msg["status"] == "error_no_log":
            self.status_label.setStyleSheet("color: rgb(252, 81, 81);")
        elif msg["status"] == "error":
            self.status_label.setStyleSheet("color: rgb(252, 81, 81);")
            logger.error(self.task_id,msg["msg"])
        elif msg["status"] == "success":
            self.status_label.setStyleSheet("color: rgb(52, 198, 147);")
            logger.success(self.task_id,msg["msg"])
            self.running = False
            self.start_btn.raise_()
            checkouts_count.setText(str(int(checkouts_count.text())+1))
        elif msg["status"] == "carted":
            self.status_label.setStyleSheet("color: rgb(163, 149, 255);")
            logger.alt(self.task_id,msg["msg"])
            carted_count.setText(str(int(carted_count.text())+1))

    def update_product(self, msg):
        self.product_label.setText(msg)

    def set_image(self,pixmap):
        self.image.setPixmap(pixmap)

    def start(self,event):
        if not self.running:
            self.browser_label.hide()
            self.task = TaskThread()
            self.task.status_signal.connect(self.update_status)
            self.task.product_signal.connect(self.update_product)
            self.task.set_data(
                self.task_id,
                self.site_label.text(),
                self.product_label.text(),
                self.info_label.text(),
                self.size_label.text(),
                self.profile_label.text(),
                self.proxies_label.text(),
                self.monitor_label.text(),
                self.error_label.text(),
                self.captcha_label.text(),
                self.qty_label.text()
            )
            self.task.start()
            self.running = True
            self.stop_btn.raise_()

    def stop(self,event):
        self.task.stop()
        self.running = False
        self.product_label.setText(self.product)
        self.update_status({"msg":"Stopped","status":"idle"})
        self.start_btn.raise_()
        from app import MainWindow
        MainWindow.spark_started = False
        MainWindow.pishop_started = False


    def edit(self,event):
        self.edit_dialog = CreateDialog()
        self.edit_dialog.setWindowTitle('Update Task')
        self.edit_dialog.addtask_btn.clicked.connect(self.update_task)
        self.edit_dialog.taskcount_spinbox.hide()
        self.edit_dialog.profile_box.clear()
        self.edit_dialog.proxies_box.clear()
        profile_combobox = self.parent().parent().parent().parent().parent().parent().parent().createdialog.profile_box
        for profile in [profile_combobox.itemText(i) for i in range(profile_combobox.count())]:
            self.edit_dialog.profile_box.addItem(profile)
        proxies_combobox = self.parent().parent().parent().parent().parent().parent().parent().createdialog.proxies_box
        for proxy in [proxies_combobox.itemText(i) for i in range(proxies_combobox.count())]:
            self.edit_dialog.proxies_box.addItem(proxy)
        self.edit_dialog.load_data(self)
        if 'Sparkfun' in self.edit_dialog.site_box.currentText():
            self.edit_dialog.setFixedSize(647, 175)
            self.edit_dialog.addtask_btn.setGeometry(QtCore.QRect(250, 125, 151, 32))
        self.edit_dialog.show()

    def update_task(self):
        self.site=self.edit_dialog.site_box.currentText()
        if 'Sparkfun' in self.site:
            self.product = self.edit_dialog.link.text()
            self.info = self.edit_dialog.link.text()
            self.size = f'{self.edit_dialog.account_user.text()}|{self.edit_dialog.account_pass.text()}'
        elif 'PiShop' in self.site or 'OKDO' in self.site:
            self.product = self.edit_dialog.link.text()
            self.info = self.edit_dialog.link.text()
            self.size = ''
        else:
            self.product=self.edit_dialog.shopify_select.currentText()
            self.info = self.info_label.text()
            self.size = self.size_label.text()
        self.profile=self.edit_dialog.profile_box.currentText()
        self.proxies=self.edit_dialog.proxies_box.currentText()
        self.monitor_delay = self.edit_dialog.monitor_edit.text()
        self.error_delay = self.edit_dialog.error_edit.text()
        self.captcha_type = self.edit_dialog.captcha_box.currentText()
        self.qty = self.edit_dialog.qty_spinbox.value()
        self.load_labels()
        self.delete_json()
        tasks_data = return_data("./data/tasks.json")
        task_data = {"task_id": self.task_id, "site": self.site, "product": self.product, "info": self.info, "size": self.size, "profile": self.profile,
                     "proxies": self.proxies, "monitor_delay": self.monitor_delay, "error_delay": self.error_delay,"captcha_type":self.captcha_type, 'qty': self.qty}
        tasks_data.append(task_data)
        write_data("./data/tasks.json",tasks_data)
        self.edit_dialog.deleteLater()

    def delete_json(self):
        tasks_data = return_data("./data/tasks.json")
        for task in tasks_data:
            if task["task_id"] == self.task_id:
                tasks_data.remove(task)
                break
        write_data("./data/tasks.json", tasks_data)

    def delete(self,event):
        tasks_total_count.setText(str(int(tasks_total_count.text()) - 1))
        self.delete_json()
        self.TaskTab.deleteLater()

class TaskThread(QtCore.QThread):
    status_signal = QtCore.pyqtSignal("PyQt_PyObject")
    product_signal = QtCore.pyqtSignal("PyQt_PyObject")
    def __init__(self):
        QtCore.QThread.__init__(self)

    def set_data(self,task_id,site,product,info,size,profile,proxies,monitor_delay,error_delay,captcha_type,qty):
        self.task_id,self.site,self.product,self.info,self.size,self.profile,self.proxies,self.monitor_delay,self.error_delay, self.captcha_type, self.qty = task_id,site,product,info,size,profile,proxies,monitor_delay,error_delay,captcha_type, qty

    def run(self):
        profile,proxy = get_profile(self.profile),get_proxy_list(self.proxies)
        if profile == None:
            self.status_signal.emit({"msg":"Invalid profile","status":"error"})
            return
        if proxy == None:
            self.status_signal.emit({"msg":"Invalid proxy list","status":"error"})
            return

        if 'PiShop' in self.site:
            PiShop(self.task_id, self.status_signal, self.product_signal, self.product, self.info, self.size, profile,
                 proxy, self.monitor_delay, self.error_delay,self.captcha_type, self.qty)
        elif 'Sparkfun' in self.site:
            account_info = self.size.split('|')
            if account_info[0] == '':
                self.status_signal.emit({"msg": "Email field empty", "status": "error"})
            elif account_info[1] == '':
                self.status_signal.emit({"msg": "Password field empty", "status": "error"})
            else:
                Sparkfun(self.task_id, self.status_signal, self.product_signal, self.product, self.size, profile,
                   proxy, self.monitor_delay, self.error_delay, self.captcha_type,self.qty)
        elif 'OKDO' in self.site:
            Okdo(self.task_id, self.status_signal, self.product_signal, self.product, self.info, self.size, profile,
                 proxy, self.monitor_delay, self.error_delay,self.captcha_type, self.qty)
        else:
            Shop(self.task_id, self.status_signal, self.product_signal, self.product, self.info, self.size, profile, proxy, self.monitor_delay,self.error_delay)

    def stop(self):
        self.terminate()

class ImageThread(QtCore.QThread):
    finished_signal = QtCore.pyqtSignal("PyQt_PyObject")
    def __init__(self,image_url):
        self.image_url = image_url
        QtCore.QThread.__init__(self)

    def run(self):
        data = urllib.request.urlopen(self.image_url).read()
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(data)
        self.finished_signal.emit(pixmap)


