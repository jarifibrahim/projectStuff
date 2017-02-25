from PyQt4 import QtGui
from ui_mainwindow import Ui_MainWindow
import sys
from yast import Yast, LogFile


class YastGui(QtGui.QMainWindow):
    def __init__(self):
        super(YastGui, self).__init__()

        # main log file object
        self.log_file = None

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Disable frames
        self.ui.token_frame.setEnabled(False)
        self.ui.clean_frame.setEnabled(False)
        self.ui.session_frame.setEnabled(False)

        # Set on click event for all buttons
        self.ui.B_choose_file.clicked.connect(self.choose_file)
        self.ui.file_path_textEdit.textChanged.connect(
            lambda x: self.ui.token_frame.setEnabled(True))
        self.ui.B_Close.clicked.connect(self.close_application)
        self.ui.B_Save.clicked.connect(self.file_save)
        self.ui.B_TStart.clicked.connect(self.start_tokenization)
        self.ui.actionOpen.triggered.connect(self.choose_file)
        self.ui.actionOpen.setShortcut("ctrl+O")
        self.ui.actionSave_As.triggered.connect(self.file_save)
        self.ui.actionSave_As.setShortcut("Ctrl+S")
        self.ui.actionExit.triggered.connect(self.close_application)

    def choose_file(self):
        """ On click event handler for choose file button """
        fname = QtGui.QFileDialog.getOpenFileName(
            self.ui.centralwidget, "YAST - Open Dialog")
        if not fname:
            return
        self.ui.file_path_textEdit.setText(fname)
        self.ui.token_frame.setEnabled(True)
        self.ui.status_lineEdit.setText("Please start Tokenization.")

    def close_application(self):
        choice = QtGui.QMessageBox.warning(
            self.ui.centralwidget, "YAST - Warning!",
            "Do you really want to Exit?",
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if choice == QtGui.QMessageBox.Yes:
            sys.exit()

    def file_save(self):
        name = QtGui.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'YAST - Save File')
        file = open(name, 'w')

        # TODO: Pull date from output_textedit and write to file

        file.close()

    def start_tokenization(self):
        """
        On click event handler for Tokenization start button
        """
        self.ui.status_lineEdit.setText("")
        msg = "Tokenization in progress. Please wait..."
        QtGui.QMessageBox.information(
            self.ui.centralwidget, "YAST - Processing Started", msg)
        self.ui.status_lineEdit.setText(msg)

        file_name = self.ui.file_path_textEdit.text()
        try:
            self.log_file = LogFile(file_name)
            # Create initial db tables
            Yast.create_tables(self.log_file)
            rows_count = self.log_file.tokenize()
        except (OSError, IOError):
            msg = "File not found or you do not have permission to access the"\
                " file. Please try again"
            QtGui.QMessageBox.critical(
                self.ui.centralwidget, "YAST - Error", msg)
            self.ui.token_frame.setEnabled(False)
            return

        self.ui.token_frame.setEnabled(False)
        self.ui.clean_frame.setEnabled(True)
        self.ui.session_frame.setEnabled(True)

        # TODO: Output data from table to output_textEdit
        # for item in self.log_file.get_all_tokens():
        #    self.ui.output_textEdit.append(str(item))

        msg = "Tokenization completed. Successfully processed {} lines. "\
            "Please start clean or sessionization.".format(rows_count)
        self.ui.status_lineEdit.setText(msg)
        QtGui.QMessageBox.information(
            self.ui.centralwidget, "YAST - Processing Completed", msg)


def main():
    app = QtGui.QApplication(sys.argv)
    gui = YastGui()
    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
