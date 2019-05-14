import sys
from PyQt5.QtWidgets import QApplication
from carvanaSoftware import *

if __name__ == "__main__":
    config = CarvanaConfig()
    app = QApplication(sys.argv)
    dia = CarvanaSoftware(config)
    dia.show()
    app.exec_()

