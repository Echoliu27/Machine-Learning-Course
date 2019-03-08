# -*- coding: utf-8 -*-
"""SolarPV.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1IyudFPmmKLH05F5LMBcnMcDy8hOhS_fj
"""

# import libraries to use
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn import svm
import sklearn.metrics as metrics
import time
from scipy import ndimage

import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten, Activation
from keras.layers import Conv2D, MaxPooling2D
from keras.layers.normalization import BatchNormalization
from keras.preprocessing.image import ImageDataGenerator
from keras.applications.vgg16 import VGG16
from keras.models import Model
import os

# upload files to Google Colab
from google.colab import files
uploaded = files.upload()

uploaded = files.upload()

# move files around and unzip
!mkdir "./data"
!mkdir "./data/training"
!mkdir "./data/testing"
!unzip "./testing.zip" -d "./data/testing"
!unzip "./training.zip" -d "./data/training"
!mv "labels_training.csv" "./data"
!mv "sample_submission.csv" "./data"

# Set the directories for the data and the CSV files that contain ids/labels
dir_train_images  = './data/training/'
dir_test_images   = './data/testing/'
dir_train_labels  = './data/labels_training.csv'
dir_test_ids      = './data/sample_submission.csv'

def load_data(dir_data, dir_labels, training=True, grayscale=False):
    ''' Load each of the image files into memory 

    While this is feasible with a smaller dataset, for larger datasets,
    not all the images would be able to be loaded into memory

    When training=True, the labels are also loaded
    '''
    labels_pd = pd.read_csv(dir_labels)
    ids       = labels_pd.id.values
    data      = []
    for identifier in ids:
        fname     = dir_data + identifier.astype(str) + '.tif'
        image     = mpl.image.imread(fname)
        if grayscale:
            image = rgb2gray(image)
        filter_blurred = ndimage.gaussian_filter(image, 1)
        alpha = -100
        image = image + alpha * (image - filter_blurred)
        data.append(image)
    data = np.array(data) # Convert to Numpy array
    if training:
        labels = labels_pd.label.values
        return data, labels
    else:
        return data, ids

# load data
data, labels = load_data(dir_train_images, dir_train_labels, training=True, grayscale=False)

# find the dimensions of the images array
dims = data.shape
sample_size, img_rows, img_cols, depth = dims


## Split training and validation sets
split_prop = 9/10  # proportion of data to be training data
train_size = int(np.ceil(sample_size*split_prop))  # tend towards bigger training set
train_inds = sorted(np.random.choice(np.arange(sample_size),
                                     train_size,
                                     replace=False))
validate_inds = np.setdiff1d(np.arange(sample_size), train_inds)  # find inds not in training set

imgs_train = data[train_inds]
imgs_validate = data[validate_inds]

num_classes = 2
labels_train = keras.utils.to_categorical(labels[train_inds], num_classes)
labels_validate = keras.utils.to_categorical(labels[validate_inds], num_classes)

print('imgs_train shape:', imgs_train.shape)
print(imgs_train.shape[0], 'train samples')
print(imgs_validate.shape[0], 'test samples')

# define the CNN model
model = Sequential()
model.add(Conv2D(32, kernel_size = (3, 3), activation='relu', input_shape=(img_rows, img_cols, depth)))
model.add(MaxPooling2D(pool_size=(2,2)))
model.add(BatchNormalization())

model.add(Conv2D(64, kernel_size=(3,3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2,2)))
model.add(BatchNormalization())

model.add(Conv2D(96, kernel_size=(3,3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2,2)))
model.add(BatchNormalization())

model.add(Conv2D(96, kernel_size=(3,3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2,2)))
model.add(BatchNormalization())

model.add(Conv2D(64, kernel_size=(3,3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2,2)))
model.add(BatchNormalization())


model.add(Dropout(0.2))

model.add(Flatten())


model.add(Dense(1024, activation='relu'))
model.add(Dropout(0.2))
model.add(BatchNormalization())

model.add(Dense(2048, activation='relu'))
model.add(Dropout(0.3))
model.add(BatchNormalization())

model.add(Dense(2, activation = 'softmax'))

model.compile(loss="binary_crossentropy",
              optimizer="Adadelta",
              metrics=['accuracy'])

# train the model using data generator
epochs = 20

datagen = ImageDataGenerator(
    featurewise_center=True,
    featurewise_std_normalization=True,
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    horizontal_flip=True)
	
model.fit_generator(datagen.flow(imgs_train, labels_train, batch_size=batch_size),
                    steps_per_epoch=len(imgs_train) / 32, epochs=epochs, validation_data=(imgs_validate, labels_validate))

  print('Test loss:', score[0])
  print('Test accuracy:', score[1])

# load the test data
testdata, test_ids = load_data(dir_test_images, dir_test_ids, training=False, grayscale=False)

# predict labels on test data
predictions = model.predict(testdata)

# verify predictions reasonable
print(min(predictions[:,1]), max(predictions[:,1]))

# create submission file
submission_file = pd.DataFrame({'id':    test_ids, 'score':  predictions[:,1]})
submission_file.to_csv('submission.csv', columns=['id','score'],index=False)