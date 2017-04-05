from PyQt4 import QtGui, QtCore
from ui_mainwindow import Ui_MainWindow
import sys
import atexit
import logging
import settings
from yast import TokenizationThread, FilteringThread, SessionThread


class YastGui(QtGui.QMainWindow):
    def __init__(self):
        super(YastGui, self).__init__()
        logging.info("Initializing GUI")
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.total_records = 0

        # Disable frames
        self.ui.token_frame.setEnabled(False)
        self.ui.filter_frame.setEnabled(False)
        self.ui.session_frame.setEnabled(False)

        # Set on click event for all buttons
        self.ui.B_choose_file.clicked.connect(self.choose_file)
        self.ui.file_path_textEdit.textChanged.connect(
            lambda x: self.ui.token_frame.setEnabled(True))
        self.ui.log_format_comboBox.currentIndexChanged.connect(
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

        logging.info("GUI initialization completed")

    def choose_file(self):
        """ On click event handler for choose file button """
        logging.info("File select dialog opened")
        fname = QtGui.QFileDialog.getOpenFileName(
            self.ui.centralwidget, "YAST - Open Dialog")
        if not fname:
            logging.info("No file selected")
            return
        logging.info("%s file selected" % fname)
        self.ui.file_path_textEdit.setText(fname)
        self.ui.status_lineEdit.setText("Please start Tokenization.")
        self.ui.token_frame.setEnabled(True)
        self.ui.filter_frame.setEnabled(False)
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
        logging.info("Saving output to file %s" % name)
        file = open(name, 'w')
        result = self.ui.output_plainTextEdit.toPlainText()
        # Replace all tab characters by comma
        result = result.replace("\t", ",")
        # Remove all white spaces
        result = result.replace(" ", "")
        file.write(result)
        logging.info("Writing data to file completed")
        file.close()

    def tokenization_handler(self):
        """
        Tokenization handler is invoked by the start tokenization button
        """
        msg = "Please wait. Tokenization in progress."
        self.ui.status_lineEdit.setText(msg)

        self.timer = QtCore.QElapsedTimer()
        self.timer.start()
        f_type = int(self.ui.log_format_comboBox.currentIndex())
        self.init_database()

        self.file_path = self.ui.file_path_textEdit.text()
        try:
            self.thread = TokenizationThread(self.file_path, f_type)
            logging.info("Tokenization Thread created")
        except (OSError, IOError) as e:
            msg = "Unable to open file"
            QtGui.QMessageBox.critical(
                self.ui.centralwidget, "YAST - Error", msg + ": " + str(e))
            self.ui.token_frame.setEnabled(False)
            logging.exception("Failed to open file %s" % self.file_path)
            return
        except TypeError:
            msg = "Selected log file doesn't match with the selected log "\
                "format ({}). Please verify file format."
            msg = msg.format(self.ui.log_format_comboBox.currentText())
            self.ui.status_lineEdit.setText(msg)
            QtGui.QMessageBox.critical(
                self.ui.centralwidget, "YAST - Error", msg)
            self.ui.token_frame.setEnabled(False)
            logging.exception("Incorrect file format selected")
            return
        except ValueError as e:
            self.ui.status_lineEdit.setText(str(e))
            QtGui.QMessageBox.critical(
                self.ui.centralwidget, "YAST - Error", str(e))
            self.ui.token_frame.setEnabled(False)
            logging.exception("Unsupported file format")
            return

        self.thread.update_progress_signal.connect(self.update_progress)
        self.thread.total_count_signal.connect(self.set_total_count)
        self.thread.finished.connect(self.tokenization_completed)
        self.thread.started.connect(self.tokenization_started)
        self.thread.start()

    def tokenization_started(self):
        """ Signal handler for STARTED signal of TokenizationThread """
        logging.info("Tokenization thread started")
        self.ui.token_frame.setEnabled(False)
        self.ui.B_Save.setEnabled(False)
        self.ui.B_Close.setEnabled(False)

        self.ui.progressBar.setValue(0)
        self.ui.records_processed_value_label.setText("0/0")
        self.ui.records_processed_label.setText("Records processed")
        self.ui.output_plainTextEdit.setPlainText("")

    def tokenization_completed(self):
        """ Signal handler for FINISHED signal of TokenizationThread """
        logging.info("Tokenization thread completed")
        self.ui.filter_frame.setEnabled(True)
        self.ui.session_frame.setEnabled(True)

        self.ui.B_Save.setEnabled(True)
        self.ui.B_Close.setEnabled(True)
        count = self.ui.records_processed_value_label.text().split('/')[0]
        msg = "Tokenization completed. Successfully processed {0} lines. "\
            "Total Time Taken: {1: .2f} secs. Please start clean or "\
            "sessionization.".format(count, self.timer.elapsed() / 1000)
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

    def update_progress(self, progress_val, output_str):
        """
        Update progress bar and current status in the GUI
        :param progress_val: Progress bar will be set to this value
        :param output_str: str that will be appended to output textEdit
        """
        current_count = progress_val
        self.ui.progressBar.setValue(current_count + 1)
        msg = self.ui.records_processed_value_label.text().split('/')
        msg[0] = str(current_count + 1)
        self.ui.records_processed_value_label.setText("/".join(msg))
        if output_str:
            self.ui.output_plainTextEdit.insertPlainText(output_str)

    def init_database(self):
        """ Create all tables """
        # Drop all existing tables
        settings.Base.metadata.drop_all(settings.engine)
        # create new tables
        settings.Base.metadata.create_all(settings.engine)
        settings.session.commit()
        logging.info("All tables created")

    def filter_handler(self):
        """ Filter handler is invoked by start cleaning button """
        self.timer = QtCore.QElapsedTimer()
        self.timer.start()

        ignore_str = self.ui.ignore_ext_lineEdit.text().split(",")
        ignore_list = [x.replace(".", "").strip() for x in ignore_str]
        self.filter_thread = FilteringThread(self.file_path, ignore_list)
        logging.info("Filter thread created")
        self.filter_thread.started.connect(self.filter_started)
        self.filter_thread.total_count_signal.connect(self.set_total_count)
        self.filter_thread.update_progress_signal.connect(self.update_progress)
        self.filter_thread.finished.connect(self.filter_completed)
        self.filter_thread.start()

    def filter_started(self):
        """ Signal handler for STARTED signal of FilteringThread """
        logging.info("Filter thread started")
        self.ui.token_frame.setEnabled(False)
        self.ui.filter_frame.setEnabled(False)
        self.ui.session_frame.setEnabled(False)

        self.ui.B_Save.setEnabled(False)
        self.ui.B_Close.setEnabled(False)
        msg = "Log Filtering in progress. Please wait..."
        self.ui.status_lineEdit.setText(msg)
        self.ui.output_plainTextEdit.setPlainText("")
        self.ui.progressBar.setValue(0)

    def filter_completed(self):
        """ Signal handler for FINISHED signal of FilteringThread """
        logging.info("Filter thread completed")
        self.ui.token_frame.setEnabled(True)
        self.ui.filter_frame.setEnabled(True)
        self.ui.session_frame.setEnabled(True)

        self.ui.B_Save.setEnabled(True)
        self.ui.B_Close.setEnabled(True)
        msg = "Log Filtering completed successfully. Deleted %s entries. "\
            "Total time taken: %.2f secs. \nYou can now sessionize the log "\
            "file." % (self.old_total_records - self.total_records,
                       self.timer.elapsed() / 1000)
        self.ui.status_lineEdit.setText(msg)
        QtGui.QMessageBox.information(
            self.ui.centralwidget, "YAST - Processing Started", msg)

    def sessionization_handler(self):
        """ Invoked by start sessionization button """

        session_timer = self.ui.time_spinBox.value()
        self.timer = QtCore.QElapsedTimer()
        self.timer.start()

        self.session_thread = SessionThread(self.file_path, session_timer)
        logging.info("Sessionization thread created")
        self.session_thread.started.connect(self.sessionization_started)
        self.session_thread.update_progress_signal.connect(
            self.update_progress)
        self.session_thread.total_count_signal.connect(self.set_total_count)
        self.session_thread.number_of_sessions_signal.connect(
            self.total_sessions_count)
        self.session_thread.step_completed_signal.connect(self.step_completed)
        self.session_thread.finished.connect(self.sessionization_completed)
        self.session_thread.start()

    def sessionization_started(self):
        """ Signal handler for STARTED signal of SessionizationThread """
        logging.info("Sessionization thread started")
        self.ui.token_frame.setEnabled(False)
        self.ui.filter_frame.setEnabled(False)
        self.ui.session_frame.setEnabled(False)

        self.ui.B_Save.setEnabled(False)
        self.ui.B_Close.setEnabled(False)
        msg = "Sessionization in progress. Please wait..."
        self.ui.status_lineEdit.setText(msg)
        self.ui.output_plainTextEdit.setPlainText("")

    def sessionization_completed(self):
        """ Signal handler for FINISHED signal of SessionizationThread """
        logging.info("Sessionization completed")
        self.ui.token_frame.setEnabled(True)
        self.ui.filter_frame.setEnabled(True)
        self.ui.session_frame.setEnabled(True)

        self.ui.B_Save.setEnabled(True)
        self.ui.B_Close.setEnabled(True)
        msg = "Sucessfully generated {0} sessions. Total time taken: "\
            "{1:.2f} secs.".format(
                self.total_sessions, self.timer.elapsed() / 1000)
        self.ui.status_lineEdit.setText(msg)
        QtGui.QMessageBox.information(
            self.ui.centralwidget, "YAST - Processing Completed", msg)

    def step_completed(self, step):

        msg = "Step {}/3 of sessionization in progress. Please wait".format(
            step)
        self.ui.status_lineEdit.setText(msg)

    def total_sessions_count(self, count):
        self.total_sessions = count


def main():
    atexit.register(db_delete)
    logging.basicConfig(
        filename='yast.log', level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.info('Started YAST')
    app = QtGui.QApplication(sys.argv)
    gui = YastGui()
    gui.show()
    sys.exit(app.exec_())


def db_delete():
    import os
    os.remove(settings.DATABASE_NAME)

if __name__ == '__main__':
    main()
