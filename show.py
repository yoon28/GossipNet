import argparse
import cv2
import os

try:
    import cPickle as pickle
except ImportError:
    import pickle

import numpy as np
import imdb

with open('/home/yoon28/workspace/gossipnet-master/data/cache/coco_2014_minival_FRCN_train_imdb_cache.pkl','rb') as fp:
    dataPkl = pickle.load(fp)

class_to_ind = dataPkl['class_to_ind']

DATA = dataPkl['roidb']
for datum in DATA:
    img = cv2.imread(datum['filename'])

    n_dt = len(datum['det_classes'])
    for i in range(n_dt):
        x1 = datum['dets'][i][0]
        y1 = datum['dets'][i][1]
        x2 = datum['dets'][i][2]
        y2 = datum['dets'][i][3]
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 1)
        cv2.putText(img, str(datum['det_scores'][i]), (x1, y2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    n_gt = len(datum['gt_classes'])
    for i in range(n_gt):
        x1 = datum['gt_boxes'][i][0]
        y1 = datum['gt_boxes'][i][1]
        x2 = datum['gt_boxes'][i][2]
        y2 = datum['gt_boxes'][i][3]
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, dataPkl['classes'][datum['gt_classes'][i]], (x1, y2), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.imshow('show', img)
    if cv2.waitKey(0) == 27:
        break
