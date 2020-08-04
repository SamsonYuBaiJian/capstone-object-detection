import paho.mqtt.client as paho
from threading import Thread
from tkinter import *
from PIL import Image, ImageTk
import numpy as np
import json
from collections import defaultdict
import os
import threading
import queue
import tkinter.font as tkFont


def gui(q):
    def test(root, q, input_img_label, pred_img_label, text_label):
        try:
            data = q.get(0)
            h, w, _ = np.asarray(Image.open('./inference/outputs/image.jpg')).shape
            root.geometry('{}x{}'.format(w * 2 + 30, h + 50))
            input_img = ImageTk.PhotoImage(Image.open('./inference/inputs/image.jpg'))
            input_img_label.configure(image=input_img)
            input_img_label.image = input_img
            pred_img = ImageTk.PhotoImage(Image.open('./inference/outputs/image.jpg'))
            pred_img_label.configure(image=pred_img)
            pred_img_label.image = pred_img
            misplaced = data[1]
            if misplaced:
                text = 'misplaced item(s):'
                total_count = 0
                actual_item = data[0].split()[1]
                for item in data[2].keys():
                    if item != actual_item:
                        number_of_item = len(data[2][item])
                        if total_count == 0:
                            text += " {} {}".format(number_of_item, item)
                        else:
                            text += ", {} {}".format(number_of_item, item)
                        total_count += number_of_item
                text_label['text'] = "{} {}".format(total_count, text)
            else:
                text_label['text'] = 'No misplaced items!'
            root.after(5, test, root, q, input_img_label, pred_img_label, text_label)
        except queue.Empty:
            root.after(5, test, root, q, input_img_label, pred_img_label, text_label)

    root = Tk()
    root.geometry('700x500')

    text_label = Label(root, text='Starting check for misplaced items...', font=(None, 20))
    text_label.pack(fill='x')
    input_img_label = Label(root)
    input_img_label.pack(side='left')
    pred_img_label = Label(root)
    pred_img_label.pack(side='right')

    root.after(5, test, root, q, input_img_label, pred_img_label, text_label)
    root.mainloop()


def main(q):
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
        client.subscribe("capstone/gui", 0)
        print("Connected to MQTT broker with result code: " + str(rc) + "\n")

    def on_disconnect(client, userdata, rc):
        client.loop_stop()
        if rc!=0:
            print("Unexpected disconnection")

    def on_message(client, userdata, msg):
        print("Received message: on topic " + str(msg.topic) 
        + " " + "with QoS " + str(msg.qos))
        
        if str(msg.topic) == "capstone/gui":
            data_in_dict = json.loads(msg.payload)
            q.put(data_in_dict)


    #instantiate an object of the mqtt client
    client = paho.Client("gui", clean_session= False, userdata=None) 

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

q = queue.Queue()
gui = threading.Thread(target=gui, args =(q, ))
main = threading.Thread(target=main, args =(q, ))

gui.start()
main.start()