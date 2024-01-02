import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtCore import pyqtSlot

import cv2

from UI.ui import Ui_MainWindow

import nibabel as nib

import numpy as np

class MyMainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent=parent)
        self.setupUi(self)
        # add attribute, link function here

        # default image
        self.ct_data = nib.load('Data\Zx00AD16F8B97A53DE6E7CFE260BDF122F0E655659A3DF1628.nii.gz')
        self.ct_image = self.ct_data.get_fdata()
        # normalize ct image
        self.ct_image = (self.ct_image - self.ct_image.min()) / (self.ct_image.max() - self.ct_image.min())*255
        # reshape the z axis
        extend = np.zeros((self.ct_image.shape[0], self.ct_image.shape[0], 660))
        for i in range(self.ct_image.shape[1]):
            extend[:, i, :] = cv2.resize(self.ct_image[:, i, :], (660, self.ct_image.shape[0]), interpolation=cv2.INTER_CUBIC) 
        self.ct_image = extend.astype(np.uint8)

        # default index, should be determined by the slider
        self.x_index = 0
        self.y_index = 0
        self.z_index = 0

        # define thickness of line
        self.thickness = 2
        self.rect_length = 50

        # link slider 
        self.x_slice_slider.valueChanged.connect(self.x_slice_slider_changed)
        self.y_slice_slider.valueChanged.connect(self.y_slice_slider_changed)
        self.z_slice_slider.valueChanged.connect(self.z_slice_slider_changed)

    def qimg2np(self, qimg):
        # input qimg is a QImage object and output arr is a numpy array
        qimg = qimg.convertToFormat(QtGui.QImage.Format.Format_Grayscale8)
        width = qimg.width()
        height = qimg.height()
        ptr = qimg.bits()
        ptr.setsize(qimg.byteCount())
        arr = np.array(ptr).reshape(height, width)
        return arr

    def np2qimg(self, arr):
        # and output qimg is a QImage object
        print(arr.shape)
        arr_bytes = bytes(arr)
        height, width, channel = arr.shape
        bytesPerLine = width*3
        qimg = QtGui.QImage(arr_bytes, width, height, bytesPerLine, QtGui.QImage.Format.Format_RGB888)
        # qimg = QtGui.QImage(arr_bytes, width, height, bytesPerLine, QtGui.QImage.Format.Format_Grayscale8)
        return qimg

    def show_image(self, image, graphicsView):
        # show image in graphicsView
        pixmap = QtGui.QPixmap.fromImage(self.np2qimg(image))
        pixmap.scaled(graphicsView.size(), QtCore.Qt.KeepAspectRatio)
        scene = QtWidgets.QGraphicsScene()
        scene.addPixmap(pixmap)
        graphicsView.setScene(scene)
        graphicsView.fitInView(scene.sceneRect(), QtCore.Qt.KeepAspectRatio)
    
    def show_x_image(self):
        # show x image main view and focus view
        image_temp = self.ct_image[self.x_index, :, ::-1].T
        image_temp = cv2.cvtColor(image_temp, cv2.COLOR_GRAY2RGB)
        # draw line on image according to y_index and z_index
        image_temp[:, self.y_index-self.thickness:self.y_index+self.thickness, 1] = 255
        image_temp[self.z_index-self.thickness:self.z_index+self.thickness, :, 1] = 255
        image_temp_focus = image_temp[self.z_index-50:self.z_index+50, self.y_index-50:self.y_index+50, :].copy()
        cv2.rectangle(image_temp, (self.y_index-self.rect_length, self.z_index-self.rect_length), (self.y_index+self.rect_length, self.z_index+self.rect_length), (0, 255, 0), self.thickness)
        self.show_image(image_temp, self.x_view)
        self.show_image(image_temp_focus, self.x_view_focus)


    def show_y_image(self):
        # show y image main view and focus view
        image_temp = self.ct_image[:, self.y_index, ::-1].T
        image_temp = cv2.cvtColor(image_temp, cv2.COLOR_GRAY2RGB)
        # draw line on image according to x_index and z_index
        image_temp[:, self.x_index-self.thickness:self.x_index+self.thickness, 1] = 255
        image_temp[self.z_index-self.thickness:self.z_index+self.thickness, :, 1] = 255
        image_temp_focus = image_temp[self.z_index-50:self.z_index+50, self.x_index-50:self.x_index+50, :].copy()
        cv2.rectangle(image_temp, (self.x_index-self.rect_length, self.z_index-self.rect_length), (self.x_index+self.rect_length, self.z_index+self.rect_length), (0, 255, 0), self.thickness)
        self.show_image(image_temp, self.y_view)
        self.show_image(image_temp_focus, self.y_view_focus)

    def show_z_image(self):
        # show z image main view and focus view
        image_temp = self.ct_image[:, :, self.z_index].T
        image_temp = cv2.cvtColor(image_temp, cv2.COLOR_GRAY2RGB)
        # draw line on image according to x_index and y_index
        image_temp[:, self.x_index-self.thickness:self.x_index+self.thickness, 1] = 255
        image_temp[self.y_index-self.thickness:self.y_index+self.thickness, :, 1] = 255
        image_temp_focus = image_temp[self.y_index-50:self.y_index+50, self.x_index-50:self.x_index+50, :].copy()
        cv2.rectangle(image_temp, (self.x_index-self.rect_length, self.y_index-self.rect_length), (self.x_index+self.rect_length, self.y_index+self.rect_length), (0, 255, 0), self.thickness)
        self.show_image(image_temp, self.z_view)
        self.show_image(image_temp_focus, self.z_view_focus)


    def show_ct_image(self):
        # show ct image in each graphicsView
        self.show_x_image() # use this function to show x image (and y, z image also)
        self.show_y_image() 
        self.show_z_image()
        # self.show_image(self.ct_image[self.x_index, :, ::-1].T, self.x_view)
        # self.show_image(self.ct_image[:, self.y_index, ::-1].T, self.y_view)
        # self.show_image(self.ct_image[:, :, self.z_index].T, self.z_view)

    def slider_range(self):
        # set slider range according to ct image
        self.x_slice_slider.setMinimum(0)
        self.x_slice_slider.setMaximum(self.ct_image.shape[0]-1)
        self.y_slice_slider.setMinimum(0)
        self.y_slice_slider.setMaximum(self.ct_image.shape[1]-1)
        self.z_slice_slider.setMinimum(0)
        self.z_slice_slider.setMaximum(self.ct_image.shape[2]-1)

    def x_slice_slider_changed(self):
        # change x_index according to slider
        self.x_index = self.x_slice_slider.value()
        self.show_ct_image()    

    def y_slice_slider_changed(self):
        # change y_index according to slider
        self.y_index = self.y_slice_slider.value()
        self.show_ct_image()

    def z_slice_slider_changed(self):
        # change z_index according to slider
        self.z_index = self.z_slice_slider.value()
        self.show_ct_image()

                

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    
    window.slider_range()
    window.show_ct_image() 
    # do this for test, should be called in read_image function implemented
    
    sys.exit(app.exec_())
