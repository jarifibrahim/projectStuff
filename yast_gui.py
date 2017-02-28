from PyQt4 import QtGui
from ui_mainwindow import Ui_MainWindow
import sys
import settings
from yast import LogFile


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
        self.ui.B_TStart.clicked.connect(self.init_tokenization)
        self.ui.B_CStart.clicked.connect(self.start_cleaning)
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
        self.ui.status_lineEdit.setText("Please start Tokenization.")
        self.ui.token_frame.setEnabled(True)
        self.ui.clean_frame.setEnabled(False)
        self.ui.session_frame.setEnabled(False)

    def close_application(self):
        """ Exit event handler """
        choice = QtGui.QMessageBox.warning(
            self.ui.centralwidget, "YAST - Warning!",
            "Do you really want to Exit?",
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if choice == QtGui.QMessageBox.Yes:
            raise SystemExit

    def file_save(self):
        name = QtGui.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'YAST - Save File')
        file = open(name, 'w')

        # TODO: Pull date from output_textedit and write to file

        file.close()

    def init_tokenization(self):
        """ Initializes tokenization """

        self.ui.B_TStart.setEnabled(False)
        self.ui.progressBar.setValue(0)
        self.ui.records_processed_value_label.setText("0/0")
        # Drop all existing tables
        settings.Base.metadata.drop_all(settings.engine)
        # create new tables
        settings.Base.metadata.create_all(settings.engine)
        msg = "Tokenization in progress. Please wait..."
        self.ui.status_lineEdit.setText(msg)
        msg = "Tokenization started."
        QtGui.QMessageBox.information(
            self.ui.centralwidget, "YAST - Processing Started", msg)

        self.start_tokenization()

    def start_tokenization(self):
        """
        On click event handler for Tokenization start button
        """
        file_name = self.ui.file_path_textEdit.text()
        try:
            self.log_file = LogFile(file_name)
            msg = "0/{}".format(self.log_file.number_of_lines)
            self.ui.records_processed_value_label.setText(msg)
            self.log_file.tokenize(self.ui)
        except (OSError, IOError) as e:
            msg = "File not found or you do not have permission to access the"\
                " file. Please try again"
            QtGui.QMessageBox.critical(
                self.ui.centralwidget, "YAST - Error", msg + ": " + str(e))
            self.ui.token_frame.setEnabled(False)
            return
        except Exception as e:
            QtGui.QMessageBox.critical(
                self.ui.centralwidget, "Yast - Error", str(e))
            self.ui.token_frame.setEnabled(False)
            return
        rows_count = self.log_file.total_db_records
        self.end_tokenization(rows_count)

    def end_tokenization(self, rows_count):
        """ Post tokenization handler """
        self.ui.token_frame.setEnabled(False)
        self.ui.clean_frame.setEnabled(True)
        self.ui.session_frame.setEnabled(True)

        # print output to textEdit
        self.print_output("TOKEN")
        msg = "{}/{}".format(rows_count, rows_count)
        self.ui.records_processed_value_label.setText(msg)

        msg = "Tokenization completed. Successfully processed {} lines. "\
            "Please start clean or sessionization.".format(rows_count)
        self.ui.status_lineEdit.setText(msg)
        QtGui.QMessageBox.information(
            self.ui.centralwidget, "YAST - Processing Completed", msg)
        self.ui.B_TStart.setEnabled(True)

    def print_output(self, _type):
        """
        Helper method to print output to the output_textEdit
        :param _type: Type of operation. Possible values TOKEN and SESSION
        """
        self.ui.output_textEdit.setText("")
        if _type == "TOKEN":
            if self.log_file.file_type == settings.APACHE_COMMON:
                heading = settings.APACHE_COMMON_HEADING
                self.ui.output_textEdit.setText(heading)
                # TODO: Output data from table to output_textEdit
                all_tokens = self.log_file.get_all_tokens()
                for item in all_tokens:
                    # This makes sure the Gui is refreshed after every loop
                    QtGui.QApplication.processEvents()
                    self.ui.output_textEdit.append(str(item))
            if self.log_file.file_type == settings.SQUID:
                pass
        elif _type == "SESSION":
            pass

    def start_cleaning(self):
        ignore_text = self.ui.ignore_ext_lineEdit.text()
        msg = "Log Filtering in progress. Please wait..."
        self.ui.status_lineEdit.setText(msg)
        msg = "Log filtering started."
        QtGui.QMessageBox.information(
            self.ui.centralwidget, "YAST - Processing Started", msg)

        try:
            ignore_list = ignore_text.split(",")
        except Exception:
            QtGui.QMessageBox.critical(self.ui.centralwidget, "YAST - Error",
                                       "Invalid ignore list. Please add all "
                                       "file extensions seperated by comman")

        self.ui.progressBar.setValue(0)
        del_count = self.log_file.filter_file(ignore_list)
        self.ui.progressBar.setMaximum(100)
        self.ui.progressBar.setValue(100)

        self.print_output("TOKEN")

        msg = "{}/{}".format(del_count,
                             self.log_file.total_db_records + del_count)
        self.ui.records_processed_value_label.setText(msg)
        msg = "Records removed"
        self.ui.records_processed_label.setText(msg)

        msg = "Log Filtering completed successfully. Deleted %s entries."\
            "\nYou can now sessionize the log file." % del_count
        self.ui.status_lineEdit.setText(msg)
        QtGui.QMessageBox.information(
            self.ui.centralwidget, "YAST - Processing Started", msg)


def main():
    app = QtGui.QApplication(sys.argv)
    gui = YastGui()
    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
