# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'screen.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets
from gui.widgets.Button100x100 import Button100x100
import gui.screen
import os

url = os.path.dirname("./who-want-to-be-a-millionare/gui/")

class UI_TutorialScreen(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1280, 960)
        MainWindow.setAutoFillBackground(False)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        #title
        self.title = QtWidgets.QLabel(self.centralwidget)
        self.title.setGeometry(QtCore.QRect(0, 50, 1280, 100))
        self.title.setText("")
        self.title.setPixmap(QtGui.QPixmap(os.path.join(url, "images/how-to-play.png")))
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        self.title.setObjectName("title")
        
        #information
        self.information = QtWidgets.QLabel(self.centralwidget)
        self.information.setGeometry(QtCore.QRect(0, 160, 1280, 500))
        self.information.setText("")
        self.information.setPixmap(QtGui.QPixmap(os.path.join(url, "images/game-tutorial.png")))
        self.information.setAlignment(QtCore.Qt.AlignCenter)
        self.information.setObjectName("information")
        
        #play button        
        self.playBtn = Button100x100(self.centralwidget)
        self.playBtn.setName("playBtn")
        self.playBtn.setImage("images/play-btn.png")
        self.playBtn.move(QtCore.QPoint(440, 700))
        self.playBtn.clicked.connect(lambda: self.handleClickPlayButton(MainWindow))
        
        #exit button
        self.exitBtn = Button100x100(self.centralwidget)
        self.exitBtn.setName("playBtn")
        self.exitBtn.setImage("images/exit-btn.png")
        self.exitBtn.move(QtCore.QPoint(770, 700))
        self.exitBtn.clicked.connect(lambda: self.handleClickExitButton(MainWindow))
        
        #setup
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        
    def handleClickExitButton(self, MainWindow):
        MainWindow.close()
        
    def handleClickPlayButton(self, MainWindow):
        ui = gui.screen.UI_MainMenu()
        ui.setupUi(MainWindow)
        MainWindow.show()
