from CarvanaDataset import *


class SoftData(DataSet):
    def __init__(self, config, mode):
        super(SoftData, self).__init__(config=config, mode=mode)
        assert mode == 'prediction'
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
            item = np.expand_dims(item, axis=0)
            yield item

    def deal_result(self, result, origin_width, origin_height):
        mask = resize(result[0], (origin_width, origin_height))
        mask[mask > 0.5] = 1
        mask[mask != 1] = 0
        mask = np.stack([mask, mask, mask], axis=-1)
        save_img = np.multiply(mask, self.ori_pic[0])
        # save_img = np.multiply(mask, self.ori_pic[0])/255.
        # import matplotlib.pyplot as plt
        # plt.imshow(save_img)
        # plt.show()
        return save_img
