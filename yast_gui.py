from PyQt4 import QtGui
from ui_mainwindow import Ui_MainWindow
import sys


class YastGui(QtGui.QMainWindow):
    def __init__(self):
        super(YastGui, self).__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Set on click event for all buttons
        self.ui.B_choose_file.clicked.connect(self.choose_file)
        self.ui.B_Close.clicked.connect(self.close_application)
        self.ui.B_Save.clicked.connect(self.file_save)
        self.ui.actionOpen.triggered.connect(self.choose_file)
        self.ui.actionOpen.setShortcut("ctrl+O")
        self.ui.actionSave_As.triggered.connect(self.file_save)
        self.ui.actionSave_As.setShortcut("Ctrl+S")
        self.ui.actionExit.triggered.connect(self.close_application)

    def choose_file(self):
        """ On click event handler for choose file button """
        fname = QtGui.QFileDialog.getOpenFileName(
            self.ui.centralwidget, "YAST - Open Dialog")
        self.ui.file_path_textEdit.setText(fname)

    def close_application(self):
        choice = QtGui.QMessageBox.question(
            self.ui.centralwidget, "YAST - Warning!", "Do you want to Exit?",
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if choice == QtGui.QMessageBox.Yes:
            sys.exit()
        else:
            pass

    def file_save(self):
        name = QtGui.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'YAST - Save File')
        file = open(name, 'w')
        file.close()

def main():
    app = QtGui.QApplication(sys.argv)
    gui = YastGui()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()    
