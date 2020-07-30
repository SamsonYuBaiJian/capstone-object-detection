import paho.mqtt.client as paho
import time
from threading import Thread
import sys
from PIL import Image
import numpy as np
import json
from collections import defaultdict
import ast
import os
import torch

broker = "localhost"
port = 1883
keepalive = 60
# keepalive: maximum period in seconds allowed between communications with the broker. 
# if no other messages are being exchanged, this controls the rate at which the client will send ping messages to the broker

# load settings
with open('settings.txt', 'r') as f:
    settings_dict = {}
    line = f.readline()
    while line:
        line = line.split('=')
        key = line[0]
        value = line[1]
        value = value.split('\n')[0]
        settings_dict[key] = value
        line = f.readline()
    f.close()

os.makedirs(settings_dict['output_folder'], exist_ok=True)
os.makedirs(settings_dict['input_folder'], exist_ok=True)

# set map of supermarket
supermarket_map = ast.literal_eval(settings_dict['map'])

# add path of YOLOv5 to sys.path for easier loading of libraries
sys.path.append(settings_dict['yolov5_dir'])
from detect import detect

###### define callbacks ################################################################  
def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed to topic : " + str(mid) + " with Qos " + str(granted_qos))

def on_publish(client, userdata, mid):
    print("Published to topic: " + str(mid) + "\n")

def on_connect(client, userdata, flags, rc):
    client.subscribe("capstone/capture", 0)
    print("Connected to MQTT broker with result code: " + str(rc) + "\n")

def on_disconnect(client, userdata, rc):
    client.loop_stop()
    if rc!=0:
        print("Unexpected disconnection")

def on_message(client, userdata, msg):
    print("Received message: on topic " + str(msg.topic) 
    + " " + "with QoS " + str(msg.qos))
    
    if str(msg.topic) == "capstone/capture":
        data_in_dict = json.loads(msg.payload)
        img_array = np.asarray(data_in_dict['input_img_array_list']).astype(np.uint8)
        # img_array = img_array[:, :, ::-1]
        im = Image.fromarray(img_array)
        im.save(settings_dict['input_folder'] + 'image.jpg', 'JPEG')

        location = data_in_dict['location']
        right_item_name = supermarket_map[location]

        print(supermarket_map)

        # Run YOLOv5 detections
        with torch.no_grad():
            bboxes = detect(settings_dict['output_folder'], settings_dict['input_folder'], pretrained_weights=settings_dict['pretrained_weights_path'], custom_weights=settings_dict['custom_weights_path']
                , view_img=False, imgsz=640, device='cpu', conf_thres=0.4, iou_thres=0.5, classes=None, agnostic_nms=True, augment=True, supermarket_map=supermarket_map, correct_class_name=right_item_name, save_img=True)
        
        location = data_in_dict['location']
        misplaced = False
        for key in bboxes.keys():
            if key != supermarket_map[location]:
                misplaced = True
        data_out_json = json.dumps(("Actual: " + supermarket_map[location], misplaced, bboxes))
        client.publish('capstone/detection', data_out_json)

#instantiate an object of the mqtt client
client = paho.Client("detection", clean_session= False, userdata=None) 

#assign the functions to the respective callbacks
client.on_subscribe = on_subscribe
client.on_publish = on_publish
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message= on_message

# client.username_pw_set("pgharvest", "1234")

client.reconnect_delay_set(min_delay=1, max_delay=180)

#establish connection to the broker
client.connect(broker, port, keepalive)

# right_item_name = 'banana'
# bboxes = detect(settings_dict['output_folder'], settings_dict['input_folder'], pretrained_weights=settings_dict['pretrained_weights_path'], custom_weights=settings_dict['custom_weights_path']
#             , view_img=False, imgsz=640, device='cpu', conf_thres=0.4, iou_thres=0.5, classes=None, agnostic_nms=True, augment=True, supermarket_map=supermarket_map, correct_class_name=right_item_name, save_img=True)

client.loop_forever()