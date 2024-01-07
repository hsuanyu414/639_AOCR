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

import matplotlib.pyplot as plt

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

        # window width & window level
        self.ww = 400
        self.wl = 40

        # mask image & cube size
        self.mask_image = None
        self.cube_size = [8, 8, 8]
        self.mask_alpha = 0.7
        self.line_alpha = 0.7

        # coord list sort option
        self.coord_list_sort_option = 'value'

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

        # csv file path for saving coord list
        self.csv_file_path = './mask_csv'
        if not os.path.exists(self.csv_file_path):
            os.mkdir(self.csv_file_path)

        # link slider 
        self.x_slice_slider.valueChanged.connect(lambda: self.slice_slider_changed(DIRECTION.X))
        self.y_slice_slider.valueChanged.connect(lambda: self.slice_slider_changed(DIRECTION.Y))
        self.z_slice_slider.valueChanged.connect(lambda: self.slice_slider_changed(DIRECTION.Z))
        self.focus_slider.valueChanged.connect(self.focus_slider_changed)
        self.mask_alpha_slider.valueChanged.connect(lambda: self.alpha_slider_changed("mask"))
        self.line_alpha_slider.valueChanged.connect(lambda: self.alpha_slider_changed("line"))

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
        self.delete_coord.clicked.connect(self.delete_coord_clicked)
        self.coord_list_sort.clicked.connect(self.coord_list_sort_clicked)
        self.coord_list_clear.clicked.connect(self.coord_list_clear_clicked)
        self.csv_restore.clicked.connect(self.csv_restore_clicked)

        # list element clicked
        self.file_list.itemClicked.connect(self.file_list_clicked)
        self.coord_list.itemDoubleClicked.connect(self.coord_list_double_clicked)

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

        # clip and normalize image
        image_temp[image_temp > self.wl+self.ww/2] = self.wl+self.ww/2
        image_temp[image_temp < self.wl-self.ww/2] = self.wl-self.ww/2
        image_temp = cv2.normalize(image_temp, None, 0, 255, cv2.NORM_MINMAX)
        image_temp = image_temp.astype(np.uint8)
        image_temp = cv2.cvtColor(image_temp, cv2.COLOR_GRAY2RGB)

        # draw line on image according to y_index and z_index
        reverse_z_index = abs(self.z_index - self.ct_image.shape[2])
        image_temp[:, self.y_index-self.thickness:self.y_index+self.thickness, :] = \
            tuple([x * self.line_alpha for x in COLOR.RED.value]) + image_temp[:, self.y_index-self.thickness:self.y_index+self.thickness, :] * (1 - self.line_alpha)
        image_temp[reverse_z_index-self.thickness:reverse_z_index+self.thickness, :, :] = \
            tuple([x * self.line_alpha for x in COLOR.RED.value]) + image_temp[reverse_z_index-self.thickness:reverse_z_index+self.thickness, :, :] * (1 - self.line_alpha)

        # add mask image to red channel
        if self.mask_image is not None:
            mark_temp = self.mask_image[self.x_index, :, ::-1].T
            image_temp[mark_temp > 0, :] = tuple([x * self.mask_alpha for x in COLOR.GREEN.value]) + image_temp[mark_temp > 0, :] * (1 - self.mask_alpha)
        
        # set all pixels to 255
        image_temp_focus = np.ones((self.rect_length * 2, self.rect_length * 2, 3), dtype=np.uint8) * 255
        image_temp_focus[abs(min(reverse_z_index - self.rect_length, 0)): min(self.rect_length + self.ct_image.shape[2] - reverse_z_index, self.rect_length * 2),\
                         abs(min(self.y_index - self.rect_length, 0)): min(self.rect_length + self.ct_image.shape[1] - self.y_index, self.rect_length * 2), :] = \
            image_temp[max(0, reverse_z_index-self.rect_length):min(reverse_z_index+self.rect_length, self.ct_image.shape[2]), max(0, self.y_index-self.rect_length):min(self.y_index+self.rect_length, self.ct_image.shape[1]), :].copy()
        # image_temp_focus = image_temp[max(0, reverse_z_index-self.rect_length):min(reverse_z_index+self.rect_length, self.ct_image.shape[2]), max(0, self.y_index-self.rect_length):min(self.y_index+self.rect_length, self.ct_image.shape[1]), :].copy()


        cv2.rectangle(image_temp, (self.y_index-self.rect_length, reverse_z_index-self.rect_length), (self.y_index+self.rect_length, reverse_z_index+self.rect_length), COLOR.YELLOW.value, self.thickness)
        self.show_image(image_temp, self.x_view)
        self.show_image(image_temp_focus, self.x_view_focus)

    def show_y_image(self):
        # show y image main view and focus view
        image_temp = self.ct_image[:, self.y_index, ::-1].T

        # clip and normalize image
        image_temp[image_temp > self.wl+self.ww/2] = self.wl+self.ww/2
        image_temp[image_temp < self.wl-self.ww/2] = self.wl-self.ww/2
        image_temp = cv2.normalize(image_temp, None, 0, 255, cv2.NORM_MINMAX)
        image_temp = image_temp.astype(np.uint8)
        image_temp = cv2.cvtColor(image_temp, cv2.COLOR_GRAY2RGB)

        # draw line on image according to x_index and z_index
        reverse_z_index = abs(self.z_index - self.ct_image.shape[2])
        image_temp[:, self.x_index-self.thickness:self.x_index+self.thickness, :] = \
            tuple([x * self.line_alpha for x in COLOR.RED.value]) + image_temp[:, self.x_index-self.thickness:self.x_index+self.thickness, :] * (1 - self.line_alpha)
        image_temp[reverse_z_index-self.thickness:reverse_z_index+self.thickness, :, :] = \
            tuple([x * self.line_alpha for x in COLOR.RED.value]) + image_temp[reverse_z_index-self.thickness:reverse_z_index+self.thickness, :, :] * (1 - self.line_alpha)

        # add mask image to red channel
        if self.mask_image is not None:
            mark_temp = self.mask_image[:, self.y_index, ::-1].T
            image_temp[mark_temp > 0, :] = tuple([x * self.mask_alpha for x in COLOR.GREEN.value]) + image_temp[mark_temp > 0, :] * (1 - self.mask_alpha)

        # set all pixels to 255
        image_temp_focus = np.ones((self.rect_length * 2, self.rect_length * 2, 3), dtype=np.uint8) * 255
        image_temp_focus[abs(min(reverse_z_index - self.rect_length, 0)): min(self.rect_length + self.ct_image.shape[2] - reverse_z_index, self.rect_length * 2),\
                            abs(min(self.x_index - self.rect_length, 0)): min(self.rect_length + self.ct_image.shape[0] - self.x_index, self.rect_length * 2), :] = \
            image_temp[max(0, reverse_z_index-self.rect_length):min(reverse_z_index+self.rect_length, self.ct_image.shape[2]), max(0, self.x_index-self.rect_length):min(self.x_index+self.rect_length, self.ct_image.shape[0]), :].copy()
        
        cv2.rectangle(image_temp, 
            (self.x_index-self.rect_length, reverse_z_index-self.rect_length), (self.x_index+self.rect_length, reverse_z_index+self.rect_length), 
            COLOR.YELLOW.value,
            self.thickness)
        self.show_image(image_temp, self.y_view)
        self.show_image(image_temp_focus, self.y_view_focus)

    def show_z_image(self):
        # show z image main view and focus view
        image_temp = self.ct_image[:, :, self.z_index]

        # clip and normalize image
        image_temp[image_temp > self.wl+self.ww/2] = self.wl+self.ww/2
        image_temp[image_temp < self.wl-self.ww/2] = self.wl-self.ww/2
        image_temp = cv2.normalize(image_temp, None, 0, 255, cv2.NORM_MINMAX)
        image_temp = image_temp.astype(np.uint8)
        image_temp = cv2.cvtColor(image_temp, cv2.COLOR_GRAY2RGB)

        # draw line on image according to x_index and y_index
        image_temp[:, self.y_index-self.thickness:self.y_index+self.thickness, :] = \
            tuple([x * self.line_alpha for x in COLOR.RED.value]) + image_temp[:, self.y_index-self.thickness:self.y_index+self.thickness, :] * (1 - self.line_alpha)
        image_temp[self.x_index-self.thickness:self.x_index+self.thickness, :, :] = \
            tuple([x * self.line_alpha for x in COLOR.RED.value]) + image_temp[self.x_index-self.thickness:self.x_index+self.thickness, :, :] * (1 - self.line_alpha)

        # add mask image to red channel
        if self.mask_image is not None:
            mark_temp = self.mask_image[:, :, self.z_index]
            image_temp[mark_temp > 0, :] = tuple([x * self.mask_alpha for x in COLOR.GREEN.value]) + image_temp[mark_temp > 0, :] * (1 - self.mask_alpha)
        
        # set all pixels to 255
        image_temp_focus = np.ones((self.rect_length * 2, self.rect_length * 2, 3), dtype=np.uint8) * 255
        image_temp_focus[abs(min(self.x_index - self.rect_length, 0)): min(self.rect_length + self.ct_image.shape[0] - self.x_index, self.rect_length * 2),\
                            abs(min(self.y_index - self.rect_length, 0)): min(self.rect_length + self.ct_image.shape[1] - self.y_index, self.rect_length * 2), :] = \
            image_temp[max(0, self.x_index-self.rect_length):min(self.x_index+self.rect_length, self.ct_image.shape[0]), max(0, self.y_index-self.rect_length):min(self.y_index+self.rect_length, self.ct_image.shape[1]), :].copy()
        
        cv2.rectangle(image_temp, (self.y_index-self.rect_length, self.x_index-self.rect_length), (self.y_index+self.rect_length, self.x_index+self.rect_length), COLOR.YELLOW.value, self.thickness)

        # rotate image 90 degree
        image_temp = cv2.rotate(image_temp, cv2.ROTATE_90_COUNTERCLOCKWISE)
        image_temp_focus = cv2.rotate(image_temp_focus, cv2.ROTATE_90_COUNTERCLOCKWISE)

        self.show_image(image_temp, self.z_view)
        self.show_image(image_temp_focus, self.z_view_focus)

    def show_ct_image(self):
        try:
            if self.ct_image is None:
                return
            # show ct image in each graphicsView
            self.show_x_image() # use this function to show x image (and y, z image also)
            self.show_y_image() 
            self.show_z_image()
            # self.show_image(self.ct_image[self.x_index, :, ::-1].T, self.x_view)
            # self.show_image(self.ct_image[:, self.y_index, ::-1].T, self.y_view)
            # self.show_image(self.ct_image[:, :, self.z_index].T, self.z_view)
        except:
            print("show_ct_image error")
            return

    def focus_mark(self, coord_focus, flag):
        """
        Mark / Erase the coord with mouse click in focus view
            flag: 0. mark, 1. erase
            * The range of erase is 2 times of cube size
            * The range of mark is 1 time of cube size
            Input:
                coord_focus:
                    type: list
                    description: index of single record
                    example: [x, y, z]
        """
        try:
            if self.ct_image is None or self.mask_image is None:
                return
            # coord_focus contain negative value
            if coord_focus[0] < 0 or coord_focus[1] < 0 or coord_focus[2] < 0 or \
                coord_focus[0] >= self.ct_image.shape[0] or coord_focus[1] >= self.ct_image.shape[1]\
                or coord_focus[2] >= self.ct_image.shape[2]:
                return
            elif coord_focus[0] < self.x_index - self.rect_length or coord_focus[0] > self.x_index + self.rect_length or \
                coord_focus[1] < self.y_index - self.rect_length or coord_focus[1] > self.y_index + self.rect_length or \
                coord_focus[2] < self.z_index - self.rect_length or coord_focus[2] > self.z_index + self.rect_length:
                return
            op = "mark" if flag == 0 else "erase"
            if op == "mark":
                # check if the coord is already in the list
                for coord in self.record_coord_list:
                    if coord[0] == coord_focus[0] and coord[1] == coord_focus[1] and coord[2] == coord_focus[2]:
                        return
                self.record_coord_list.append(coord_focus)
            elif op == "erase":
                for coord in self.record_coord_list:
                    if abs(coord[0] - coord_focus[0]) <= self.cube_size[0] * 1.3 and \
                    abs(coord[1] - coord_focus[1]) <= self.cube_size[1] * 1.3 and \
                    abs(coord[2] - coord_focus[2]) <= self.cube_size[2] * 1.3:
                        self.record_coord_list.remove(coord)
            
            # update coord list
            self.update_coord_list()

            # mark cube in the mask image
            self.mark_cube(coord_focus, op = op)

            # show image
            self.show_ct_image()
        except:
            print("focus_mark error")
            return

    def initialize_mask_image(self):
        """
        Initialize mask image
            1. set same size as ct image
            2. mark pixels in the coord list
        """
        try:
            if self.ct_image is None:
                return
            self.mask_image = np.zeros(self.ct_image.shape, dtype=np.uint8)
            if self.record_coord_list is None:
                return
            elif len(self.record_coord_list) == 0:
                return
            for coord in self.record_coord_list:
                self.mark_cube(coord)
        except:
            print("initialize_mask_image error")
            return

    def mark_cube(self, coord, op = "mark"):
        """
        Mark or erase cube in the mask image
            1. mark pixels in the coord list
            2. center of the cube is marked as 255
               other pixels in the cube is marked as 128
        Input: 
            coord_list:
                type: list
                description: index of single record
                example: [x, y, z]
        """
        try:
            if self.ct_image is None or self.mask_image is None:
                return
            half_cube_size = [int(self.cube_size[0]/2), int(self.cube_size[1]/2), int(self.cube_size[2]/2)]
            if op == "mark":
                self.mask_image[coord[0], coord[1], coord[2]] = 255
                self.mask_image[max(0, coord[0]-half_cube_size[0]):min(coord[0]+half_cube_size[0], self.mask_image.shape[0]), 
                                max(0, coord[1]-half_cube_size[1]):min(coord[1]+half_cube_size[1], self.mask_image.shape[1]), 
                                max(0, coord[2]-half_cube_size[2]):min(coord[2]+half_cube_size[2], self.mask_image.shape[2])] = 128
            elif op == "erase":
                # print("erase)
                self.mask_image[coord[0], coord[1], coord[2]] = 0
                # pixel in the cube is marked as 0
                self.mask_image[max(0, coord[0]-self.cube_size[0]):min(coord[0]+self.cube_size[0], self.mask_image.shape[0]), 
                                max(0, coord[1]-self.cube_size[1]):min(coord[1]+self.cube_size[1], self.mask_image.shape[1]), 
                                max(0, coord[2]-self.cube_size[2]):min(coord[2]+self.cube_size[2], self.mask_image.shape[2])] = 0
        except:
            print("mark_cube error")
            return
        
    def update_coord_list(self):
        """
        Update coord list according to sort option
        """
        try:
            if self.coord_list_sort_option == 'value':
                tmp_list = sorted(self.record_coord_list)
            elif self.coord_list_sort_option == 'add_time':
                tmp_list = self.record_coord_list[::-1]

            self.coord_list.clear()
            for coord in tmp_list:
                self.coord_list.addItem(str(coord))
        except:
            print("update_coord_list error")
            return

    def slider_range(self):
        # set slider range according to ct image
        self.x_slice_slider.setMinimum(0)
        self.x_slice_slider.setMaximum(self.ct_image.shape[0]-1)
        self.y_slice_slider.setMinimum(0)
        self.y_slice_slider.setMaximum(self.ct_image.shape[1]-1)
        self.z_slice_slider.setMinimum(0)
        self.z_slice_slider.setMaximum(self.ct_image.shape[2]-1)
        self.focus_slider.setMinimum(30)
        self.focus_slider.setMaximum(160)
        self.mask_alpha_slider.setMinimum(0)
        self.mask_alpha_slider.setMaximum(10)
        self.line_alpha_slider.setMinimum(0)
        self.line_alpha_slider.setMaximum(10)

    def slice_slider_changed(self, direction):
        try:
            if direction == DIRECTION.X:
                self.x_index = self.x_slice_slider.value()
            elif direction == DIRECTION.Y:
                self.y_index = self.y_slice_slider.value()
            elif direction == DIRECTION.Z:
                self.z_index = self.z_slice_slider.value()
            self.show_ct_image()
        except:
            print("slice_slider_changed error")
            return

    def focus_slider_changed(self):
        """
        Change the length of rectangle in focus view
        """
        try:
            self.rect_length = self.focus_slider.value()
            self.show_ct_image()
        except:
            pass

    def alpha_slider_changed(self, option):
        """
        Change the opacity of mask image
            option: a. mask
                    b. line
        """
        try:
            if option == "mask":
                self.mask_alpha = self.mask_alpha_slider.value() / 10
            elif option == "line":
                self.line_alpha = self.line_alpha_slider.value() / 10
            try:
                self.show_ct_image()
            except:
                pass
        except:
            print("alpha_slider_changed error")
            return

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
        try:
            self.current_open_file_folder = QFileDialog.getExistingDirectory(self, "Select Folder")
            self.opened_file_list.clear()
            self.file_list.clear()
            for file in os.listdir(self.current_open_file_folder):
                if file.endswith('.nii.gz'):
                    self.opened_file_list.append(file)
            self.opened_file_list.sort()

            for file in self.opened_file_list:
                self.file_list.addItem(file)
        except:
            return
        
    def read_csv(self):
        self.record_coord_list.clear()
        # if there are corresponding coord file, read it
        coord_file_path = os.path.join(self.csv_file_path, '{}_coord.csv'.format(self.ct_image_name))
        if os.path.exists(coord_file_path):
            df = pd.read_csv(coord_file_path)
            self.record_coord_list = df.values.tolist()
            self.coord_list.clear()
            for coord in self.record_coord_list:
                self.coord_list.addItem(str(coord))
    

    def read_image(self, file_path):
        try:
            # clear coord list
            self.record_coord_list.clear()
            self.coord_list.clear()

            # read image from file_path
            ct_data = nib.load(file_path)
            self.ct_image = ct_data.get_fdata()
            self.ct_image_name = os.path.basename(file_path)
            
            # normalize ct image
            extend = np.zeros((self.ct_image.shape[0], self.ct_image.shape[0], 660))
            for i in range(self.ct_image.shape[1]):
                extend[:, i, :] = cv2.resize(self.ct_image[:, i, :], (660, self.ct_image.shape[0]), interpolation=cv2.INTER_CUBIC)
            self.ct_image = extend

            self.read_csv()

            # initialize mask image
            self.initialize_mask_image()

            self.slider_range()
            self.show_ct_image()
        except:
            print("read_image error")
            return

    def file_list_clicked(self):
        try:
            self.init_for_new_image()
            image_name = self.file_list.currentItem().text()
            file_path = os.path.join(self.current_open_file_folder, image_name)
            self.read_image(file_path)
        except:
            print("file_list_clicked error")
            return

    def coord_list_double_clicked(self):
        """
        Relocate the focus view according to the coord
        """
        try:
            selected_coord = self.coord_list.currentItem().text()
            selected_coord = selected_coord.replace('[', '').replace(']', '')
            selected_coord = selected_coord.split(',')
            selected_coord = [int(coord) for coord in selected_coord]
            self.x_index = selected_coord[0]
            self.y_index = selected_coord[1]
            self.z_index = selected_coord[2]
            self.x_slice_slider.setValue(self.x_index)
            self.y_slice_slider.setValue(self.y_index)
            self.z_slice_slider.setValue(self.z_index)
            self.show_ct_image()
        except:
            print("coord_list_double_clicked error")
            return

    def save_to_csv_clicked(self):
        try:
            if self.ct_image_name is None:
                return
            # save coord list to csv file
            df = pd.DataFrame(self.record_coord_list, columns=['x', 'y', 'z'])
            # df.to_csv("Data/{}_coord.csv".format(self.ct_image_name), index=False)
            df.to_csv(os.path.join(self.csv_file_path, '{}_coord.csv'.format(self.ct_image_name)), index=False)

            # show a small window to indicate saving success
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setText("Save to csv successfully")
            msg.setWindowTitle("Save to csv")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg.exec_()
        except:
            print("save_to_csv_clicked error")
            return


    def record_coord_clicked(self):
        try:
            if self.ct_image_name is None:
                return
            # check if the coord is already in the list
            for coord in self.record_coord_list:
                if coord[0] == self.x_index and coord[1] == self.y_index and coord[2] == self.z_index:
                    return
            self.record_coord_list.append([self.x_index, self.y_index, self.z_index])
            # self.ct_image[self.x_index, self.y_index, self.z_index] = 255
            
            # update coord list
            self.update_coord_list()

            # mark cube in the mask image
            self.mark_cube([self.x_index, self.y_index, self.z_index])

            # show image
            self.show_ct_image()
        except:
            print("record_coord_clicked error")
            return

    def delete_coord_clicked(self):
        """
        Delete selected coord
            1. get coord from coord list or current index
               if current index is not in the coord list, do nothing
            2. delete coord from coord list
            3. delete mark in the mask image
            4. show image
            5. update coord list
        """
        # get selected coord
        try:
            selected_coord = self.coord_list.currentItem().text()
            selected_coord = selected_coord.replace('[', '').replace(']', '')
            selected_coord = selected_coord.split(',')
            selected_coord = [int(coord) for coord in selected_coord]
            # delete coord from coord list
            self.record_coord_list.remove(selected_coord)
        except:
            selected_coord = [self.x_index, self.y_index, self.z_index]
            if selected_coord in self.record_coord_list:
                self.record_coord_list.remove(selected_coord)
            else:
                return

        try:
            # delete coord from mask image
            self.mark_cube(selected_coord, op="erase")

            # show image
            self.show_ct_image()

            # update coord list
            self.update_coord_list()
        except:
            print("delete_coord_clicked error")
            return

    def coord_list_sort_clicked(self):
        """
        Change the order of coord list
        option: a. sort by x, y, z value
                b. sort by add time
        """
        if self.coord_list_sort_option == 'value':
            self.coord_list_sort_option = 'add_time'
            self.coord_list_sort.setText('Sort by add time')
        elif self.coord_list_sort_option == 'add_time':
            self.coord_list_sort_option = 'value'
            self.coord_list_sort.setText('Sort by value')
        self.update_coord_list()

    def coord_list_clear_clicked(self):
        """
        Clear coord list
        """
        try:
            self.record_coord_list.clear()
            self.coord_list.clear()
            self.initialize_mask_image()
            self.show_ct_image()
        except:
            print("coord_list_clear_clicked error")
            return
        
    def csv_restore_clicked(self):
        """
        Restore coord list from csv file
        """
        try:
            self.read_csv()
            self.initialize_mask_image()
            self.show_ct_image()
        except:
            print("csv_restore_clicked error")
            return

    def init_for_new_image(self):
        # init everything except file list
        self.x_slice_slider.setValue(0)
        self.y_slice_slider.setValue(0)
        self.z_slice_slider.setValue(0)
        self.focus_slider.setValue(self.rect_length)
        self.mask_alpha_slider.setValue(int(self.mask_alpha * 10))
        self.line_alpha_slider.setValue(int(self.line_alpha * 10))
        self.coord_list.clear()


    
    



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    
    # do this for test, should be called in read_image function implemented
    
    sys.exit(app.exec_())
