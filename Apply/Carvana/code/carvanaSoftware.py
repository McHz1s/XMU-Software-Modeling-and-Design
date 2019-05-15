from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from CarvanaSoftwareData import *


class CarvanaSoftware(QDialog):
    def __init__(self,  config, parent=None):
        super(CarvanaSoftware, self).__init__(parent)
        self.config = config
        self._title = "CarBackgroundRemove"
        self._diawidth = 1600
        self._diaheight = 800
        self.setWindowTitle(self._title)
        self.setMinimumHeight(self._diaheight)
        self.setMinimumWidth(self._diawidth)
        self.source_img_view = QLabel("add a image file")
        self.target_img_view = QLabel("waiting a source file")
        self.btn_open = QPushButton("open")
        self.btn_open.clicked.connect(self.open_clicked)
        self.btn_save = QPushButton("save")
        self.btn_save.clicked.connect(self.save_clicked)
        self.hlayout = QHBoxLayout()
        self.hlayout.addWidget(self.source_img_view, 0, Qt.AlignLeft | Qt.AlignCenter)
        self.hlayout.addWidget(self.btn_open, 0, Qt.AlignBottom | Qt.AlignCenter)
        self.hlayout.addWidget(self.btn_save, 0, Qt.AlignBottom | Qt.AlignCenter)
        self.hlayout.addWidget(self.target_img_view, 0, Qt.AlignRight | Qt.AlignCenter)
        self.setLayout(self.hlayout)
        self.hlayout.setStretchFactor(self.btn_open, 1)
        self.hlayout.setStretchFactor(self.source_img_view, 6)
        self.hlayout.setStretchFactor(self.target_img_view, 6)
        self.result = []
        self.img_name = None

    def predict(self, filepath, origin_width, origin_height):
        config = CarvanaConfig()
        data = SoftData(config=config, mode='prediction')
        model = FCNModel(config=self.config, mode="prediction", data=data, network=network)
        result = model.software_predict(filepath)
        result = data.deal_result(result, origin_width, origin_height)
        return result

    def open_clicked(self, checked):
        self.filename = QFileDialog.getOpenFileName(self, "OpenFile", ".", 
            "Image Files(*.jpg *.jpeg *.png)")[0]
        if len(self.filename):
            src = QImage(self.filename)
            self.img_name = (self.filename.split('/')[-1]).split('.')[0]
            print(self.img_name)
            self.source_img_view.setPixmap(QPixmap.fromImage(src))
            self.resize(src.width(), src.height())
            self.result = self.predict(self.filename, src.width(), src.height())
            imwrite('temp.jpg', self.result)
            tar = QImage('temp.jpg')
            self.target_img_view.setPixmap(QPixmap.fromImage(tar))

    def save_clicked(self):
        if self.img_name is None:
            return None
        imwrite(self.img_name+'_RB.jpg', self.result)
