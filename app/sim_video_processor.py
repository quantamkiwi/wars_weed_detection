import cv2
import math
import argparse
import json
import numpy as np

from kalman_filter import WeedTracker


def load_config(config_file):
    """
    Loading in the JSON congiguration file. 
    """
    with open(config_file, 'r') as file:
        return json.load(file)

def parse_args():
    """ 
    Parsing the arguments in the JSON configuration file and returning an 
    arg object. 
    """
    parser = argparse.ArgumentParser(description='Weed detection system.')
    parser.add_argument('--config', type=str, default='app/config.json', help='Path to the configuration file')
    return parser.parse_args()


def initialize_video_capture(video_path):
    """ 
    Initializing the video capture. 
    -> Dev mode should be implemented here?
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video file {video_path}")
    return cap

def process_frame(frame, config):
    """ 
    Performs the neccessary frame preprocessing. 
    """
    # Crop Frame
    frame = frame[config['top_crop']:config['bottom_crop'], config['left_crop']:config['right_crop']]

    # Binary Threshold the frame based on the level of green.
    color = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(color, np.array(config['dark_green']), np.array(config['light_green']))

    # Perfrom Morphology on the masked frame.
    dilated_connect = cv2.dilate(mask, None, iterations=3)
    eroded = cv2.erode(dilated_connect, None, iterations=4)
    dilated = cv2.dilate(eroded, None, iterations=5)
    
    return frame, dilated



class VideoProcessor:
    """
    Class to process a video input and find weeds to spray. 
    """

    def __init__(self, cap, config):

        # Create attributes out of function parameters
        self.cap = cap
        self.config = config
        self.wt = WeedTracker()
        self.initialize_parameters()
        
        print(cap.isOpened())

        # --------------------------------------------------

    def initialize_parameters(self):
        """ 
        Function to initialize all the neccessary parameters needed for the video
        processor.
        """

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

    def invalid_contour(self, contour, area):
        """Checks that the contour area is within a certain range and has more than 5 points."""
        return area < self.min_contour_area or area > self.max_contour_area or len(contour) < self.min_contour_points

    def find_and_draw_contours(self, frame, gray_frame):
        """Finds contours and draws them on the frame."""
        contours, _ = cv2.findContours(gray_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        number_of_sprays = 0

        self.wt.process_new_contours(contours)
        # Show the predicted weed location from the previous iteration. 
        for contour in self.wt.predicted_weeds:
            ellipse = cv2.fitEllipse(contour)
            cv2.ellipse(frame, ellipse, (255, 255, 0), 2)
        self.wt.predict_new_contours()

        n_new = len(self.wt.current_weeds[0])
        # print(self.wt.current_weeds)
        i = -1
        sprayed = []

        for contour in self.wt.current_weeds[0] + self.wt.current_weeds[1]:
            # area = cv2.contourArea(contour)
            # if self.invalid_contour(contour, area):
            #     continue
            i += 1 

            moments = cv2.moments(contour)
            cX = int(moments["m10"] / moments["m00"])
            cY = int(moments["m01"] / moments["m00"])

            # Kalman Filter

            ellipse = cv2.fitEllipse(contour)
            if i < n_new:
                cv2.ellipse(frame, ellipse, (0, 255, 0), 2)
                cv2.circle(frame, (cX, cY), 7, (0, 255, 0), -1)
                continue 

            if self.config['spray_line_bottom'] < cY < self.config['spray_line_top']:
                sprayed.append(contour)
                if self.wt.sprayed_contour(contour):
                    # if sprayed
                    cv2.ellipse(frame, ellipse, (0, 0, 255), 2)
                    cv2.circle(frame, (cX, cY), 7, (0, 0, 255), -1)
                    continue 

                self.update_spray_data(cX, cY, number_of_sprays)
                    
            cv2.ellipse(frame, ellipse, (255, 0, 0), 2)
            cv2.circle(frame, (cX, cY), 7, (255, 0, 0), -1)
            

            # if area > 100:
            #     number_of_sprays = 1


        self.wt.input_sprayed_contours(sprayed)
        self.draw_spray_lines(frame)
        return frame

    def draw_spray_lines(self, frame):
        """Draws spray lines on the frame."""
        cv2.line(frame, (0, self.config['spray_line_top']), (self.screen_width, self.config['spray_line_top']), (0, 255, 0), 2)
        cv2.line(frame, (0, self.config['spray_line_bottom']), (self.screen_width, self.config['spray_line_bottom']), (0, 0, 255), 2)

    
    def update_spray_data(self, cX, cY, number_of_sprays):
        """Updates spray data based on contour centroid."""
        if cX < 240:
            if abs(self.cX_old_left - cX) > self.config['weed_threshold']:
                self.cX_old_left = cX
                self.xcord_deg_left = -math.degrees(math.atan(((cX - self.config['x_centre_left']) * self.a) / 150))
                self.xcord_deg_right = 0
                self.number_of_sprays_left = number_of_sprays
                self.number_of_sprays_right = 0
        else:
            if abs(self.cX_old_right - cX) > self.config['weed_threshold']:
                self.cX_old_right = cX
                self.xcord_deg_right = -math.degrees(math.atan(((cX - self.config['x_centre_right'] - 240) * self.a) / 150))
                self.xcord_deg_left = 0
                self.number_of_sprays_right = number_of_sprays
                self.number_of_sprays_left = 0

        self.input_array = [self.xcord_deg_left, 0, self.number_of_sprays_left, self.xcord_deg_right, 0, self.number_of_sprays_right]

    def display_frame(self, frame):
        """Displays the frame if in development mode."""
        if self.config['dev_mode']:
            cv2.namedWindow('Colour Segmentation', cv2.WINDOW_AUTOSIZE)
            cv2.imshow('Colour Segmentation', frame)
            if cv2.waitKey(100) & 0xFF == ord('q'):
                return False
        return True
    
    def cleanup(self):
        """Releases the video capture and destroys all windows."""
        self.cap.release()
        cv2.destroyAllWindows()

    def loop(self):

        while self.cap.isOpened():
            print("frame")

            self.ret, self.frame = cap.read()  # Read a frame from the video file.
    
            # If we cannot read any more frames from the video file, then exit.
            if not self.ret:
                print("Broken")
                break
            print("opened frame")

            self.frame, self.grey_frame = process_frame(self.frame, self.config) 
            print("framed")

            if self.config['spray_system_enable']:
                print("sprayer")
                self.frame = self.find_and_draw_contours(self.frame, self.grey_frame)

            if not self.display_frame(self.frame):
                break
        
        else:
            cv2.line(self.frame, (0, self.config['spray_line_top']), (self.screen_width, self.config['spray_line_top']), (0, 255, 0), 2)
            cv2.line(self.frame, (0, self.config['spray_line_bottom']), (self.screen_width, self.config['spray_line_bottom']), (0, 0, 255), 2)

        print("end of if")

        self.cleanup()



if __name__ == "__main__":

    # Get Program Configurations
    args = parse_args()
    config = load_config(args.config)

    # Get Video
    cap = initialize_video_capture(config['doc_folder'] + config["video_file"])
    
    # Create and start the video processor.
    vp = VideoProcessor(cap, config)
    vp.loop()