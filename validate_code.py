import ctypes
import sys

import requests
import userpaths
import wmi
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QFontDatabase, QFont, QIntValidator


class Ui_MainWindow(object):
    style_sheet = ""
    style_sheet_button = ""

    def __init__(self):
        pass

    def validate(self, event):
        code = self.lineEdit.text()
        if code.__len__() != 6:
            return
        response = self.send_request(code)
        if response['result'].__contains__("not found"):
            ctypes.windll.user32.MessageBoxW(0, "This code doesn't exists!", "Wrong code", 0)
            return
        else:
            ctypes.windll.user32.MessageBoxW(0, "Successfully registered!", "Correct code", 0)
            path = userpaths.get_local_appdata() + '\MrPowerManager'
            token, pc_name = [response['token'], response['pcName']]
            self.send_battery_capacity(token, pc_name)
            open(path + '\config.dat', "w").write(token + "@@@" + pc_name)
        QCoreApplication.quit()
        return

    def send_request(self, code):
        url = 'https://mrpowermanager.herokuapp.com/validateCode'
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json'
        }
        params = {
            'code': code,
        }

        response = requests.get(url, headers=headers, params=params)
        return dict(response.json())

    def send_battery_capacity(self, token, pc_name):
        c = wmi.WMI()
        t = wmi.WMI(moniker="//./root/wmi")
        batts1 = c.CIM_Battery(Caption='Portable Battery')
        batts = t.ExecQuery('Select * from BatteryFullChargedCapacity')

        capacity = 30000
        if len(batts) > 0:
            capacity = batts[0].FullChargedCapacity
        elif len(batts1) > 0:
            capacity = batts1[0].DesignCapacity

        url = 'https://mrpowermanager.herokuapp.com/addPcBatteryCapacity'
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json'
        }
        params = {
            'token': token,
            'pcName': pc_name,
            'value': capacity
        }

        requests.post(url, headers=headers, params=params)

    def setupUi(self, MainWindow):
        id = QFontDatabase.addApplicationFont("ui/lcd.ttf")
        families_lcd = QFontDatabase.applicationFontFamilies(id)

        style_sheet = open("ui/style_sheet").read()
        style_sheet_button = open("ui/style_sheet_button").read()
        MainWindow.setObjectName("Validate code")
        MainWindow.setWindowModality(QtCore.Qt.WindowModality.NonModal)
        MainWindow.resize(551, 304)
        palette = QtGui.QPalette()
        gradient = QtGui.QRadialGradient(0.5, 0.5, 0.5, 0.5, 0.5)
        gradient.setSpread(QtGui.QGradient.Spread.PadSpread)
        gradient.setCoordinateMode(QtGui.QGradient.CoordinateMode.ObjectBoundingMode)
        gradient.setColorAt(0.0, QtGui.QColor(70, 70, 70))
        gradient.setColorAt(1.0, QtGui.QColor(35, 35, 35))
        brush = QtGui.QBrush(gradient)
        palette.setBrush(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Button, brush)
        gradient = QtGui.QRadialGradient(0.5, 0.5, 0.5, 0.5, 0.5)
        gradient.setSpread(QtGui.QGradient.Spread.PadSpread)
        gradient.setCoordinateMode(QtGui.QGradient.CoordinateMode.ObjectBoundingMode)
        gradient.setColorAt(0.0, QtGui.QColor(70, 70, 70))
        gradient.setColorAt(1.0, QtGui.QColor(35, 35, 35))
        brush = QtGui.QBrush(gradient)
        palette.setBrush(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Base, brush)
        gradient = QtGui.QRadialGradient(0.5, 0.5, 0.5, 0.5, 0.5)
        gradient.setSpread(QtGui.QGradient.Spread.PadSpread)
        gradient.setCoordinateMode(QtGui.QGradient.CoordinateMode.ObjectBoundingMode)
        gradient.setColorAt(0.0, QtGui.QColor(70, 70, 70))
        gradient.setColorAt(1.0, QtGui.QColor(35, 35, 35))
        brush = QtGui.QBrush(gradient)
        palette.setBrush(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Window, brush)
        gradient = QtGui.QRadialGradient(0.5, 0.5, 0.5, 0.5, 0.5)
        gradient.setSpread(QtGui.QGradient.Spread.PadSpread)
        gradient.setCoordinateMode(QtGui.QGradient.CoordinateMode.ObjectBoundingMode)
        gradient.setColorAt(0.0, QtGui.QColor(70, 70, 70))
        gradient.setColorAt(1.0, QtGui.QColor(35, 35, 35))
        brush = QtGui.QBrush(gradient)
        palette.setBrush(QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.Button, brush)
        gradient = QtGui.QRadialGradient(0.5, 0.5, 0.5, 0.5, 0.5)
        gradient.setSpread(QtGui.QGradient.Spread.PadSpread)
        gradient.setCoordinateMode(QtGui.QGradient.CoordinateMode.ObjectBoundingMode)
        gradient.setColorAt(0.0, QtGui.QColor(70, 70, 70))
        gradient.setColorAt(1.0, QtGui.QColor(35, 35, 35))
        brush = QtGui.QBrush(gradient)
        palette.setBrush(QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.Base, brush)
        gradient = QtGui.QRadialGradient(0.5, 0.5, 0.5, 0.5, 0.5)
        gradient.setSpread(QtGui.QGradient.Spread.PadSpread)
        gradient.setCoordinateMode(QtGui.QGradient.CoordinateMode.ObjectBoundingMode)
        gradient.setColorAt(0.0, QtGui.QColor(70, 70, 70))
        gradient.setColorAt(1.0, QtGui.QColor(35, 35, 35))
        brush = QtGui.QBrush(gradient)
        palette.setBrush(QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.Window, brush)
        gradient = QtGui.QRadialGradient(0.5, 0.5, 0.5, 0.5, 0.5)
        gradient.setSpread(QtGui.QGradient.Spread.PadSpread)
        gradient.setCoordinateMode(QtGui.QGradient.CoordinateMode.ObjectBoundingMode)
        gradient.setColorAt(0.0, QtGui.QColor(70, 70, 70))
        gradient.setColorAt(1.0, QtGui.QColor(35, 35, 35))
        brush = QtGui.QBrush(gradient)
        palette.setBrush(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Button, brush)
        gradient = QtGui.QRadialGradient(0.5, 0.5, 0.5, 0.5, 0.5)
        gradient.setSpread(QtGui.QGradient.Spread.PadSpread)
        gradient.setCoordinateMode(QtGui.QGradient.CoordinateMode.ObjectBoundingMode)
        gradient.setColorAt(0.0, QtGui.QColor(70, 70, 70))
        gradient.setColorAt(1.0, QtGui.QColor(35, 35, 35))
        brush = QtGui.QBrush(gradient)
        palette.setBrush(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Base, brush)
        gradient = QtGui.QRadialGradient(0.5, 0.5, 0.5, 0.5, 0.5)
        gradient.setSpread(QtGui.QGradient.Spread.PadSpread)
        gradient.setCoordinateMode(QtGui.QGradient.CoordinateMode.ObjectBoundingMode)
        gradient.setColorAt(0.0, QtGui.QColor(70, 70, 70))
        gradient.setColorAt(1.0, QtGui.QColor(35, 35, 35))
        brush = QtGui.QBrush(gradient)
        palette.setBrush(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Window, brush)
        MainWindow.setPalette(palette)
        MainWindow.setWindowOpacity(1.9)
        MainWindow.setAutoFillBackground(False)
        MainWindow.setStyleSheet(style_sheet)
        MainWindow.setTabShape(QtWidgets.QTabWidget.TabShape.Triangular)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(41, 30, 481, 111))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lineEdit = QtWidgets.QLineEdit(self.verticalLayoutWidget)
        font = QFont(families_lcd[0], 84)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 26)
        self.lineEdit.setFont(font)
        self.lineEdit.setStyleSheet("background-color: rgb(80, 80,80);\n"
                                    "color: rgb(169, 211, 255);")
        self.lineEdit.setObjectName("lineEdit")
        self.lineEdit.setValidator(QIntValidator(0, 999999, None))
        self.verticalLayout.addWidget(self.lineEdit)
        self.pushButton_4 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_4.setEnabled(True)
        self.pushButton_4.setGeometry(QtCore.QRect(290, 180, 231, 91))
        self.pushButton_4.mousePressEvent = self.validate
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum,
                                           QtWidgets.QSizePolicy.Policy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_4.sizePolicy().hasHeightForWidth())
        self.pushButton_4.setSizePolicy(sizePolicy)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(17, 17, 17))
        brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)
        palette.setBrush(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.WindowText, brush)
        gradient = QtGui.QLinearGradient(0.0, 0.0, 1.0, 1.0)
        gradient.setSpread(QtGui.QGradient.Spread.PadSpread)
        gradient.setCoordinateMode(QtGui.QGradient.CoordinateMode.ObjectBoundingMode)
        gradient.setColorAt(0.0, QtGui.QColor(254, 255, 172))
        gradient.setColorAt(1.0, QtGui.QColor(175, 147, 80))
        brush = QtGui.QBrush(gradient)
        palette.setBrush(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(17, 17, 17))
        brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)
        palette.setBrush(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(17, 17, 17))
        brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)
        palette.setBrush(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.ButtonText, brush)
        gradient = QtGui.QLinearGradient(0.0, 0.0, 1.0, 1.0)
        gradient.setSpread(QtGui.QGradient.Spread.PadSpread)
        gradient.setCoordinateMode(QtGui.QGradient.CoordinateMode.ObjectBoundingMode)
        gradient.setColorAt(0.0, QtGui.QColor(254, 255, 172))
        gradient.setColorAt(1.0, QtGui.QColor(175, 147, 80))
        brush = QtGui.QBrush(gradient)
        palette.setBrush(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Base, brush)
        gradient = QtGui.QLinearGradient(0.0, 0.0, 1.0, 1.0)
        gradient.setSpread(QtGui.QGradient.Spread.PadSpread)
        gradient.setCoordinateMode(QtGui.QGradient.CoordinateMode.ObjectBoundingMode)
        gradient.setColorAt(0.0, QtGui.QColor(254, 255, 172))
        gradient.setColorAt(1.0, QtGui.QColor(175, 147, 80))
        brush = QtGui.QBrush(gradient)
        palette.setBrush(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(17, 17, 17))
        brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)
        palette.setBrush(QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.WindowText, brush)
        gradient = QtGui.QLinearGradient(0.0, 0.0, 1.0, 1.0)
        gradient.setSpread(QtGui.QGradient.Spread.PadSpread)
        gradient.setCoordinateMode(QtGui.QGradient.CoordinateMode.ObjectBoundingMode)
        gradient.setColorAt(0.0, QtGui.QColor(254, 255, 172))
        gradient.setColorAt(1.0, QtGui.QColor(175, 147, 80))
        brush = QtGui.QBrush(gradient)
        palette.setBrush(QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(17, 17, 17))
        brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)
        palette.setBrush(QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(17, 17, 17))
        brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)
        palette.setBrush(QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.ButtonText, brush)
        gradient = QtGui.QLinearGradient(0.0, 0.0, 1.0, 1.0)
        gradient.setSpread(QtGui.QGradient.Spread.PadSpread)
        gradient.setCoordinateMode(QtGui.QGradient.CoordinateMode.ObjectBoundingMode)
        gradient.setColorAt(0.0, QtGui.QColor(254, 255, 172))
        gradient.setColorAt(1.0, QtGui.QColor(175, 147, 80))
        brush = QtGui.QBrush(gradient)
        palette.setBrush(QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.Base, brush)
        gradient = QtGui.QLinearGradient(0.0, 0.0, 1.0, 1.0)
        gradient.setSpread(QtGui.QGradient.Spread.PadSpread)
        gradient.setCoordinateMode(QtGui.QGradient.CoordinateMode.ObjectBoundingMode)
        gradient.setColorAt(0.0, QtGui.QColor(254, 255, 172))
        gradient.setColorAt(1.0, QtGui.QColor(175, 147, 80))
        brush = QtGui.QBrush(gradient)
        palette.setBrush(QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(174, 167, 159))
        brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)
        palette.setBrush(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.WindowText, brush)
        gradient = QtGui.QLinearGradient(0.5, 1.0, 0.5, 0.0)
        gradient.setSpread(QtGui.QGradient.Spread.PadSpread)
        gradient.setCoordinateMode(QtGui.QGradient.CoordinateMode.ObjectBoundingMode)
        gradient.setColorAt(0.0, QtGui.QColor(200, 200, 200))
        gradient.setColorAt(1.0, QtGui.QColor(230, 230, 230))
        brush = QtGui.QBrush(gradient)
        palette.setBrush(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(174, 167, 159))
        brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)
        palette.setBrush(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(174, 167, 159))
        brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)
        palette.setBrush(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.ButtonText, brush)
        gradient = QtGui.QLinearGradient(0.5, 1.0, 0.5, 0.0)
        gradient.setSpread(QtGui.QGradient.Spread.PadSpread)
        gradient.setCoordinateMode(QtGui.QGradient.CoordinateMode.ObjectBoundingMode)
        gradient.setColorAt(0.0, QtGui.QColor(200, 200, 200))
        gradient.setColorAt(1.0, QtGui.QColor(230, 230, 230))
        brush = QtGui.QBrush(gradient)
        palette.setBrush(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Base, brush)
        gradient = QtGui.QLinearGradient(0.5, 1.0, 0.5, 0.0)
        gradient.setSpread(QtGui.QGradient.Spread.PadSpread)
        gradient.setCoordinateMode(QtGui.QGradient.CoordinateMode.ObjectBoundingMode)
        gradient.setColorAt(0.0, QtGui.QColor(200, 200, 200))
        gradient.setColorAt(1.0, QtGui.QColor(230, 230, 230))
        brush = QtGui.QBrush(gradient)
        palette.setBrush(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Window, brush)
        self.pushButton_4.setPalette(palette)
        font = QtGui.QFont()
        font.setFamily("Consolas")
        font.setPointSize(22)
        font.setBold(True)
        font.setItalic(True)
        font.setWeight(75)
        self.pushButton_4.setFont(font)
        self.pushButton_4.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_4.setMouseTracking(False)
        self.pushButton_4.setAutoFillBackground(False)
        self.pushButton_4.setStyleSheet(style_sheet_button)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("ui/star.ico"),
                       QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pushButton_4.setIcon(icon)
        self.pushButton_4.setIconSize(QtCore.QSize(60, 60))
        self.pushButton_4.setObjectName("pushButton_4")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 551, 20))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton_4.setText(_translate("MainWindow", "Confirm"))




if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
