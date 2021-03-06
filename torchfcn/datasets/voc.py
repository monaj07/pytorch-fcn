#!/usr/bin/env python

import collections
import os.path as osp

import numpy as np
import PIL.Image
import scipy.io
import torch
from torch.utils import data
import cv2
import os


class SiftFlowData(data.Dataset):

    class_names = np.array([
        'awning',
        'balcony',
        'bird',
        'boat',
        'bridge',
        'building',
        'bus',
        'car',
        'cow',
        'crosswalk',
        'desert',
        'door',
        'fence',
        'field',
        'grass',
        'moon',
        'mountain',
        'person',
        'plant',
        'pole',
        'river',
        'road',
        'rock',
        'sand',
        'sea',
        'sidewalk',
        'sign',
        'sky',
        'staircase',
        'streetlight',
        'sun',
        'tree',
        'window'
    ])
    mean_bgr = np.array([104.00698793, 116.66876762, 122.67891434])

    def __init__(self, root, split='train', transform=False):
        self.root = root
        self.split = split
        self._transform = transform

        # VOC2011 and others are subset of VOC2012
        dataset_dir = self.root + '/SiftFlowDataset'
        file_list = []
        for filename in os.listdir(dataset_dir + '/Images'):
            file_list.append(filename[:-4])
        val_file_list = []
        for filename in open(dataset_dir + '/TestSet1.txt', 'r'):
            val_file_list.append(filename.strip()[51:-4])
        train_file_list = list(set(file_list) - set(val_file_list))
        file_list_dict = {'train':train_file_list, 'val':val_file_list}
        self.files = collections.defaultdict(list)
        for split in ['train', 'val']:
            for file in file_list_dict[split]:
                img_file = osp.join(dataset_dir, 'Images/%s.jpg' % file)
                lbl_file = osp.join(dataset_dir, 'SemanticLabels/%s.mat' % file)
                self.files[split].append({
                    'img': img_file,
                    'lbl': lbl_file,
                })

    def __len__(self):
        return len(self.files[self.split])

    def __getitem__(self, index):
        data_file = self.files[self.split][index]
        # load image
        img_file = data_file['img']
        img = PIL.Image.open(img_file)
        img = np.array(img, dtype=np.uint8)
        # load label
        lbl_file = data_file['lbl']
        mat = scipy.io.loadmat(lbl_file)
        lbl = mat['S'].astype(np.int32)
        lbl = lbl - 1
        sparse_tags = np.unique(lbl)
        sparse_tags = sparse_tags[sparse_tags >= 0]
        tags = np.zeros(33)
        tags[sparse_tags] = 1
        if self._transform:
            return self.transform(img, lbl, tags)
        else:
            return img, lbl, tags

    def transform(self, img, lbl, tags):
        img = img[:, :, ::-1]  # RGB -> BGR
        img = img.astype(np.float64)
        img -= self.mean_bgr
        img = img.transpose(2, 0, 1)
        img = torch.from_numpy(img).float()
        lbl = torch.from_numpy(lbl).long()
        tags = torch.from_numpy(tags).float()
        return img, lbl, tags

    def untransform(self, img, lbl):
        img = img.numpy()
        img = img.transpose(1, 2, 0)
        img += self.mean_bgr
        img = img.astype(np.uint8)
        img = img[:, :, ::-1]
        lbl = lbl.numpy()
        return img, lbl

class VOCClassSegBase(data.Dataset):

    class_names = np.array([
        'background',
        'aeroplane',
        'bicycle',
        'bird',
        'boat',
        'bottle',
        'bus',
        'car',
        'cat',
        'chair',
        'cow',
        'diningtable',
        'dog',
        'horse',
        'motorbike',
        'person',
        'potted plant',
        'sheep',
        'sofa',
        'train',
        'tv/monitor',
    ])
    mean_bgr = np.array([104.00698793, 116.66876762, 122.67891434])

    def __init__(self, root, split='train', transform=False):
        self.root = root
        self.split = split
        self._transform = transform

        # VOC2011 and others are subset of VOC2012
        dataset_dir = self.root + '/VOCdevkit/VOC2012'
        self.files = collections.defaultdict(list)
        for split in ['train', 'val']:
            imgsets_file = dataset_dir + '/ImageSets/Segmentation/%s.txt' % split
            for did in open(imgsets_file):
                did = did.strip()
                img_file = osp.join(dataset_dir, 'JPEGImages/%s.jpg' % did)
                lbl_file = osp.join(
                    dataset_dir, 'SegmentationClass/%s.png' % did)
                self.files[split].append({
                    'img': img_file,
                    'lbl': lbl_file,
                })

    def __len__(self):
        return len(self.files[self.split])

    def __getitem__(self, index):
        data_file = self.files[self.split][index]
        # load image
        img_file = data_file['img']
        img = PIL.Image.open(img_file)
        img = np.array(img, dtype=np.uint8)
        # load label
        lbl_file = data_file['lbl']
        lbl = PIL.Image.open(lbl_file)
        lbl = np.array(lbl, dtype=np.int32)
        lbl[lbl == 255] = -1
        sparse_tags = np.unique(lbl)
        sparse_tags = sparse_tags[sparse_tags > 0]
        tags = np.zeros(20)
        tags[sparse_tags-1] = 1
        if self._transform:
            return self.transform(img, lbl, tags)
        else:
            return img, lbl, tags

    def transform(self, img, lbl, tags):
        img = img[:, :, ::-1]  # RGB -> BGR
        img = img.astype(np.float64)
        #img = cv2.resize(img, (321, 321), interpolation=cv2.INTER_CUBIC)
        #lbl = cv2.resize(lbl, (321, 321), interpolation=cv2.INTER_NEAREST)
        img -= self.mean_bgr
        img = img.transpose(2, 0, 1)
        img = torch.from_numpy(img).float()
        lbl = torch.from_numpy(lbl).long()
        tags = torch.from_numpy(tags).float()
        return img, lbl, tags

    def untransform(self, img, lbl):
        img = img.numpy()
        img = img.transpose(1, 2, 0)
        img += self.mean_bgr
        img = img.astype(np.uint8)
        img = img[:, :, ::-1]
        lbl = lbl.numpy()
        return img, lbl


class VOC2011ClassSeg(VOCClassSegBase):

    def __init__(self, root, split='train', transform=False):
        super(VOC2011ClassSeg, self).__init__(
            root, split=split, transform=transform)
        pkg_root = osp.join(osp.dirname(osp.realpath(__file__)), '..')
        imgsets_file = osp.join(
            pkg_root, 'ext/fcn.berkeleyvision.org',
            'data/pascal/seg11valid.txt')
        dataset_dir = osp.join(self.root, 'VOCdevkit/VOC2012')
        for did in open(imgsets_file):
            did = did.strip()
            img_file = osp.join(dataset_dir, 'JPEGImages/%s.jpg' % did)
            lbl_file = osp.join(dataset_dir, 'SegmentationClass/%s.png' % did)
            self.files['seg11valid'].append({'img': img_file, 'lbl': lbl_file})


class VOC2012ClassSeg(VOCClassSegBase):

    url = 'http://host.robots.ox.ac.uk/pascal/VOC/voc2012/VOCtrainval_11-May-2012.tar'  # NOQA

    def __init__(self, root, split='train', transform=False):
        super(VOC2012ClassSeg, self).__init__(
            root, split=split, transform=transform)


class SBDClassSeg(VOCClassSegBase):

    # XXX: It must be renamed to benchmark.tar to be extracted.
    url = 'http://www.eecs.berkeley.edu/Research/Projects/CS/vision/grouping/semantic_contours/benchmark.tgz'  # NOQA

    def __init__(self, root, split='train', transform=False):
        self.root = root
        self.split = split
        self._transform = transform

        dataset_dir = self.root + '/VOCdevkit/VOC2012/benchmark_RELEASE/dataset'
        self.files = collections.defaultdict(list)
        for split in ['train', 'val']:
            imgsets_file = osp.join(dataset_dir, '%s.txt' % split)
            for did in open(imgsets_file):
                did = did.strip()
                img_file = osp.join(dataset_dir, 'img/%s.jpg' % did)
                lbl_file = osp.join(dataset_dir, 'cls/%s.mat' % did)
                self.files[split].append({
                    'img': img_file,
                    'lbl': lbl_file,
                })

    def __getitem__(self, index):
        data_file = self.files[self.split][index]
        # load image
        img_file = data_file['img']
        img = PIL.Image.open(img_file)
        img = np.array(img, dtype=np.uint8)
        # load label
        lbl_file = data_file['lbl']
        mat = scipy.io.loadmat(lbl_file)
        lbl = mat['GTcls'][0]['Segmentation'][0].astype(np.int32)
        lbl[lbl == 255] = -1
        sparse_tags = np.unique(lbl)
        sparse_tags = sparse_tags[sparse_tags > 0]
        tags = np.zeros(20)
        tags[sparse_tags-1] = 1
        if self._transform:
            return self.transform(img, lbl, tags)
        else:
            return img, lbl, tags


class CamVid(data.Dataset):

    class_names = np.array([
        'Sky',
        'Building',
        'Pole',
        'Road',
        'Pavement',
        'Tree',
        'SignSymbol',
        'Fence',
        'Car',
        'Pedestrian',
        'Bicyclist',
    ])
    mean_bgr = np.array([105.00698793, 113.66876762, 116.67891434]) #Mean image for places (It should be replaced by places+imagenet)

    def __init__(self, root, split='train', transform=False):
        self.root = root
        self.split = split
        self._transform = transform

        dataset_dir = self.root + '/SegNet/CamVid/'
        self.files = collections.defaultdict(list)
        for split in ['train', 'val', 'test']:
            imgsets_file = dataset_dir + '%s.txt' % split
            for did in open(imgsets_file):
                did = did.split()
                img_file = self.root + did[0]
                lbl_file = self.root + did[1]
                self.files[split].append({
                    'img': img_file,
                    'lbl': lbl_file,
                })

    def __len__(self):
        return len(self.files[self.split])

    def __getitem__(self, index):
        data_file = self.files[self.split][index]
        # load image
        img_file = data_file['img']
        img = PIL.Image.open(img_file)
        img = np.array(img, dtype=np.uint8)
        # load label
        lbl_file = data_file['lbl']
        lbl = PIL.Image.open(lbl_file)
        lbl = np.array(lbl, dtype=np.int32)
        lbl[lbl == 11] = -1
        sparse_tags = np.unique(lbl)
        sparse_tags = sparse_tags[sparse_tags >= 0]
        tags = np.zeros(11)
        tags[sparse_tags] = 1
        if self._transform:
            return self.transform(img, lbl, tags)
        else:
            return img, lbl, tags

    def transform(self, img, lbl, tags):
        img = img[:, :, ::-1]  # RGB -> BGR
        img = img.astype(np.float64)
        #img = cv2.resize(img, (321, 321), interpolation=cv2.INTER_CUBIC)
        #lbl = cv2.resize(lbl, (321, 321), interpolation=cv2.INTER_NEAREST)
        img -= self.mean_bgr
        img = img.transpose(2, 0, 1)
        img = torch.from_numpy(img).float()
        lbl = torch.from_numpy(lbl).long()
        tags = torch.from_numpy(tags).float()
        return img, lbl, tags

    def untransform(self, img, lbl):
        img = img.numpy()
        img = img.transpose(1, 2, 0)
        img += self.mean_bgr
        img = img.astype(np.uint8)
        img = img[:, :, ::-1]
        lbl = lbl.numpy()
        return img, lbl

