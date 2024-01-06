import sys

import pandas as pd

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtCore import pyqtSlot

import cv2

from UI.ui import Ui_MainWindow

import nibabel as nib

import numpy as np

from enum import Enum

from copy import deepcopy

import os

class DIRECTION(Enum):
    X = 1
    Y = 2
    Z = 3

class COLOR(Enum):
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)

class MyMainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent=parent)
        self.setupUi(self)
        # add attribute, link function here
        self.ct_image = None
        self.ct_image_name = None

        # define thickness of line
        self.thickness = 2 #set the value larger than 2 to see more clearly
        self.rect_length = 100

        # default index, should be determined by the slider
        self.x_index = 0
        self.y_index = 0
        self.z_index = 0


        self.record_coord_list = []
        self.opened_file_list = []
        self.current_open_file_folder = ''

        # link slider 
        self.x_slice_slider.valueChanged.connect(lambda: self.slice_slider_changed(DIRECTION.X))
        self.y_slice_slider.valueChanged.connect(lambda: self.slice_slider_changed(DIRECTION.Y))
        self.z_slice_slider.valueChanged.connect(lambda: self.slice_slider_changed(DIRECTION.Z))

        # link button
        self.x_plus_1.clicked.connect(lambda: self.plus_minus_1(DIRECTION.X, 1))
        self.x_minus_1.clicked.connect(lambda: self.plus_minus_1(DIRECTION.X, -1))
        self.y_plus_1.clicked.connect(lambda: self.plus_minus_1(DIRECTION.Y, 1))
        self.y_minus_1.clicked.connect(lambda: self.plus_minus_1(DIRECTION.Y, -1))
        self.z_plus_1.clicked.connect(lambda: self.plus_minus_1(DIRECTION.Z, 1))
        self.z_minus_1.clicked.connect(lambda: self.plus_minus_1(DIRECTION.Z, -1))
        self.select_folder.clicked.connect(self.select_folder_clicked)
        self.record_coord.clicked.connect(self.record_coord_clicked)
        self.save_to_csv.clicked.connect(self.save_to_csv_clicked)

        # list element clicked
        self.file_list.itemClicked.connect(self.file_list_clicked)

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
        image_temp[:, self.y_index-self.thickness:self.y_index+self.thickness, :] = COLOR.RED.value
        image_temp[self.z_index-self.thickness:self.z_index+self.thickness, :, :] = COLOR.RED.value
        
        image_temp_focus = image_temp[max(0, self.z_index-50):min(self.z_index+50, self.ct_image.shape[2]), max(0, self.y_index-50):min(self.y_index+50, self.ct_image.shape[1]), :].copy()
        
        cv2.rectangle(image_temp, (self.y_index-self.rect_length, self.z_index-self.rect_length), (self.y_index+self.rect_length, self.z_index+self.rect_length), COLOR.YELLOW.value, self.thickness)
        self.show_image(image_temp, self.x_view)
        self.show_image(image_temp_focus, self.x_view_focus)

    def show_y_image(self):
        # show y image main view and focus view
        image_temp = self.ct_image[:, self.y_index, ::-1].T
        image_temp = cv2.cvtColor(image_temp, cv2.COLOR_GRAY2RGB)
        # draw line on image according to x_index and z_index
        image_temp[:, self.x_index-self.thickness:self.x_index+self.thickness, :] = COLOR.RED.value
        image_temp[self.z_index-self.thickness:self.z_index+self.thickness, :, :] = COLOR.RED.value

        image_temp_focus = image_temp[max(0, self.z_index-50):min(self.z_index+50, self.ct_image.shape[2]), max(0, self.x_index-50):min(self.x_index+50, self.ct_image.shape[0]), :].copy()

        cv2.rectangle(image_temp, 
            (self.x_index-self.rect_length, self.z_index-self.rect_length), (self.x_index+self.rect_length, self.z_index+self.rect_length), 
            COLOR.YELLOW.value,
            self.thickness)
        self.show_image(image_temp, self.y_view)
        self.show_image(image_temp_focus, self.y_view_focus)

    def show_z_image(self):
        # show z image main view and focus view
        image_temp = self.ct_image[:, :, self.z_index].T
        image_temp = cv2.cvtColor(image_temp, cv2.COLOR_GRAY2RGB)
        # draw line on image according to x_index and y_index
        image_temp[:, self.x_index-self.thickness:self.x_index+self.thickness, :] = COLOR.RED.value
        image_temp[self.y_index-self.thickness:self.y_index+self.thickness, :, :] = COLOR.RED.value
        
        image_temp_focus = image_temp[max(0, self.y_index-50):min(self.y_index+50, self.ct_image.shape[1]), max(0, self.x_index-50):min(self.x_index+50, self.ct_image.shape[0]), :].copy()

        cv2.rectangle(image_temp, (self.x_index-self.rect_length, self.y_index-self.rect_length), (self.x_index+self.rect_length, self.y_index+self.rect_length), COLOR.YELLOW.value, self.thickness)
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

    def slice_slider_changed(self, direction):
        if direction == DIRECTION.X:
            self.x_index = self.x_slice_slider.value()
        elif direction == DIRECTION.Y:
            self.y_index = self.y_slice_slider.value()
        elif direction == DIRECTION.Z:
            self.z_index = self.z_slice_slider.value()
        self.show_ct_image()

    def plus_minus_1(self, direction, value):
        if direction == DIRECTION.X:
            self.x_index += value
            self.x_slice_slider.setValue(self.x_index)
        elif direction == DIRECTION.Y:
            self.y_index += value
            self.y_slice_slider.setValue(self.y_index)
        elif direction == DIRECTION.Z:
            self.z_index += value
            self.z_slice_slider.setValue(self.z_index)

    def select_folder_clicked(self):
        # just open ./Data folder
        # self.current_open_file_folder = './Data'
        # select folder and read image
        self.current_open_file_folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        
        self.opened_file_list.clear()
        for file in os.listdir(self.current_open_file_folder):
            if file.endswith('.nii.gz'):
                self.opened_file_list.append(file)
        self.opened_file_list.sort()

        for file in self.opened_file_list:
            self.file_list.addItem(file)

    def read_image(self, file_path):
        # clear coord list
        self.record_coord_list.clear()
        self.coord_list.clear()

        # read image from file_path
        ct_data = nib.load(file_path)
        self.ct_image = ct_data.get_fdata()
        self.ct_image_name = os.path.basename(file_path)
        
        # normalize ct image
        self.ct_image = (self.ct_image - self.ct_image.min()) / (self.ct_image.max() - self.ct_image.min())*255
        extend = np.zeros((self.ct_image.shape[0], self.ct_image.shape[0], 660))
        for i in range(self.ct_image.shape[1]):
            extend[:, i, :] = cv2.resize(self.ct_image[:, i, :], (660, self.ct_image.shape[0]), interpolation=cv2.INTER_CUBIC)
        self.ct_image = extend.astype(np.uint8)
        self.slider_range()
        self.show_ct_image()
        # if there are corresponding coord file, read it
        coord_file_path = os.path.join('Data', '{}_coord.csv'.format(self.ct_image_name))
        if os.path.exists(coord_file_path):
            df = pd.read_csv(coord_file_path)
            self.record_coord_list = df.values.tolist()
            self.coord_list.clear()
            for coord in self.record_coord_list:
                self.coord_list.addItem(str(coord))

    def file_list_clicked(self):
        self.init_for_new_image()
        image_name = self.file_list.currentItem().text()
        file_path = os.path.join(self.current_open_file_folder, image_name)
        self.read_image(file_path)

    def save_to_csv_clicked(self):
        print(self.ct_image_name)
        if self.ct_image_name is None:
            return
        # save coord list to csv file
        df = pd.DataFrame(self.record_coord_list, columns=['x', 'y', 'z'])
        # df.to_csv("Data/{}_coord.csv".format(self.ct_image_name), index=False)
        df.to_csv(os.path.join(self.current_open_file_folder, '{}_coord.csv'.format(self.ct_image_name)), index=False)

    def record_coord_clicked(self):
        # check if the coord is already in the list
        for coord in self.record_coord_list:
            if coord[0] == self.x_index and coord[1] == self.y_index and coord[2] == self.z_index:
                return
        self.record_coord_list.append([self.x_index, self.y_index, self.z_index])
        self.ct_image[self.x_index, self.y_index, self.z_index] = 255
        self.record_coord_list.sort()
        
        # show the coord in the list
        self.coord_list.clear()
        for coord in self.record_coord_list:
            self.coord_list.addItem(str(coord))

    def init_for_new_image(self):
        # init everything except file list
        self.x_slice_slider.setValue(0)
        self.y_slice_slider.setValue(0)
        self.z_slice_slider.setValue(0)
        self.coord_list.clear()


    
    



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    
    # do this for test, should be called in read_image function implemented
    
    sys.exit(app.exec_())
