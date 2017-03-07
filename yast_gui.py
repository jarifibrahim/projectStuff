from PyQt4 import QtGui
from ui_mainwindow import Ui_MainWindow
import sys
import settings
from yast import TokenizationThread, FilteringThread, SessionThread


class YastGui(QtGui.QMainWindow):
    def __init__(self):
        super(YastGui, self).__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.total_records = 0

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
        self.ui.B_TStart.clicked.connect(self.tokenization_handler)
        self.ui.B_CStart.clicked.connect(self.filter_handler)
        self.ui.B_SStart.clicked.connect(self.sessionization_handler)
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
            self.ui.centralwidget, 'YAST - Save File',
            filter="Comma seperated Variable File (*.csv)")
        file = open(name, 'w')
        result = self.ui.output_textEdit.toPlainText()
        # Replace all tab characters by comma
        result = result.replace("\t", ",")
        # Remove all white spaces
        result = result.replace(" ", "")
        file.write(result)
        file.close()

    def tokenization_handler(self):
        """
        Tokenization handler is invoked by the start tokenization button
        """
        self.init_database()

        self.file_path = self.ui.file_path_textEdit.text()
        try:
            self.thread = TokenizationThread(self.file_path)
        except (OSError, IOError) as e:
            msg = "Unable to open file"
            QtGui.QMessageBox.critical(
                self.ui.centralwidget, "YAST - Error", msg + ": " + str(e))
            self.ui.token_frame.setEnabled(False)
            return

        self.thread.update_progress_signal.connect(self.update_progress)
        self.thread.line_count_signal.connect(self.set_total_count)
        self.thread.finished.connect(self.tokenization_completed)
        self.thread.started.connect(self.tokenization_started)
        self.thread.start()

    def tokenization_started(self):
        """ Signal handler for STARTED signal of TokenizationThread """
        self.ui.token_frame.setEnabled(False)
        self.ui.B_Save.setEnabled(False)
        self.ui.B_Close.setEnabled(False)

        self.ui.progressBar.setValue(0)
        self.ui.records_processed_value_label.setText("0/0")
        self.ui.records_processed_label.setText("Records processed")

        msg = "Please wait. Tokenization in progress."
        self.ui.status_lineEdit.setText(msg)


        #heading = settings.APACHE_COMMON_HEADING
        #self.ui.output_textEdit.setText(heading)

    
        #heading = settings.SQUID_HEADING
        #self.ui.output_textEdit.setText(heading)

    def tokenization_completed(self):
        """ Signal handler for FINISHED signal of TokenizationThread """
        self.ui.clean_frame.setEnabled(True)
        self.ui.session_frame.setEnabled(True)

        self.ui.B_Save.setEnabled(True)
        self.ui.B_Close.setEnabled(True)
        count = self.ui.records_processed_value_label.text().split('/')[0]
        msg = "Tokenization completed. Successfully processed {} lines. "\
            "Please start clean or sessionization.".format(count)
        self.ui.status_lineEdit.setText(msg)
        QtGui.QMessageBox.information(
            self.ui.centralwidget, "YAST - Processing Completed", msg)

    def set_total_count(self, count):
        """ Set total number of lines in the GUI """
        msg = "0/{}".format(count)
        self.ui.records_processed_value_label.setText(msg)
        self.ui.progressBar.setMaximum(count)
        self.old_total_records = self.total_records
        self.total_records = count

    def update_progress(self, status_list):
        """ Update progress bar and current status in the GUI """
        # Calculate completion percentage
        current_count = status_list[0]
        self.ui.progressBar.setValue(current_count + 1)
        msg = self.ui.records_processed_value_label.text().split('/')
        msg[0] = str(current_count + 1)
        self.ui.records_processed_value_label.setText("/".join(msg))
        if status_list[1] is not None:
            self.ui.output_textEdit.append(status_list[1])

    def init_database(self):
        """ Create all tables """
        # Drop all existing tables
        settings.Base.metadata.drop_all(settings.engine)
        # create new tables
        settings.Base.metadata.create_all(settings.engine)
        settings.session.commit()

    def filter_handler(self):
        """ Filter handler is invoked by start cleaning button """
        ignore_list = self.ui.ignore_ext_lineEdit.text().split(",")

        self.filter_thread = FilteringThread(self.file_path, ignore_list)
        self.filter_thread.started.connect(self.filter_started)
        self.filter_thread.line_count_signal.connect(self.set_total_count)
        self.filter_thread.result_item_signal.connect(
            self.update_progress)
        self.filter_thread.finished.connect(self.filter_completed)
        self.filter_thread.start()

    def filter_started(self):
        """ Signal handler for STARTED signal of FilteringThread """

        self.ui.token_frame.setEnabled(False)
        self.ui.clean_frame.setEnabled(False)
        self.ui.session_frame.setEnabled(False)

        self.ui.B_Save.setEnabled(False)
        self.ui.B_Close.setEnabled(False)
        msg = "Log Filtering in progress. Please wait..."
        self.ui.status_lineEdit.setText(msg)
        heading = settings.APACHE_COMMON_HEADING
        self.ui.output_textEdit.setText(heading)
        self.ui.progressBar.setValue(0)

    def filter_completed(self):
        """ Signal handler for FINISHED signal of FilteringThread """

        self.ui.token_frame.setEnabled(True)
        self.ui.clean_frame.setEnabled(True)
        self.ui.session_frame.setEnabled(True)

        self.ui.B_Save.setEnabled(True)
        self.ui.B_Close.setEnabled(True)
        msg = "Log Filtering completed successfully. Deleted %s entries."\
            "\nYou can now sessionize the log file." % (
                self.old_total_records - self.total_records)
        self.ui.status_lineEdit.setText(msg)
        QtGui.QMessageBox.information(
            self.ui.centralwidget, "YAST - Processing Started", msg)

    def sessionization_handler(self):
        """ Invoked by start sessionization button """

        session_timer = self.ui.time_spinBox.value()
        self.session_thread = SessionThread(self.file_path, session_timer)
        self.session_thread.started.connect(self.sessionization_started)
        self.session_thread.update_progress_signal.connect(
            self.update_progress)
        self.session_thread.total_count_signal.connect(self.set_total_count)
        self.session_thread.step_completed_signal.connect(self.step_completed)
        self.session_thread.finished.connect(self.sessionization_completed)
        self.session_thread.start()

    def sessionization_started(self):
        """ Signal handler for STARTED signal of SessionizationThread """

        self.ui.token_frame.setEnabled(False)
        self.ui.clean_frame.setEnabled(False)
        self.ui.session_frame.setEnabled(False)

        self.ui.B_Save.setEnabled(False)
        self.ui.B_Close.setEnabled(False)
        msg = "Sessionization in progress. Please wait..."
        self.ui.status_lineEdit.setText(msg)
        self.ui.output_textEdit.setText(settings.URL_OUTPUT_HEADING)

    def sessionization_completed(self):
        """ Signal handler for FINISHED signal of SessionizationThread """

        self.ui.token_frame.setEnabled(True)
        self.ui.clean_frame.setEnabled(True)
        self.ui.session_frame.setEnabled(True)

        self.ui.B_Save.setEnabled(True)
        self.ui.B_Close.setEnabled(True)
        msg = "Sessionization successfully completed."
        self.ui.status_lineEdit.setText(msg)

        msg = "Sucessfully generated {} sessions".format(self.total_records)
        QtGui.QMessageBox.information(
            self.ui.centralwidget, "YAST - Processing Completed", msg)

    def step_completed(self, step):

        msg = "Step {}/3 of sessionization in progress. Please wait".format(
            step)
        self.ui.status_lineEdit.setText(msg)


def main():
    app = QtGui.QApplication(sys.argv)
    gui = YastGui()
    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
