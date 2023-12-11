from socket import AddressFamily
from subprocess import Popen, PIPE
from csv import writer

from PyQt5.QtCore import QObject, QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import QMainWindow, QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox
from psutil import net_if_addrs

from window_main import Ui_MainWindow

class ARPScanWorker(QObject):
    finished = pyqtSignal()
    result = pyqtSignal(tuple)

    def __init__(self, parent=None, nic=None) -> None:
        super().__init__(parent)
        self.nic = nic

    def run(self):
        process = Popen(["arp-scan", "--localnet", "-x", "-I", self.nic], stdout=PIPE, text=True)
        count = 0
        while True:
            line = process.stdout.readline().strip()
            if not line:
                break
            count += 1
            self.result.emit(tuple(line.split("\t")))
        print("get here", count)
        self.finished.emit()

class ReadOnlyTableWidgetItem(QTableWidgetItem):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setFlags(self.flags() & ~Qt.ItemFlag.ItemIsEditable)

class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.nicBox: QComboBox
        self.scanButton: QPushButton
        self.saveButton: QPushButton
        self.tableWidget: QTableWidget
        self.tableWidget.setColumnWidth(2, 300)
        self.tableWidget.setColumnWidth(3, 200)
        self.nics = {}
        self.init_nics()
        self.saveButton.clicked.connect(self.save_csv)
        self.scanButton.clicked.connect(self.scan_ip)
        
        self.context_keeper = {}
    

    def init_nics(self):
        self.nics.clear()
        for name, ips in net_if_addrs().items():
            for ip in ips:
                if ip.family == AddressFamily.AF_INET:
                    if ip.address == "127.0.0.1":
                        continue
                    self.nics[name] = ip
                    self.nicBox.addItem(f"{name}({ip.address})", name)
                    self.scanButton.setEnabled(True)
    
    def scan_ip(self, checked=None):
        self.scanButton.setDisabled(True)
        self.saveButton.setDisabled(True)
        
        self.tableWidget.setRowCount(0)
        nic_name = self.nicBox.currentData()

        worker = ARPScanWorker(nic=nic_name)
        thread = QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.result.connect(self.on_worker_result)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(self.on_worker_finished)
        thread.finished.connect(thread.deleteLater)
        thread.start()

        self.context_keeper["thread"] = thread
        self.context_keeper["worker"] = worker
    
    def save_csv(self, checked):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save results as CSV file",
            "",
            "CSV File (*.csv)"
        )
        def item_to_text(item):
            return item.text() if item else ""
        with open(filename, "w", newline="") as csv_file:
            csv = writer(csv_file)
            csv.writerow(["IP", "MAC", "MAC Source", "comments"])
            for row in range(self.tableWidget.rowCount()):
                row_data = [item_to_text(self.tableWidget.item(row, col))
                            for col in range(self.tableWidget.columnCount())]
                csv.writerow(row_data)
        box = QMessageBox(self)
        box.setWindowTitle("Data Saved")
        box.setText("Successfully saved data into " + filename)
        box.exec()
        
    
    def on_worker_result(self, result):
        row = self.tableWidget.rowCount()
        self.tableWidget.setRowCount(row + 1)
        self.tableWidget.setItem(row, 0, ReadOnlyTableWidgetItem(result[0]))
        self.tableWidget.setItem(row, 1, ReadOnlyTableWidgetItem(result[1]))
        self.tableWidget.setItem(row, 2, ReadOnlyTableWidgetItem(result[2]))
        self.tableWidget.update()
    
    def on_worker_finished(self):
        self.scanButton.setEnabled(True)
        self.saveButton.setEnabled(True)
    
    def add_history(self):
        pass

