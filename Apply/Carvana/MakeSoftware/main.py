############################################
# Mobilenetv2_u_net
############################################
"""
MobileNetV2-UNet
Reference: https://github.com/JonathanCMitchell/mobilenet_v2_keras
"""
from keras.layers import Activation
from keras.layers import BatchNormalization
from keras.layers import Conv2D
from keras.applications.mobilenet import DepthwiseConv2D,relu6
from keras.layers import UpSampling2D
from keras.layers import Add
from keras.layers import Concatenate
from keras.layers import Input
from keras.backend import int_shape, image_data_format
from keras.models import Model as Modelib




def _make_divisible(v, divisor, min_value=None):
    if min_value is None:
        min_value = divisor
    new_v = max(min_value, int(v + divisor / 2) // divisor * divisor)
    # Make sure that round down does not go down by more than 10%.
    if new_v < 0.9 * v:
        new_v += divisor
    return new_v


def _inverted_res_block(inputs, expansion, stride, alpha, filters,
                        block_id, prefix, dilation=1,use_shortcuts=False):
    in_channels = inputs._keras_shape[-1]
    pointwise_conv_filters = int(filters * alpha)
    pointwise_filters = _make_divisible(pointwise_conv_filters, 8)
    x = inputs
    prefix = '{}_mn_block_{}_'.format(prefix, block_id)

    if block_id:
        # Expand
        x = Conv2D(expansion * in_channels, kernel_size=1, padding='same',
                   use_bias=False, activation=None,
                   name=prefix + 'expand')(x)
        x = BatchNormalization(epsilon=1e-3, momentum=0.999,
                               name=prefix + 'expand_BN')(x)
        x = Activation(relu6, name=prefix + 'expand_relu')(x)
    else:
        prefix = '{}_mn_expanded_conv_'.format(prefix)

    # Depthwise
    x = DepthwiseConv2D(kernel_size=3, strides=stride,
                        dilation_rate=dilation, activation=None,
                        use_bias=False, padding='same',
                        name=prefix + 'depthwise')(x)
    x = BatchNormalization(epsilon=1e-3, momentum=0.999,
                           name=prefix + 'depthwise_BN')(x)

    x = Activation(relu6, name=prefix + 'depthwise_relu')(x)

    # Project
    x = Conv2D(pointwise_filters,
               kernel_size=1, padding='same', use_bias=False, activation=None,
               name=prefix + 'project')(x)
    x = BatchNormalization(epsilon=1e-3, momentum=0.999,
                           name=prefix + 'project_BN')(x)

    if in_channels == pointwise_filters and stride == 1 and dilation == 1:
        return Add(name=prefix + 'add')([inputs, x])

    return x



def shortcut(input, residual, block_id):
    input_shape = int_shape(input)
    residual_shape = int_shape(residual)
    stride_row = int(round(input_shape[1] / residual_shape[1]))
    stride_col = int(round(input_shape[2] / residual_shape[2]))
    channels_equal = (input_shape[3] == residual_shape[3])

    shortcut_connection = input
    if stride_col > 1 or stride_row > 1 or not channels_equal:
        shortcut_connection = Conv2D(filters=residual_shape[3],
                                     kernel_size=1, strides=(stride_row, stride_col),
                                     padding='valid', kernel_initializer='he_normal',
                                     name='shortcut_conv_' + str(block_id))(input)

    return Add(name='shortcut' + str(block_id))([shortcut_connection, residual])


def mobilenet_v2_unet(input_size=(512, 512, 3), class_num=1, output_stride=16, alpha=1.0):
    if alpha not in [0.35, 0.50, 0.75, 1.0, 1.3, 1.4]:
        raise ValueError('If imagenet weights are being loaded, '
                         'alpha can be one of'
                         '`0.25`, `0.50`, `0.75` or `1.0` only.')
    input_image = Input(input_size)
    first_block_filters = _make_divisible(32 * alpha, 8)
    x = Conv2D(first_block_filters,
               kernel_size=3,
               strides=(2, 2), padding='same',
               use_bias=False, name='enc_mn_Conv1')(input_image)
    x = BatchNormalization(epsilon=1e-3, momentum=0.999, name='enc_mn_bn_Conv1')(x)
    x = Activation(relu6, name='enc_mn_Conv1_relu')(x)

    current_stride = 2
    stride_left = output_stride / current_stride

    enc_conv0 = _inverted_res_block(x, filters=16, alpha=alpha, stride=1,
                                    expansion=1, block_id=0, prefix='enc')

    if stride_left > 1:
        strides = (2, 2)
        dilation = 1
        stride_left /= 2
    else:
        strides = (1, 1)
        dilation = 2

    enc_conv1 = _inverted_res_block(enc_conv0, filters=24, alpha=alpha, stride=strides, dilation=dilation,
                                    expansion=6, block_id=1, use_shortcuts=True, prefix='enc')
    enc_conv2 = _inverted_res_block(enc_conv1, filters=24, alpha=alpha, stride=1,
                                    expansion=6, block_id=2, prefix='enc')

    if stride_left > 1:
        strides = (2, 2)
        dilation = 1
        stride_left /= 2
    else:
        strides = (1, 1)
        dilation = 2

    enc_conv3 = _inverted_res_block(enc_conv2, filters=32, alpha=alpha, stride=strides, dilation=dilation,
                                    expansion=6, block_id=3, use_shortcuts=True, prefix='enc')
    enc_conv4 = _inverted_res_block(enc_conv3, filters=32, alpha=alpha, stride=1, expansion=6, block_id=4,
                                    use_shortcuts=True, prefix='enc')
    enc_conv5 = _inverted_res_block(enc_conv4, filters=32, alpha=alpha, stride=1, expansion=6, block_id=5,
                                    use_shortcuts=True, prefix='enc')

    if stride_left > 1:
        strides = (2, 2)
        dilation = 1
        stride_left /= 2
    else:
        strides = (1, 1)
        dilation = 2

    enc_conv6 = _inverted_res_block(enc_conv5, filters=64, alpha=alpha, stride=strides,
                                    dilation=dilation, expansion=6, block_id=6,
                                    use_shortcuts=True, prefix='enc')
    enc_conv7 = _inverted_res_block(enc_conv6, filters=64, alpha=alpha, stride=1,
                                    expansion=6, block_id=7, use_shortcuts=True, prefix='enc')
    enc_conv8 = _inverted_res_block(enc_conv7, filters=64, alpha=alpha, stride=1,
                                    expansion=6, block_id=8, use_shortcuts=True, prefix='enc')
    enc_conv9 = _inverted_res_block(enc_conv8, filters=64, alpha=alpha, stride=1,
                                    expansion=6, block_id=9, use_shortcuts=True, prefix='enc')

    enc_conv10 = _inverted_res_block(enc_conv9, filters=96, alpha=alpha, stride=1,
                                     expansion=6, block_id=10, use_shortcuts=True, prefix='enc')
    enc_conv11 = _inverted_res_block(enc_conv10, filters=96, alpha=alpha, stride=1,
                                     expansion=6, block_id=11, use_shortcuts=True, prefix='enc')
    enc_conv12 = _inverted_res_block(enc_conv11, filters=96, alpha=alpha, stride=1,
                                     expansion=6, block_id=12, use_shortcuts=True, prefix='enc')

    if stride_left > 1:
        strides = (2, 2)
        dilation = 1
        stride_left /= 2
    else:
        strides = (1, 1)
        dilation = 2

    enc_conv13 = _inverted_res_block(enc_conv12, filters=160, alpha=alpha, stride=strides, dilation=dilation,
                                     expansion=6, block_id=13, use_shortcuts=True, prefix='enc')
    enc_conv14 = _inverted_res_block(enc_conv13, filters=160, alpha=alpha, stride=1,
                                     expansion=6, block_id=14, use_shortcuts=True, prefix='enc')
    enc_conv15 = _inverted_res_block(enc_conv14, filters=160, alpha=alpha, stride=1,
                                     expansion=6, block_id=15, use_shortcuts=True, prefix='enc')

    enc_conv16 = _inverted_res_block(enc_conv15, filters=320, alpha=alpha, stride=1,
                                     expansion=6, block_id=16, use_shortcuts=True, prefix='enc')

    # no alpha applied to last conv as stated in the paper:
    # if the width multiplier is greater than 1 we
    # increase the number of output channels
    if alpha > 1.0:
        last_block_filters = _make_divisible(1280 * alpha, 8)
    else:
        last_block_filters = 1280

    enc_out = Conv2D(last_block_filters,
                     kernel_size=1,
                     use_bias=False,
                     name='enc_mn_Conv_1')(enc_conv16)
    enc_out = BatchNormalization(epsilon=1e-3, momentum=0.999, name='enc_mn_Conv_1_bn')(enc_out)
    enc_out = Activation(relu6, name='enc_mn_out_relu')(enc_out)

    def upconv(input_tensor, filters, stride, block_id, concat_tensor=None, dilation=1):
        tensor = input_tensor
        if concat_tensor is not None:
            # print(input_tensor.shape, concat_tensor.shape, block_id)
            tensor = UpSampling2D(size=(2, 2),
                                  data_format=image_data_format(), name='upsampling_{}'.format(block_id))(tensor)

            # Ugly solution for input shape=(401,401,3)
            # if block_id > 25:
            #     tensor = Lambda(lambda x: x[:, :-1, :-1, :])(tensor)

            tensor = Concatenate(name='concat_{}'.format(block_id))([tensor, concat_tensor])
        dec_conv = _inverted_res_block(tensor, filters=filters, alpha=alpha, stride=stride, dilation=dilation,
                                       expansion=6, block_id=block_id, use_shortcuts=True, prefix='dec')
        return dec_conv

    bottleneck = _inverted_res_block(enc_out,
                                     filters=160,
                                     alpha=alpha,
                                     stride=2, dilation=1,
                                     expansion=6,
                                     block_id=None, use_shortcuts=True, prefix='bottleneck')

    upconv1 = upconv(input_tensor=bottleneck,
                     filters=160, stride=1,
                     block_id=None)
    upconv2 = upconv(input_tensor=upconv1,
                     filters=160, stride=1,
                     block_id=19)
    upconv3 = upconv(input_tensor=upconv2,
                     filters=160, stride=1,
                     block_id=20)

    upconv4 = upconv(input_tensor=upconv3,
                     filters=96, stride=1,
                     block_id=21)
    upconv5 = upconv(input_tensor=upconv4,
                     filters=96, stride=1,
                     block_id=22)
    upconv6 = upconv(input_tensor=upconv5,
                     filters=96, stride=1,
                     block_id=23)
    upconv7 = upconv(input_tensor=upconv6,
                     filters=64, stride=1,
                     block_id=24)
    upconv8 = upconv(input_tensor=upconv7,
                     concat_tensor=enc_conv8,
                     filters=64, stride=1,
                     block_id=25)
    upconv9 = upconv(input_tensor=upconv8,
                     filters=64, stride=1,
                     block_id=26)
    upconv10 = upconv(input_tensor=upconv9,
                      filters=64, stride=1,
                      block_id=27)
    upconv11 = upconv(input_tensor=upconv10,
                      concat_tensor=enc_conv5,
                      filters=32, stride=1,
                      block_id=28)
    upconv12 = upconv(input_tensor=upconv11,
                      filters=32, stride=1,
                      block_id=29)
    upconv13 = upconv(input_tensor=upconv12,
                      filters=32, stride=1,
                      block_id=30)

    upconv14 = upconv(input_tensor=upconv13,
                      concat_tensor=enc_conv2,
                      filters=24, stride=1,
                      block_id=31)
    upconv15 = upconv(input_tensor=upconv14,
                      filters=24, stride=1,
                      block_id=32)

    upconv16 = upconv(input_tensor=upconv15,
                      concat_tensor=enc_conv0,
                      filters=16, stride=1,
                      block_id=33)
    upconv17 = upconv(input_tensor=upconv16,
                      concat_tensor=input_image,
                      filters=8, stride=1,
                      block_id=34)
    segmap = Conv2D(kernel_size=1,
                    strides=1,
                    filters=1,
                    padding='same',
                    activation='sigmoid',
                    name='segmentation_map')(upconv17)

    model = Modelib(inputs=[input_image], outputs=[segmap], name='mobilenetv2_unet')

    return model

########################################
# Data
########################################
class Config(object):
    image_width = 512
    image_height = 512


from numpy import  expand_dims, stack, multiply
from cv2 import resize, imread, imwrite, INTER_AREA, IMREAD_GRAYSCALE

class SoftData(object):
    def __init__(self, config):
        self.config = config
        self.pic = []
        self.ori_pic = []

    def pic_append(self, img, ori_img):
        self.pic.append(img)
        self.ori_pic.append(ori_img)

    def predict_generate(self, path):
        img = imread(path)
        new_img = resize(img, (self.config.image_width, self.config.image_height), interpolation=INTER_AREA)
        self.pic_append(new_img, img)
        for item in self.pic:
            item = item / 255.0
            item = expand_dims(item, axis=0)
            yield item

    def deal_result(self, result, origin_width, origin_height):
        mask = resize(result[0], (origin_width, origin_height))
        mask[mask > 0.5] = 1
        mask[mask != 1] = 0
        mask = stack([mask, mask, mask], axis=-1)
        save_img = multiply(mask, self.ori_pic[0])
        return save_img

########################################
# Software
########################################
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


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
        data = SoftData(config=self.config)
        model = mobilenet_v2_unet()
        model.load_weights('mobilenet_v2_unet_0100.h5', by_name=True)
        result = model.predict_generator(data.predict_generate(filepath), 1)
        result = data.deal_result(result, origin_width, origin_height)
        return result

    def open_clicked(self, checked):
        self.filename = QFileDialog.getOpenFileName(self, "OpenFile", ".",
            "Image Files(*.jpg *.jpeg *.png)")[0]
        if len(self.filename):
            src = QImage(self.filename)
            self.img_name = (self.filename.split('/')[-1]).split('.')[0]
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


if __name__ == "__main__":
    from sys import argv
    app = QApplication(argv)
    config = Config
    dia = CarvanaSoftware(config)
    dia.show()
    app.exec_()

