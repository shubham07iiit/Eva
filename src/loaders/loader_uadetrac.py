"""
This file implements the dataset loading methods for UA-detrac
If any problem occurs, please email jaeho.bang@gmail.com
@Jaeho Bang
"""

import argparse
import os
import warnings
import xml.etree.ElementTree as ET
import random2 as random    # INSTALL RAMDOM2
import cv2
import numpy as np
import sys
import time
import pandas as pd
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath('../src'))))
from src.loaders.TaskManager import TaskManager
from src.loaders.abstract_loader import AbstractLoader


# Make this return a dictionary of label to data for the whole dataset

class UADetracLoader(AbstractLoader):
    def __init__(self, args, image_width=300, image_height=300):
        self.args = args
        self.data_dict = {}
        self.label_dict = {}
        self.vehicle_type_filters = ['car', 'van', 'bus', 'others']
        self.cloud_type_filters = ['Fish','Flower','Gravel','Sugar']
        self.speed_filters = [40, 50, 60, 65, 70]
        self.intersection_filters = ["pt335", "pt342", "pt211", "pt208"]
        self.color_filters = ['white', 'black', 'silver', 'red']
        original image height = 540
        original image width = 960

        self.image_width = image_width
        self.image_height = image_height
        self.image_channels = 3
        self.task_manager = TaskManager()
        self.images = None
        self.labels = None
        self.boxes = None
        self.eva_dir = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        self.video_start_indices = []

    def load_video(self, dir: str):
        """
        This function is not needed for ua_detrac
        Should never be called
        :return: None
        """
        return None

    def load_boxes(self, dir: str = None):
        if args.data_type=='i':
            boxes = loader.load_boxes_for_images()

        elif args.data_type=='v':
            boxes = loader.load_boxes_for_videos()

    def load_labels(self, dir: str = None):
        if args.data_type=='i':
            labels = loader.load_labels_for_images()

        elif args.data_type=='v':
            labels = loader.load_labels_for_videos()

    def load_boxes_for_images(self, dir: str = None):
        """
        Loads boxes from annotation
        Should be same shape as self.labels
        :return: boxes
        """
        if dir is None:
            dir = os.path.join(self.eva_dir, 'data', 'cloud_dataset/train', self.args.anno_path)
        info = self.image_info[image_id]
                
        mask = np.zeros((IMAGE_SIZE, IMAGE_SIZE, len(info['annotations'])), dtype=np.uint8)
        labels = []
        
        for m, (annotation, label) in enumerate(zip(info['annotations'], info['labels'])):
            sub_mask = np.full(info['height']*info['width'], 0, dtype=np.uint8)
            annotation = [int(x) for x in annotation.split(' ')]
            
            for i, start_pixel in enumerate(annotation[::2]):
                sub_mask[start_pixel: start_pixel+annotation[2*i+1]] = 1

            sub_mask = sub_mask.reshape((info['height'], info['width']), order='F')
            sub_mask = cv2.resize(sub_mask, (IMAGE_SIZE, IMAGE_SIZE), interpolation=cv2.INTER_NEAREST)
            
            mask[:, :, m] = sub_mask
            labels.append(int(label)+1)
        self.boxes = mask
        return self.boxes

    def load_boxes_for_videos(self, dir: str = None):
        """
        Loads boxes from annotation
        Should be same shape as self.labels
        :return: boxes
        """
        if dir is None:
            dir = os.path.join(self.eva_dir, 'data', 'ua_detrac',
                               self.args.anno_path)
        self.boxes = np.array(self.get_boxes_for_videos(dir))
        return self.boxes

    def load_images(self, image_dir: str = None, image_size=None):
        """
        This function simply loads image of given image
        :return: image_array (numpy)
        """
        if image_size is not None:
            self.image_height = image_size
            self.image_width = image_size
        
        if image_dir is None:
            if self.args.data_type == 'i':
                image_dir = os.path.join(self.eva_dir, 'data', 'cloud_dataset/data', self.args.image_path)
            elif self.args.data_type == 'v':
                image_dir = os.path.join(self.eva_dir, 'data', 'ua_detrac',
-                                     self.args.image_path)
        
        file_names = []
        for root, subdirs, files in os.walk(image_dir):
            files.sort()
            if self.args.data_type == 'v':
                self.video_start_indices.append(len(file_names))
            for file in files:
                file_names.append(os.path.join(root, file))

        print("Number of files added: ", len(file_names))
        self.images = np.ndarray(shape=(
            len(file_names), self.image_height, self.image_width,
            self.image_channels),
            dtype=np.uint8)
        for i in range(len(file_names)):
            file_name = file_names[i]
            img = cv2.imread(file_name)
            img = cv2.resize(img, (self.image_width, self.image_height))
            self.images[i] = img
        return self.images

    def load_labels_for_images(self, dir: str = None):
        """
        Loads cloud type, fish, flower, gravel and sugar of cloud dataset
        :return: labels
        """
        if dir is None:
            dir = os.path.join(self.eva_dir, 'data', 'cloud_dataset/train',
                               self.args.anno_path)
        category_list = self.filters

        train_dict = {}
        train_class_dict = {}
        train_df = pd.read_csv(dir+"/train.csv")
        train_df = train_df.dropna()
        for idx, row in train_df.iterrows():
            image_filename = row.Image_Label.split("_")[0]
            class_name = row.Image_Label.split("_")[1]
            class_id = category_list.index(class_name)
            if train_dict.get(image_filename):
                train_dict[image_filename].append(row.EncodedPixels)
                train_class_dict[image_filename].append(class_id)
            else:
                train_dict[image_filename] = [row.EncodedPixels]
                train_class_dict[image_filename] = [class_id]
        
        df = pd.DataFrame(columns=["image_id","EncodedPixels","CategoryId","Width","Height"])
        for key, value in train_dict.items():
            img = Image.open(dir+"/train_images/{}".format(key))
            width, height = img.width, img.height
            df = df.append({"image_id": key, "EncodedPixels": value, "CategoryId": train_class_dict[key], "Width": width, "Height": height},ignore_index=True)
            self.labels = {'classes': df} #returning dataframes
            return self.labels
        else:
            return None

    def load_labels_for_videos(self, dir: str = None):
        """
        Loads vehicle type, speed, color, and intersection of ua-detrac
        vehicle type, speed is given by the dataset
        color, intersection is derived from functions built-in
        :return: labels
        """
        if dir is None:
            dir = os.path.join(self.eva_dir, 'data', 'ua_detrac',
                               self.args.anno_path)
        results = self._load_XML(dir)
        if results is not None:
            vehicle_type_labels, speed_labels, color_labels, \
                intersection_labels = results
            self.labels = {'vehicle': vehicle_type_labels,
                           'speed': speed_labels,
                           'color': color_labels,
                           'intersection': intersection_labels}

            return self.labels
        else:
            return None

    def get_video_start_indices(self):
        """
        This function returns the starting indexes for each video bc
        uadetrac has numerous videos of different perspectives
        :return: python list with starting indexes saved
        """
        return self.video_start_indices

    def save_images(self):
        # we need to save the image / video start indexes
        # convert list to np.array
        save_dir = os.path.join(self.eva_dir, 'data', self.args.cache_path,
                                self.args.cache_image_name)
        save_dir_vi = os.path.join(self.eva_dir, 'data', self.args.cache_path,
                                   self.args.cache_vi_name)
        if self.images is None:
            warnings.warn("No image loaded, call load_images() first", Warning)
        elif type(self.images) is np.ndarray:
            np.save(save_dir, self.images)
            np.save(save_dir_vi, np.array(self.video_start_indices))
            print("saved images to", save_dir)
            print("saved video indices to", save_dir_vi)
        else:
            warnings.warn("Image array type is not np.....cannot save",
                          Warning)

    def save_labels(self):
        save_dir = os.path.join(self.eva_dir, 'data', self.args.cache_path,
                                self.args.cache_label_name)
        if self.labels is None:
            warnings.warn("No labels loaded, call load_labels() first",
                          Warning)
        elif type(self.labels) is dict:
            np.save(save_dir, self.labels, allow_pickle=True)
            print("saved labels to", save_dir)
        else:
            warnings.warn("Labels type is not dict....cannot save", Warning)
            print("labels type is ", type(self.labels))

    def save_boxes(self):
        save_dir = os.path.join(self.eva_dir, 'data', self.args.cache_path,
                                self.args.cache_box_name)
        if self.images is None:
            warnings.warn("No labels loaded, call load_boxes() first", Warning)
        elif type(self.images) is np.ndarray:
            np.save(save_dir, self.boxes)
            print("saved boxes to", save_dir)
        else:
            warnings.warn("Labels type is not np....cannot save", Warning)

    def load_cached_images(self):
        save_dir = os.path.join(self.eva_dir, 'data', self.args.cache_path,
                                self.args.cache_image_name)
        save_dir_vi = os.path.join(self.eva_dir, 'data', self.args.cache_path,
                                   self.args.cache_vi_name)
        self.images = np.load(save_dir)
        self.video_start_indices = np.load(save_dir_vi)
        return self.images

    def load_cached_boxes(self):
        save_dir = os.path.join(self.eva_dir, 'data', self.args.cache_path,
                                self.args.cache_box_name)
        self.boxes = np.load(save_dir, allow_pickle=True)
        return self.boxes

    def load_cached_labels(self):
        save_dir = os.path.join(self.eva_dir, 'data', self.args.cache_path,
                                self.args.cache_label_name)
        labels_pickeled = np.load(save_dir, allow_pickle=True)
        self.labels = labels_pickeled.item()
        return self.labels


    def get_boxes_for_videos(self, anno_dir):
        width = self.image_width
        height = self.image_height
        import xml.etree.ElementTree as ET
        original_height = 540
        original_width = 960
        anno_files = os.listdir(anno_dir)
        anno_files.sort()
        boxes_dataset = []
        cumu_count = 0

        for anno_file in anno_files:
            if ".xml" not in anno_file:
                print("skipping", anno_file)
                continue
            file_path = os.path.join(anno_dir, anno_file)

            tree = ET.parse(file_path)
            tree_root = tree.getroot()

            for frame in tree_root.iter('frame'):
                boxes_frame = []
                curr_frame_num = int(frame.attrib['num'])
                if len(boxes_dataset) < cumu_count + curr_frame_num - 1:
                    boxes_dataset.extend([None] * (
                        cumu_count + curr_frame_num - len(boxes_dataset)))
                for box in frame.iter('box'):
                    top, left, bottom, right = self.get_corners(box,
                                                                width /
                                                                original_width,
                                                                height /
                                                                original_height
                                                                )
                    boxes_frame.append((top, left, bottom, right))

                boxes_dataset.append(boxes_frame)

        return boxes_dataset

    
    def get_boxes_for_images(self, anno_dir):
        width = self.image_width
        height = self.image_height
        category_list = self.filters
        boxes_dataset = []
        # for i, name in enumerate(category_list):
        #   self.add_class("cloud", i+1, name)
        df = pd.DataFrame(columns=["image_id","EncodedPixels","CategoryId","Width","Height"])
        train_dataset = CloudDataset(df[:training_set_size])
        for i, row in df.iterrows():
            self.add_image("cloud", 
                           image_id=row.name, 
                           path='../understanding_cloud_organization/train_images/'+str(row.image_id), 
                           labels=row['CategoryId'],
                           annotations=row['EncodedPixels'], 
                           height=row['Height'], width=row['Width'])
        for i in range(50):
            image_id = random.choice(train_dataset.image_ids)
            # print(train_dataset.image_reference(image_id))
            
            # image = resize_image(self.image_info[image_id]['path'])
            info = self.image_info[image_id]
                
            mask = np.zeros((IMAGE_SIZE, IMAGE_SIZE, len(info['annotations'])), dtype=np.uint8)
            # labels = []
            
            for m, (annotation, label) in enumerate(zip(info['annotations'], info['labels'])):
                sub_mask = np.full(info['height']*info['width'], 0, dtype=np.uint8)
                annotation = [int(x) for x in annotation.split(' ')]
                
                for i, start_pixel in enumerate(annotation[::2]):
                    sub_mask[start_pixel: start_pixel+annotation[2*i+1]] = 1

                sub_mask = sub_mask.reshape((info['height'], info['width']), order='F')
                sub_mask = cv2.resize(sub_mask, (IMAGE_SIZE, IMAGE_SIZE), interpolation=cv2.INTER_NEAREST)
                
                mask[:, :, m] = sub_mask
                # labels.append(int(label)+1)
                print(mask)
                boxes_frame.append(mask)

            boxes_dataset.append(boxes_frame)
                
            # return mask, np.array(labels)

            # convert mask to bounding box

        # return mask, np.array(labels)
        return boxes_dataset

    def get_corners(self, box, width_scale, height_scale):
        left = int(
            float(box.attrib['left']) * width_scale)
        top = int(
            float(box.attrib['top']) * height_scale)
        right = int((float(box.attrib['left']) + float(
            box.attrib['width'])) * width_scale)
        bottom = int((float(box.attrib['top']) + float(
            box.attrib['height'])) * height_scale)
        return top, left, bottom, right

    def _convert_speed(self, original_speed):
        """
        TODO: Need to actually not use this function, because we need to
        find out what the original speed values mean
        TODO: However, in the meantime, we will use this extrapolation....
        :param original_speed:
        :return: converted_speed
        """
        speed_range = [0.0, 20.0]
        converted_range = [0.0, 100.0]

        return original_speed * 5

    def parse_frame_att(self, frame):
        car_per_frame = []
        speed_per_frame = []
        color_per_frame = []
        intersection_per_frame = []

        for att in frame.iter('attribute'):
            if att.attrib['vehicle_type']:
                car_per_frame.append(att.attrib['vehicle_type'])
            if att.attrib['speed']:
                speed_per_frame.append(self._convert_speed(
                    float(att.attrib['speed'])))
            if 'color' in att.attrib.keys():
                color_per_frame.append(att.attrib['color'])
        return car_per_frame, speed_per_frame, color_per_frame, \
            intersection_per_frame

    def populate_label(self, per_frame, labels):
        if len(per_frame) == 0:
            labels.append(None)
        else:
            labels.append(per_frame)

    def _load_XML(self, directory):
        """
        UPDATE: vehicle colors can now be extracted through the xml files!!!
        We will toss the color generator
        :param directory:
        :return:
        """
        if self.images is None:
            warnings.warn("Must load image before loading labels...returning",
                          Warning)
            return None

        car_labels = []
        speed_labels = []
        color_labels = []
        intersection_labels = []

        print("walking", directory, "for xml parsing")
        for root, subdirs, files in os.walk(directory):
            files.sort()
            for file in files:
                file_path = os.path.join(root, file)
                if ".swp" in file_path:
                    continue
                tree = ET.parse(file_path)
                tree_root = tree.getroot()
                start_frame_num = 1
                start_frame = True
                for frame in tree_root.iter('frame'):
                    curr_frame_num = int(frame.attrib['num'])
                    if start_frame and curr_frame_num != start_frame_num:
                        car_labels.append(
                            [None] * (curr_frame_num - start_frame_num))
                        speed_labels.append(
                            [None] * (curr_frame_num - start_frame_num))

                    car_per_frame, speed_per_frame, color_per_frame, \
                        intersection_per_frame = self.parse_frame_att(frame)

                    assert (len(car_per_frame) == len(speed_per_frame))

                    self.populate_label(car_per_frame, car_labels)
                    self.populate_label(speed_per_frame, speed_labels)
                    self.populate_label(color_per_frame, color_labels)
                    self.populate_label(intersection_per_frame,
                                        intersection_labels)

                    start_frame = False

        return [car_labels, speed_labels, color_labels, intersection_labels]


def get_parser():
    parser = argparse.ArgumentParser(description='Define arguments for loader')
    
    parser.add_argument('--data_type', default='i' ,
                        help='i and v for image and video dataset respectively')
    parser.add_argument('--path', default='small-data',
                        help='Define data folder within eva/data/cloud_dataset')

    parser.add_argument('--image_path', default='small-data',
                        help='Define data folder within eva/data/uadetrac')

    parser.add_argument('--anno_path', default='small-annotations',
                        help='Define annotation folder within '
                             'eva/data/uadetrac')
    parser.add_argument('--cache_path', default='npy_files',
                        help='Define save folder for images, annotations, '
                             'boxes')
    parser.add_argument('--cache_image_name', default='ua_detrac_images.npy',
                        help='Define filename for saving and loading cached '
                             'images')
    parser.add_argument('--cache_label_name', default='ua_detrac_labels.npy',
                        help='Define filename for saving and loading cached '
                             'labels')
    parser.add_argument('--cache_box_name', default='ua_detrac_boxes.npy',
                        help='Define filename for saving and loading cached '
                             'boxes')
    parser.add_argument('--cache_vi_name', default='ua_detrac_vi.npy',
                        help='Define filename for saving and loading cached '
                             'video indices')
    return parser


def load_images():
    if args.data_type=='i':
        images = loader.load_images()

    elif args.data_type=='v':
        images = loader.load_video()


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()

    import time
    
    if args.data_type=='i':
        args.image_path=args.path
    elif args.data_type=='v':
        args.video_path=args.path
    st = time.time()
    loader = UADetracLoader(args)
    images = loader.load_images()
    labels = loader.load_labels()
    boxes = loader.load_boxes()
    

    print("Time taken to load everything from disk ", time.time() - st,
          " seconds")
    loader.save_boxes()
    loader.save_labels()
    loader.save_images()

    st = time.time()
    images_cached = loader.load_cached_images()
    labels_cached = loader.load_cached_labels()
    boxes_cached = loader.load_cached_boxes()
    print("Time taken to load everything from npy", time.time() - st,
          "seconds")

    assert (images.shape == images_cached.shape)
    assert (boxes.shape == boxes_cached.shape)

    for key, value in labels.items():
        assert (labels[key] == labels_cached[key])
    assert (labels.keys() == labels_cached.keys())