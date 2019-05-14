from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from CarvanaSoftwareData import *

class CarvanaSoftware(QDialog):
    def __init__(self,  config, parent=None):
        super(CarvanaSoftware, self).__init__(parent)
        self.config = config
        self._title = "CarBackgroundRemove"
        self._diawidth = 600
        self._diaheight = 600
        self.setWindowTitle(self._title)
        self.setMinimumHeight(self._diaheight)
        self.setMinimumWidth(self._diawidth)
        self.source_img_view = QLabel("add a image file")
        self.source_img_view.setAlignment(Qt.AlignCenter)
        self.target_img_view = QLabel("waiting a source file")
        self.target_img_view.setAlignment(Qt.AlignCenter)
        self.btn_open = QPushButton("open")
        self.btn_open.clicked.connect(self.on_btn_open_clicked)
        self.vlayout = QVBoxLayout()
        self.vlayout.addWidget(self.source_img_view)
        self.vlayout.addWidget(self.target_img_view)
        self.vlayout.addWidget(self.btn_open)
        self.setLayout(self.vlayout)
        
    # @pyqtSlot(bool)
    def predict(self, filepath, origin_width, origin_height):
        config = CarvanaConfig()
        data = SoftData(config=config, mode='prediction')
        model = FCNModel(config=self.config, mode="prediction", data=data, network=network)
        result = model.software_predict(filepath)
        result = data.deal_result(result, origin_width, origin_height)
        return result

    def on_btn_open_clicked(self, checked):
        self.filename = QFileDialog.getOpenFileName(self, "OpenFile", ".", 
            "Image Files(*.jpg *.jpeg *.png)")[0]
        if len(self.filename):
            self.image = QImage(self.filename)
            self.source_img_view.setPixmap(QPixmap.fromImage(self.image))
            self.resize(self.image.width(), self.image.height())
            result = self.predict(self.filename, self.image.width(), self.image.height())
            # import matplotlib.pyplot as plt
            # plt.imshow(result)
            # plt.show()
            imwrite('temp.jpg', result)
            self.image = QImage('temp.jpg')
            self.target_img_view.setPixmap(QPixmap.fromImage(self.image))
            self.resize(self.image.width(), 2*self.image.height())
