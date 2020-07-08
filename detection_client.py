import paho.mqtt.client as paho
from threading import Thread
from PIL import Image
import numpy as np
import json

# broker = "10.12.108.241"
broker = "localhost"
port = 1883
keepalive = 60
#keepalive: maximum period in seconds allowed between communications with the broker. 
#If no other messages are being exchanged, this controls the rate at which the client will send ping messages to the broker

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
        data_dict = json.loads(msg.payload)
        img_array = np.asarray(data_dict['img_array_list'])
        img_array = (img_array * 255).round().astype(np.uint8)
        im = Image.fromarray(img_array)
        im.save('./current.png', 'PNG')

        # TODO: Run YOLOv5 detection
        client.publish('capstone/detection', msg.payload)

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

client.loop_forever()