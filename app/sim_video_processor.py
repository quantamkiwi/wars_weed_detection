import cv2
import math
import argparse
import json
import numpy as np


def load_config(config_file):
    with open(config_file, 'r') as file:
        return json.load(file)

def parse_args():
    parser = argparse.ArgumentParser(description='Weed detection system.')
    parser.add_argument('--config', type=str, default='app/config.json', help='Path to the configuration file')
    return parser.parse_args()


def initialize_video_capture(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video file {video_path}")
    return cap

def process_frame(frame, config):
    frame = frame[config['top_crop']:config['bottom_crop'], config['left_crop']:config['right_crop']]
    color = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(color, np.array(config['dark_green']), np.array(config['light_green']))

    dilated_connect = cv2.dilate(mask, None, iterations=3)
    eroded = cv2.erode(dilated_connect, None, iterations=4)
    dilated = cv2.dilate(eroded, None, iterations=5)
    
    return frame, dilated



class VideoProcessor:

    def __init__(self, cap, config):
        self.cap = cap
        self.config = config

        # --------------------------------------------------

        # Cropping parameters
        self.screen_width = self.config['right_crop'] - self.config['left_crop']
        self.screen_height = self.config['top_crop'] - self.config['bottom_crop']

        # Sprayer sections
        self.spray_line_optimal = 90

        self.send_slow_speed = 0
        self.watchdog_frames = 0
        self.cluster_frames = 0
        self.weed_found = 0
        self.max_cluster_size = 5
        self.cluster_accum = 0
        self.found_cluster = False

        self.xcord_deg_left = 0
        self.xcord_deg_right = 0
        self.number_of_sprays_left = 0
        self.number_of_sprays_right = 0
        self.a = 0.99
        self.cX_old_left = 1000
        self.cX_old_right = 1000

        self.sent_left = []
        self.sent_right = []
        self.input_array = []

        self.min_contour_area = 10
        self.max_contour_area = 10000
        self.min_contour_points = 5


        print(cap.isOpened())
    
    def invalid_contour(self, contour, area):
        if area < self.min_contour_area or area > self.max_contour_area or len(contour) < self.min_contour_points:  # Set a lower bound on the elipse area.
            return True
        return False


    def loop(self):

        while self.cap.isOpened():
            print("frame")
    

            """1"""

            self.ret, self.frame = cap.read()  # Read a frame from the video file.
            # If we cannot read any more frames from the video file, then exit.
            print("opened frame")
            if not self.ret:
                print("Broken")
                break
        
            """2"""

            self.frame, self.grey_frame = process_frame(self.frame, self.config) #Cropping, should comment this out to check for sim

            print("framed")

            if config['spray_system_enable']:
                print("sprayer")

                        

            """6"""

            # Now that we have hopefully distinguished the coins, find and fit ellipses around the coins in the image.
            contours, _ = cv2.findContours(self.grey_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            number_of_sprays = 0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if self.invalid_contour(contour, area):
                    continue

                    
                # cv2.drawContours(self.frame, contours, -1, (0,0,255), 1)
                ellipse = cv2.fitEllipse(contour)  # Fit an ellipse to the points in the contour.

                cv2.ellipse(self.frame, ellipse, (0,255,0), 2)  # Draw the ellipse on the original image.
                
                # Use the moments of the contour to draw a dot at the centroid.
                moments = cv2.moments(contour)
                cX = int(moments["m10"] / moments["m00"])
                cY = int(moments["m01"] / moments["m00"])
                cv2.circle(self.frame, (cX, cY), 7, (0, 255, 0), -1) # Draw circles idenitified by moments

                if self.config['spray_line_bottom']  < cY < self.config['spray_line_top']:
                    if area > 100:
                        number_of_sprays = 1

                    if cX < 240:

                        if abs(self.cX_old_left - cX) > config['weed_threshold']:
                            print("cX: {}, cX_old_left:{}".format(cX,self.cX_old_left))

                            self.cX_old_left = cX
                            xcord_deg_left = -math.degrees(math.atan(((cX-self.config['x_centre_left'])*self.a)/150))
                            xcord_deg_right = 0
                            number_of_sprays_left = number_of_sprays
                            number_of_sprays_right = 0
                    else: 
                        if abs(self.cX_old_right - cX) > config['weed_threshold']:
                            print("cX: {}, cX_old_right:{}".format(cX,self.cX_old_right))
                            self.cX_old_right = cX
                            xcord_deg_right = -math.degrees(math.atan(((cX-self.config['x_centre_right']-240)*self.a)/150))
                            xcord_deg_left = 0
                            number_of_sprays_right = number_of_sprays
                            number_of_sprays_left = 0
                            
                    input_array = [xcord_deg_left,0,number_of_sprays_left,xcord_deg_right,0,number_of_sprays_right]

                    """PUBLISH DATA"""
                    # if number_of_sprays_left > 0 or number_of_sprays_right > 0:
                    #     # sprayer_msg.data = input_array
                    #     # sprayer_input.publish(sprayer_msg)
                    #     print("Sending this: ", input_array)
                    #     print("Area of contour: ", area)
            
            cv2.line(self.frame, (0, self.config['spray_line_top']), (self.screen_width, self.config['spray_line_top']), (0, 255, 0), 2)
            cv2.line(self.frame, (0, self.config['spray_line_bottom']), (self.screen_width, self.config['spray_line_bottom']), (0, 0, 255), 2)

            # Write_image(image_pub, frame)
            if (self.config['dev_mode']):
                
                # Show images
                cv2.namedWindow('Colour Segmentation', cv2.WINDOW_AUTOSIZE)
                # frame = cv2.resize(frame, (int(frame.shape[1]*3), int(frame.shape[0]*3))) #For display
                cv2.imshow('Colour Segmentation', self.frame)

                # cv2.imshow('Mask', mask)5
                # cv2.imshow('Dilated Connect', dilated_connect)
                # cv2.imshow('Eroded', eroded)
                # cv2.imshow('dilated', dilated)

            if cv2.waitKey(100) & 0xFF == ord('q'):
                break
        
        else:
            cv2.line(self.frame, (0, self.config['spray_line_top']), (self.screen_width, self.config['spray_line_top']), (0, 255, 0), 2)
            cv2.line(self.frame, (0, self.config['spray_line_bottom']), (self.screen_width, self.config['spray_line_bottom']), (0, 0, 255), 2)

            # Write_image(image_pub, frame)

        # Write_image(image_pub, frame)
        print("end of if")

        self.cap.release()
        cv2.destroyAllWindows()



if __name__ == "__main__":

    # Get Program Configurations
    args = parse_args()
    config = load_config(args.config)

    # Get Video
    cap = initialize_video_capture(config['doc_folder'] + config["video_file"])
    
    # Create and start the video processor.
    vp = VideoProcessor(cap, config)
    vp.loop()