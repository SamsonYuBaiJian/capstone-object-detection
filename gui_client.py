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
import imutils
import pyzbar.pyzbar as pyzbar
import ast
import cv2
import sys


def barcode_scanner(img_path, label, barcode_map):
    label_to_idx = barcode_map
    idx_to_label = {v: k for k, v in label_to_idx.items()}    
    
    # load the input image
    image = cv2.imread(img_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    barcodeDetected = []

    for i in range(0, 10, 10):
        # Rotate image to find barcodes
        image = imutils.rotate_bound(image, i) 

        # find the barcodes in the image and decode each of the barcodes
        barcodes = pyzbar.decode(image)

        # loop over the detected barcodes
        for barcode in barcodes:        
            barcode_type = barcode.type

            # Comment out to detect QR codes
            if barcode_type == "QRCODE":            
                continue    

            # the barcode data is a bytes object so if we want to draw it on
            # our output image we need to convert it to a string first
            barcode_data = barcode.data.decode("utf-8")
            try:
                barcode_label = idx_to_label[int(barcode_data)]
                barcodeDetected.append(barcode_label)
                # extract the bounding box location of the barcode and draw the
                # bounding box surrounding the barcode on the image
                (x, y, w, h) = barcode.rect
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)

                text = barcode_label
                cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            except KeyError:
                continue
        else:
            continue    
        break    
    
    if len(barcodeDetected) == 0:
        label = "Barcode detected: " + label
        cv2.putText(image, label, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    return image


def gui(q):
    def test(root, q, input_img_label, pred_img_label, text_label, barcode_map):
        try:
            data = q.get(0)
            actual_item = data[0]
            h, w, _ = np.asarray(Image.open('./inference/inputs/image.jpg')).shape
            screen_width = 1536
            pad_width = 30
            root.geometry('{}x{}'.format(w * 2 + pad_width, h + 50))
            # input_img = ImageTk.PhotoImage(Image.open('./inference/inputs/image.jpg'))
            input_img = Image.fromarray(barcode_scanner(img_path = './inference/inputs/image.jpg', label=actual_item, barcode_map=barcode_map), 'RGB')
            pred_img = Image.open('./inference/outputs/image.jpg')
            if w * 2 + pad_width > screen_width:
                # make sure image does not go out of screen
                root.geometry('{}x{}'.format(screen_width, h))
                max_width = int(np.floor((screen_width - pad_width) / 2))
                input_img = input_img.resize((max_width, int(h * max_width / w)))
                pred_img = pred_img.resize((max_width, int(h * max_width / w)))
                root.geometry('{}x{}'.format(screen_width, int(h * max_width / w) + 50))
            input_img = ImageTk.PhotoImage(input_img)
            pred_img = ImageTk.PhotoImage(pred_img)
            input_img_label.configure(image=input_img)
            input_img_label.image = input_img
            pred_img_label.configure(image=pred_img)
            pred_img_label.image = pred_img
            misplaced = data[1]
            if misplaced:
                text = 'misplaced item(s):'
                total_count = 0
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
            root.after(5, test, root, q, input_img_label, pred_img_label, text_label, barcode_map)
        except queue.Empty:
            root.after(5, test, root, q, input_img_label, pred_img_label, text_label, barcode_map)

    root = Tk()
    root.geometry('700x500')

    text_label = Label(root, text='Starting check for misplaced items...', font=(None, 20))
    text_label.pack(fill='x')
    input_img_label = Label(root)
    input_img_label.pack(side='left')
    pred_img_label = Label(root)
    pred_img_label.pack(side='right')

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

    barcode_map = ast.literal_eval(settings_dict['barcode_map'])
    root.after(5, test, root, q, input_img_label, pred_img_label, text_label, barcode_map)
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