# -*- coding: utf-8 -*-
"""Assignment.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1sLB9kH88s1P_cTHmbfnGqj6OoQ4W1Ar4

**Task: Training the DINO Object Detection Model on a Pedestrian Dataset**

I have been assigned the task of training the DINO object detection model on a pedestrian dataset consisting of around 200 images collected within the IIT Delhi campus. The images are annotated in Pascal VOC XML format. To begin, I will first plot the bounding boxes on the images to get a better understanding of the dataset.

The steps I need to follow are:

1. **Clone the DINO Repository**: I will clone the DINO repository from [this GitHub link](https://github.com/IDEA-Research/DINO) and set up the required environment and libraries as outlined in the repo.
   
2. **Download Pre-trained Model**: I will download the pre-trained DINO-4scale R50 backbone model from the link provided in the repository.
   
3. **Convert Annotations**: I will convert the annotations from Pascal VOC XML format to the format required by the DINO model.

4. **Run Evaluations**: I will run the evaluation script on the "validation" dataset, making sure to adjust the configuration file to point to the correct dataset path.

5. **Report and Analyze Results**: Once the evaluation is done, I will report the box AP (Average Precision) values, visualize the results, and analyze any errors where the model failed to detect objects.

6. **Visualize Decoder Layers**: Since DINO has six decoder layers, I will visualize the bounding boxes predicted after each decoder layer and show how the bounding boxes change as the image passes through the layers.

7. **Visualize Sampling Points**: DINO uses deformable attention to extract features for each query at specific sampling points. I will visualize these sampling points at the final decoder layer for the "best" query, which is the one responsible for the most accurate bounding box prediction.

8. **Fine-tune and Evaluate**: I will fine-tune the model on the training set and evaluate it again on the validation set, then report any differences in performance.

Run on GPU Runtime only

> Reason: MultiScaleDeformableAttention Dependencies in DINO-DETR

---

## Installation

### A.Setup Model & Data
"""

!git clone https://github.com/IDEA-Research/DINO.git

!mv -v /content/DINO/* /content/

!rm -rf /content/DINO

import torch
import torchvision

!pip install -r requirements.txt

"""### Maily builds the MultiScaleDeformableAttention module from [Deformable-DETR](https://github.com/fundamentalvision/Deformable-DETR)"""

!python models/dino/ops/setup.py build install

"""#### NOTE: Last test will fail due to smaller GPU memory on P100/T4"""

!python models/dino/ops/test.py

"""## Assignment Dataset






"""

from google.colab import drive
drive.mount('/content/drive')

!cp -r /content/drive/MyDrive/Dataset_DINO.zip /content/

!unzip /content/Dataset_DINO.zip > /dev/null

"""### B Imports Libeary"""

import time
import os
import shutil

import random
import numpy as np
import matplotlib.pyplot as plt
import cv2

try:
  import xml.etree.ElementTree as ET
except:
  print("Installing xml Element Tree...")
  !pip install xml
  import xml.etree.ElementTree as ET

"""##  Download Pretrained model (R50, 4scale) --- Uploaded from (personal) drive"""

!cp -r /content/drive/MyDrive/checkpoint_dino.pth /content/

"""### Run on COCO2017 DS for validation

* Note that COCO2017 was downloaded using the commented code cell below
"""

# import os
# import requests
# import zipfile

# # Define the URL and file paths
# dataset_url = 'http://images.cocodataset.org/zips/train2017.zip'
# annotations_url = 'http://images.cocodataset.org/annotations/annotations_trainval2017.zip'
# dataset_path = '/content/drive/MyDrive/data/COCO/train2017.zip'
# annotations_path = '/content/drive/MyDrive/data/COCO/annotations_trainval2017.zip'
# extracted_dataset_path = '/content/drive/MyDrive/data/COCO/train2017'
# extracted_annotations_path = '/content/drive/MyDrive/data/COCO/annotations'

# # Download the dataset
# print('Downloading the dataset...')
# r = requests.get(dataset_url, stream=True)
# with open(dataset_path, 'wb') as f:
#     for chunk in r.iter_content(chunk_size=1024):
#         if chunk:
#             f.write(chunk)

# # Download the annotations
# print('Downloading the annotations...')
# r = requests.get(annotations_url, stream=True)
# with open(annotations_path, 'wb') as f:
#     for chunk in r.iter_content(chunk_size=1024):
#         if chunk:
#             f.write(chunk)

# # Extract the dataset
# print('Extracting the dataset...')
# with zipfile.ZipFile(dataset_path, 'r') as zip_ref:
#     zip_ref.extractall(extracted_dataset_path)

# # Extract the annotations
# print('Extracting the annotations...')
# with zipfile.ZipFile(annotations_path, 'r') as zip_ref:
#     zip_ref.extractall(extracted_annotations_path)

# # Cleanup - remove the zip files
# os.remove(dataset_path)
# os.remove(annotations_path)

# print('Dataset downloaded and extracted successfully.')

# !bash /content/scripts/DINO_eval.sh /content/COCO2017 /content/checkpoint_dino.pth

"""> Verified checkpoint health. AP reported in paper == experimental run ~= 40

## **C Annotations**

#  C3.1 Parsing
"""

def parse_annotation(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    boxes = []
    for obj in root.iter('object'):
        xmin = int(obj.find('bndbox').find('xmin').text)
        ymin = int(obj.find('bndbox').find('ymin').text)
        xmax = int(obj.find('bndbox').find('xmax').text)
        ymax = int(obj.find('bndbox').find('ymax').text)
        boxes.append((xmin, ymin, xmax, ymax))

    return boxes

"""### C3.2 Plotting"""

def plot_bounding_boxes(image_path, boxes):
    image = cv2.imread(image_path)

    for box in boxes:
        xmin, ymin, xmax, ymax = box
        cv2.rectangle(image, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)

    return image

DATA_PATH = '/content/Dataset/'
TRAIN_PATH = DATA_PATH+"train/"
VALID_PATH = DATA_PATH+"valid/"

annotated_imgs = []
for e in os.listdir(TRAIN_PATH):
  if e.endswith(".xml"):
    _, id = e.split("_")
    id, _ = id.split(".")
    # print(e, " | ", id)
    boxes = parse_annotation(TRAIN_PATH + e)
    annotated_imgs.append(plot_bounding_boxes(TRAIN_PATH+f"Image_{id}.png", boxes))

print(annotated_imgs[0].dtype)

# 16-row, 9-column image grid --> 160 plots (almost all of the training data)
fig, axs = plt.subplots(16, 9, figsize=(32, 32))
axs = axs.flatten()

for i, ax in enumerate(axs):
    ax.imshow(annotated_imgs[i], cmap='gray')
    ax.axis('off')

plt.tight_layout()
plt.show()

"""### C3.3 Conversion to compatible format & dir structure"""

!mv /content/Dataset/train /content/Dataset/train2017
!mv /content/Dataset/valid /content/Dataset/val2017
!mkdir /content/Dataset/annotations

!rm -rf /content/Dataset/annotations/instances_train2017.json /content/Dataset/annotations/instances_val2017.json

!touch /content/Dataset/annotations/instances_train2017.json
!touch /content/Dataset/annotations/instances_val2017.json

import json

def parse_annotation_cocoStyle(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    boxes = []
    for obj in root.iter('object'):
        xmin = int(obj.find('bndbox').find('xmin').text)
        ymin = int(obj.find('bndbox').find('ymin').text)
        xmax = int(obj.find('bndbox').find('xmax').text)
        ymax = int(obj.find('bndbox').find('ymax').text)

        height = ymax - ymin
        width = xmax - xmin

        boxes.append((xmin, ymin, width, height))

    return boxes

def make_json_from_xml(path, json_file_path, base_D):

  base_dict = base_D.copy()
  images_dict = []
  bb_dict = []
  bb_dict_cnt = 0

  for i in range(len(os.listdir(path))):
    fileName = os.listdir(path)[i]
    if fileName.endswith(".png"): # only process these & don't forget to delete xml files
      images_dict.append({"file_name": str(fileName), "id": i})

      boxes = parse_annotation_cocoStyle(path+fileName[:-3]+"xml")

      for j in range(len(boxes)):
        x, y, w, h = boxes[j]
        curr_area = h * w
        bb_dict.append({"iscrowd": 0,
                        "image_id": i,
                        "bbox": [x, y, w, h],
                        "area": curr_area,
                        "category_id": 1,
                        "id":	bb_dict_cnt})
        bb_dict_cnt += 1


  base_dict["images"] = images_dict
  base_dict["annotations"] = bb_dict

  json_str = json.dumps(base_dict)
  # Write JSON to a file
  with open(json_file_path, 'w') as f:
    f.write(json_str)

  print("JSON file created as", json_file_path)

TP_2 = DATA_PATH+"train2017/"
VP_2 = DATA_PATH+"val2017/"

trData_json = {"info": {"description": "IIT Delhi Dataset"},
               "images": None,
               "annotations": None,
               "categories": [{"supercategory": "person", "id": 1, "name": "person"}]
               }

valData_json = {"info": {"description": "IIT Delhi Dataset - Val"},
               "images": None,
               "annotations": None,
               "categories": [{"supercategory": "person", "id": 1, "name": "person"}]
               }

make_json_from_xml(TP_2, '/content/Dataset/annotations/instances_train2017.json', trData_json)
make_json_from_xml(VP_2, '/content/Dataset/annotations/instances_val2017.json', valData_json)

# To verify difference between the two jsons (and to correct them)


# orig = "/content/COCO2017/annotations/instances_val2017.json"
# new = "/content/Dataset/annotations/instances_val2017.json"

# # Read JSON data from the file
# with open(orig, 'r') as f1:
#     orig_d = json.load(f1)

# with open(new, 'r') as f2:
#     new_d = json.load(f2)

# print(orig_d['images'][4])
# print(f"---------")
# print(new_d['images'][4])

"""## C4 Evaluation on Validation Set    """

!bash /content/scripts/DINO_eval.sh /content/Dataset /content/checkpoint_dino.pth

"""## C5 Visualizations of C4 (and Observations)  

Code referenced from official repository's Assignment
"""

!python main.py --save_results --output_dir logs/DINO/R50-MS4-B -c config/DINO/DINO_4scale.py --coco_path /content/Dataset --eval --resume /content/checkpoint_dino.pth --options dn_scalar=100 embed_init_tgt=TRUE dn_label_coef=1.0 dn_bbox_coef=1.0 use_ema=False dn_box_noise_scale=1.0

t5 = torch.load('t5_gt_preds.pth')
# t5[image_id] -> will give you everything
print(t5)

json_train = "/content/Dataset/annotations/instances_train2017.json"
json_val = "/content/Dataset/annotations/instances_val2017.json"

# Map json to dataset imgs and draw bbs around themwith open('data.json') as json_file:

# Open the JSON file
with open(json_val) as json_file:
    # Load the JSON data
    data = json.load(json_file)

from util.slconfig import SLConfig
from datasets import build_dataset
from util.visualizer import COCOVisualizer
from util import box_ops

model_config_path = "config/DINO/DINO_4scale.py"
args = SLConfig.fromfile(model_config_path)

args.device = 'cuda'
args.dataset_file = 'coco'
args.coco_path = "/content/Dataset" # the path of coco
args.fix_size = False

dataset_val = build_dataset(image_set='val', args=args)
vslzr = COCOVisualizer()
vslzr_2 = COCOVisualizer()

for i, batch in enumerate(dataset_val):
  img, targets = batch
  # print(i, img.shape, batch)
  box_label = ['person' for item in targets['labels']]
  gt_dict = {
    'boxes': targets['boxes'],
    'image_id': targets['image_id'],
    'size': targets['size'],
    'box_label': box_label,
  }
  # print(gt_dict)
  vslzr.visualize(img, gt_dict, caption=f"orig_{str(i).zfill(4)}", savedir="/content/figs/original")

  img_id = int(targets['image_id'].detach().cpu().numpy())

  box_label_pred = ['person' for ite in t5[img_id]['pred_boxes']]
  H, W = [480,600] # norm with original image size
  pred_dict = {
      'boxes': t5[img_id]['pred_boxes'].cpu() / torch.Tensor([W, H, W, H]),
      'image_id': targets['image_id'].cpu(),
      'size': t5[img_id]['size'].cpu(),
      'box_label': box_label_pred,
  }
  vslzr_2.visualize(img, pred_dict, caption=f"pred_{str(i).zfill(4)}", savedir="/content/figs/pred")

"""## C6 Decoder layerwise-visualizations

Ran after making changes to:
> models/dino/deformable_transformer.py
"""

!python main.py --save_results --output_dir logs/DINO/R50-MS4-B -c config/DINO/DINO_4scale.py --coco_path /content/Dataset --eval --resume /content/checkpoint_dino.pth --options dn_scalar=100 embed_init_tgt=TRUE dn_label_coef=1.0 dn_bbox_coef=1.0 use_ema=False dn_box_noise_scale=1.0

# So, this output is for the img with id: 58
itm_layers = np.load("/content/itm_layers.npy")
itm_ref = np.load("/content/itm_refpoints_dec.npy")
top_k_proposals = np.load("/content/top_k_proposals.npy")

print(itm_layers.shape, itm_ref.shape, top_k_proposals)

post_lx_boxes = {}
for i in range(1,7):
  post_lx_boxes[i] = itm_ref[i][0]

print(post_lx_boxes[3] == post_lx_boxes[6])

for i, batch in enumerate(dataset_val):
  img, targets = batch
  box_label = ['person' for item in targets['labels']]
  img_id = int(targets['image_id'].detach().cpu().numpy())
  gt_dict = {
    'boxes': targets['boxes'],
    'image_id': img_id,
    'size': targets['size'],
    'box_label': box_label,
  }
  if int(img_id) == 58:
    vslzr.visualize(img, gt_dict, caption=f"orig_{str(i).zfill(4)}", savedir="/content/figs/layers_viz")

    for j in range(1,7): # j == layer number
      topk_proposals = (torch.topk(torch.tensor(itm_layers[j-1][0]).max(-1)[0], j, dim=0)[1]).cpu().numpy()
      print(f"topk proposals from layer outs: {topk_proposals}")
      boxes = [post_lx_boxes[j][e] for e in topk_proposals]
      post_box_label = ['person' for item in boxes]
      layer_dict = {
          'boxes': torch.tensor(boxes),
          'image_id': img_id,
          'size': targets['size'],
          'box_label': post_box_label,
      }
      vslzr.visualize(img, layer_dict, caption=f"id_{img_id}_layer_{str(j)}", savedir="/content/figs/layers_viz")

"""## C7 Visualization of sampling points for best query at last layer    

> modified: deformable_transformer.py again
"""

!python main.py --save_results --output_dir logs/DINO/R50-MS4-B -c config/DINO/DINO_4scale.py --coco_path /content/Dataset --eval --resume /content/checkpoint_dino.pth --options dn_scalar=100 embed_init_tgt=TRUE dn_label_coef=1.0 dn_bbox_coef=1.0 use_ema=False dn_box_noise_scale=1.0

# One of the bb from the best query: topk: [257 135 250 745 708 358]
post_lx_boxes[5][257]

best_pts = np.load("/content/best_sampling_pts_4.npy")

sH, sW = 600, 480

from google.colab.patches import cv2_imshow
img = cv2.imread('/content/Dataset/val2017/Image_00014.png')

for i in range(len(best_pts)):
  x, y = int(sH * best_pts[i][0][0]), int(sW * best_pts[i][0][1])
  # print(x, y)
  img = cv2.circle(img, (x,y), radius=1, color=(0, 255, 0), thickness=-1)

print("Sampling points from the best query (last layer) for image with id: 58 (Image_0014.png)")
cv2_imshow(img)

"""## C8 Fine-tuning on the training set (pre-trained: R50-12epochs -> fine-tuned: 5 epochs)

> Modified: config.DINO.DINO_4scale.py
* num_classes *to 2 from 91*
* dn_labelbook_size to ensure dn_labelbook_size >= num_classes + 1 *(to 2 from 91)*    


---    

Added two flags:
* --pretrain_model_path (same ckpt as before)
* --finetune_ignore label_enc.weight class_embed

---


Train - Val steps:

> logs saved at: logs/DINO/fine_tune_R50-MS4
"""

!python main.py --finetune_ignore label_enc.weight class_embed --pretrain_model_path /content/checkpoint_dino.pth --output_dir logs/DINO/fine_tune_R50-MS4 -c config/DINO/DINO_4scale.py --coco_path /content/Dataset --options dn_scalar=100 embed_init_tgt=TRUE dn_label_coef=1.0 dn_bbox_coef=1.0 use_ema=False dn_box_noise_scale=1.0

"""### Perceptual Validation that AP improved!"""

!python main.py --save_results --output_dir logs/DINO/eval_finetune_R50-MS4-x -c config/DINO/DINO_4scale.py --coco_path /content/Dataset --eval --resume /content/logs/DINO/fine_tune_R50-MS4/checkpoint_best_regular.pth --options dn_scalar=100 embed_init_tgt=TRUE dn_label_coef=1.0 dn_bbox_coef=1.0 use_ema=False dn_box_noise_scale=1.0

t5 = torch.load('fineTune_gt_preds.pth')
print(t5)

# Map json to dataset imgs and draw bbs around themwith open('data.json') as json_file:
# Open the JSON file
with open(json_val) as json_file:
    # Load the JSON data
    data = json.load(json_file)

model_config_path = "config/DINO/DINO_4scale.py"
args = SLConfig.fromfile(model_config_path)

args.device = 'cuda'
args.dataset_file = 'coco'
args.coco_path = "/content/Dataset" # the path of coco
args.fix_size = False

dataset_val = build_dataset(image_set='val', args=args)
vslzr = COCOVisualizer()
vslzr_2 = COCOVisualizer()

for i, batch in enumerate(dataset_val):
  img, targets = batch
  # print(i, img.shape, batch)
  box_label = ['person' for item in targets['labels']]
  gt_dict = {
    'boxes': targets['boxes'],
    'image_id': targets['image_id'],
    'size': targets['size'],
    'box_label': box_label,
  }
  # print(gt_dict)
  vslzr.visualize(img, gt_dict, caption=f"orig_{str(i).zfill(4)}", savedir="/content/figs/original")

  img_id = int(targets['image_id'].detach().cpu().numpy())

  box_label_pred = ['person' for ite in t5[img_id]['pred_boxes']]
  H, W = [480,600] # norm with original image size
  pred_dict = {
      'boxes': t5[img_id]['pred_boxes'].cpu() / torch.Tensor([W, H, W, H]),
      'image_id': targets['image_id'].cpu(),
      'size': t5[img_id]['size'].cpu(),
      'box_label': box_label_pred,
  }
  vslzr_2.visualize(img, pred_dict, caption=f"pred_{str(i).zfill(4)}", savedir="/content/figs/fine_tune_preds")

"""---     

---    
"""

!zip -r /content/DINO_aryan.zip /content/*

