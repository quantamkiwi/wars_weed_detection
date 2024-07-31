import cv2
import math

spray_system_enable = True # Just to entertain the sim.


class VideoProcessor:

    def __init__(self, cap):
        self.cap = cap




        self.weed_threshold = 8
        self.dev_mode = True
        self.weed_cam_status = 0

        # cap.set(3, 480)
        # cap.set(4,240)

        FPS = 7 # Modifiable

        # --------------------- COLOUR ---------------------
        # Colour thresholds to identify weeds in dark soil
        # ORIGINAL
        # dark_green = (30, 50, 40) #HSV format (0, 0, 240) 
        # light_green = (100,255, 255) #(255, 15, 255)


        # dark_green = (40, 60, 80) #HSV format (0, 0, 240) 
        # light_green = (100,150, 255) #(255, 15, 255)

        # TEST
        self.dark_green = (40, 65, 100) #HSV format (0, 0, 240) 
        self.light_green = (80,255, 255) #(255, 15, 255)

        # --------------------------------------------------

        self.left_crop = 100 #0
        self.right_crop = 540 #640
        self.top_crop = 0
        self.bottom_crop =  400 # 210

        # Cropping parameters
        self.screen_width = self.right_crop - self.left_crop
        self.screen_height = self.top_crop - self.bottom_crop

        # Sprayer sections
        self.spray_line_bottom = 20
        self.spray_line_top = 130
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
        self.x_centre_left = 90
        self.x_centre_right = 140
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


    def thresholding(self):

        color = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(color, self.dark_green, self.light_green)
        print("masked")

        dilated_connect = cv2.dilate(mask, None, iterations=3 ) #Dilate to connect leaves
        eroded = cv2.erode(dilated_connect, None, iterations=4) #Erode to remove noise
        dilated = cv2.dilate(eroded, None, iterations=5 ) #Dilate to get correct size
        return dilated

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

            self.frame = self.frame[self.top_crop:self.bottom_crop,self.left_crop:self.right_crop] #Cropping, should comment this out to check for sim

            print("framed")

            if spray_system_enable:
                print("sprayer")

                self.watchdog_frames += 1
                        
                # if cluster_accum >= max_cluster_size and found_cluster == False:
                #     found_cluster = True
                #     #print("Found Cluster")            
                            
                # if found_cluster == True:
                #     cluster_frames += 1
                #     if cluster_frames <= 10*FPS:
                #         send_slow_speed = 1 #Send a flag
                #         #  print("Frame {}".format(cluster_frames))
                        
                #     else:
                #         send_slow_speed = 0
                #         cluster_frames = 0
                #         found_cluster = False
                    
                # cluster_accum = 0    
                


                # if watchdog_frames >= 5*FPS and weed_found == 0:
                #     sent_left[:] = []
                #     sent_right[:] = []
                #     watchdog_frames = 0
                #     print("Timeout")
                # elif weed_found == 1:
                #     watchdog_frames = 0
                #     weed_found = 0



            self.grayscale_frame = self.thresholding()

            """6"""

            # Now that we have hopefully distinguished the coins, find and fit ellipses around the coins in the image.
            contours, _ = cv2.findContours(self.grayscale_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

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

                if self.spray_line_bottom  < cY < self.spray_line_top:
                    if area > 100:
                        number_of_sprays = 1

                    if cX < 240:

                        if abs(self.cX_old_left - cX) > self.weed_threshold:
                            print("cX: {}, cX_old_left:{}".format(cX,self.cX_old_left))

                            self.cX_old_left = cX
                            xcord_deg_left = -math.degrees(math.atan(((cX-self.x_centre_left)*self.a)/150))
                            xcord_deg_right = 0
                            number_of_sprays_left = number_of_sprays
                            number_of_sprays_right = 0
                    else: 
                        if abs(self.cX_old_right - cX) > self.weed_threshold:
                            print("cX: {}, cX_old_right:{}".format(cX,self.cX_old_right))
                            self.cX_old_right = cX
                            xcord_deg_right = -math.degrees(math.atan(((cX-self.x_centre_right-240)*self.a)/150))
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
            
            cv2.line(self.frame, (0, self.spray_line_top), (self.screen_width, self.spray_line_top), (0, 255, 0), 2)
            cv2.line(self.frame, (0, self.spray_line_bottom), (self.screen_width, self.spray_line_bottom), (0, 0, 255), 2)

            # Write_image(image_pub, frame)
            if (self.dev_mode):
                #print("in DEV")
                
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
            cv2.line(self.frame, (0, self.spray_line_top), (self.screen_width, self.spray_line_top), (0, 255, 0), 2)
            cv2.line(self.frame, (0, self.spray_line_bottom), (self.screen_width, self.spray_line_bottom), (0, 0, 255), 2)

            # Write_image(image_pub, frame)

        # Write_image(image_pub, frame)
        print("end of if")

        self.cap.release()
        cv2.destroyAllWindows()



if __name__ == "__main__":

    # Get document folder. 
    doc_folder = "test_content/"

    # Get Video
    cap = cv2.VideoCapture(doc_folder + "test_vid_1.avi")
    
    vp = VideoProcessor(cap)
    vp.loop()