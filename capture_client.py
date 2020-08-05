import paho.mqtt.client as paho
import time
from threading import Thread
import sys
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import json
# sys.path.remove('/opt/ros/kinetic/lib/python2.7/dist-packages')
import cv2

# broker = "10.12.43.47"
broker = "localhost"
port = 1883
keepalive = 60
# keepalive: maximum period in seconds allowed between communications with the broker. 
# if no other messages are being exchanged, this controls the rate at which the client will send ping messages to the broker

###### define callbacks ################################################################  
def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed to topic : " + str(mid) + " with Qos " + str(granted_qos))

def on_publish(client, userdata, mid):
    print("Published to topic: " + str(mid) + "\n")

def on_connect(client, userdata, flags, rc):
    client.subscribe("capstone/detection", 0)
    print("Connected to MQTT broker with result code: " + str(rc) + "\n")

def on_disconnect(client, userdata, rc):
    client.loop_stop()
    if rc!=0:
        print("Unexpected disconnection")

def on_message(client, userdata, msg):
    print("Received message: on topic " + str(msg.topic) 
    + " " + "with QoS " + str(msg.qos))
    
    if str(msg.topic) == "capstone/detection":
        data_in_dict = json.loads(msg.payload)
        print("Received", data_in_dict)

#instantiate an object of the mqtt client
client = paho.Client("capture", clean_session= False, userdata=None) 

#assign the functions to the respective callbacks
client.on_subscribe = on_subscribe
client.on_publish = on_publish
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

# client.username_pw_set("pgharvest", "1234")

client.reconnect_delay_set(min_delay=1, max_delay=180)

# establish connection to the broker
client.connect(broker, port, keepalive)

# set up the camera


def capture(location):
    # _, frame = cap.read()
    # cv2.imwrite('./test.jpg', frame)
    frame = plt.imread('/mnt/c/Users/samso/Desktop/image.jpg', format='jpeg')
    # frame = plt.imread('/mnt/c/Users/samso/Desktop/image.png', format='png')
    data_out_dict = {'input_img_array_list': frame.tolist(), 'input_img_dim': str(frame.shape), 'location': location}
    data_out_json = json.dumps(data_out_dict)
    client.publish('capstone/capture', data_out_json)

client.loop_start()

while True:
    # get prompt and location from ROS
    try:
        # set up the camera
        # cap = cv2.VideoCapture(0)
        # cap.set(cv2.CAP_PROP_FRAME_WIDTH,640)
        # cap.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
        i = input('location')
        capture(int(i))
        # release camera to refresh feed
        # cap.release()
    except KeyboardInterrupt:
        print("Stopped video streaming.")
        # cap.release()
        exit()
