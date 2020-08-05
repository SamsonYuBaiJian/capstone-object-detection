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


def gui(notification_q, info_q):
    def test(root, max_size, info_q, input_img_label, pred_img_label, descrip_frame, status_label, barcode_map):
        try:
            data = info_q.get(0)
            descrip_frame.pack(side='bottom')
            actual_item = data[0]
            h, w, _ = np.asarray(Image.open('./inference/inputs/image.jpg')).shape
            # input_img = ImageTk.PhotoImage(Image.open('./inference/inputs/image.jpg'))
            input_img = Image.fromarray(barcode_scanner(img_path = './inference/inputs/image.jpg', label=actual_item, barcode_map=barcode_map), 'RGB')
            pred_img = Image.open('./inference/outputs/image.jpg')
            max_width = max_size[0]
            pad_width = 30
            if w * 2 + pad_width > max_width:
                # make sure image does not go out of screen
                max_width = int(np.floor((max_width - pad_width) / 2))
                input_img = input_img.resize((max_width, int(h * max_width / w)))
                pred_img = pred_img.resize((max_width, int(h * max_width / w)))
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
                status_label['text'] = "{} {}".format(total_count, text)
            else:
                if len(data[2].keys()) > 0:
                    # for misplaced items
                    status_label['text'] = 'No misplaced items!'
                else:
                    # for OOS items
                    status_label['text'] =  '{} is out of stock!'.format(actual_item)
            root.after(5, test, root, max_size, info_q, input_img_label, pred_img_label, descrip_frame, status_label, barcode_map)
        except queue.Empty:
            root.after(5, test, root, max_size, info_q, input_img_label, pred_img_label, descrip_frame, status_label, barcode_map)


    def start_robot(root, start_button, notification_q, info_q, input_img_label, pred_img_label, descrip_frame, barcode_map):
        start_button.destroy()
        descrip_frame['highlightbackground'] = "black"
        descrip_frame['highlightthickness'] = 4
        notification_q.put('START')
        max_size = root.maxsize()
        root.geometry('{}x{}'.format(max_size[0], max_size[1]))
        text_label = Label(descrip_frame, text='Starting check for misplaced items...', height=5, font=(None, 20), bg='white')
        text_label.pack()
        root.after(5, test, root, max_size, info_q, input_img_label, pred_img_label, descrip_frame, text_label, barcode_map)


    root = Tk()
    root.geometry('600x250')
    root['bg']= "white"

    title_label = Label(root, text='R E D R O', pady=20, font=(None, 25), bg='white')
    title_label.pack(fill='x')
    input_img_label = Label(root)
    input_img_label.pack(side='left')
    pred_img_label = Label(root)
    pred_img_label.pack(side='right')
    descrip_frame = Frame(root, bg="white")
    descrip_frame.pack(fill='x')
    start_button = Button(root, text='START', bg="gray24", fg="white", activebackground='black', 
        activeforeground='white', height=3, font=(None, 30), command = lambda: start_robot(root, start_button, notification_q, info_q, input_img_label, 
        pred_img_label, descrip_frame, barcode_map))
    start_button.pack(fill='x')

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
    root.mainloop()


def main(notification_q, info_q):
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
            info_q.put(data_in_dict)


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

    client.loop_start()

    while True:
        try:
            notify = notification_q.get(0)
            client.publish('capstone/notify', notify)
        except queue.Empty:
            pass

notification_q = queue.Queue()
info_q = queue.Queue()
gui = threading.Thread(target=gui, args =(notification_q, info_q))
main = threading.Thread(target=main, args =(notification_q, info_q))

gui.start()
main.start()