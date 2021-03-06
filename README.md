# Capstone Object Detection
YOLOv5 server for SUTD Capstone project

## Setup
1. `pip3 install -r requirements.txt`.
2. Get the custom weights for YOLOv5 at https://drive.google.com/file/d/1czULVB0CeVR5qU607mvviR7lScTo_lRF/view?usp=sharing.

## Instructions
1. Run `sudo service mosquitto start` on server.
2. Run `python3 capture_client.py` on NUC.
3. Run `python3 detection_client.py` and `python3 gui_client.py` (make sure this is not on Anaconda as its Python does not work well with tkinter) on server.

## References
- https://github.com/ianlimle/Engineering-Design-Innovation
- http://www.steves-internet-guide.com/install-mosquitto-linux/
- https://www.e-consystems.com/blog/camera/how-to-access-cameras-using-opencv-with-python/

## Credits
Much credit to the amazing YOLOv5 team over at Ultralytics!