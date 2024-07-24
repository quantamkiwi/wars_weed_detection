import cv2
import math

spray_system_enable = True # Just to entertain the sim.
WEED_THRESHOLD = 8
dev_mode = True
weed_cam_status = 0

# Get document folder. 
doc_folder = "test_content/"

# Get Video
cap = cv2.VideoCapture(doc_folder + "test_vid_1.avi")

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
dark_green = (40, 65, 100) #HSV format (0, 0, 240) 
light_green = (80,255, 255) #(255, 15, 255)

# --------------------------------------------------

left_crop = 0
right_crop = 640
top_crop = 0
bottom_crop = 210

# Cropping parameters
screen_width = right_crop - left_crop
screen_height = top_crop - bottom_crop

# Sprayer sections
spray_line_bottom = 20
spray_line_top = 130

send_slow_speed = 0
watchdog_frames = 0
cluster_frames = 0
weed_found = 0
max_cluster_size = 5
cluster_accum = 0
found_cluster = False

xcord_deg_left = 0
xcord_deg_right = 0
number_of_sprays_left = 0
number_of_sprays_right = 0
x_centre_left = 90
x_centre_right = 140
a = 0.99
cX_old_left = 1000
cX_old_right = 1000

sent_left = []
sent_right = []
input_array = []


print(cap.isOpened())

while cap.isOpened():
    print("frame")

    """1"""

    ret, frame = cap.read()  # Read a frame from the video file.
    # If we cannot read any more frames from the video file, then exit.
    print("opened frame")
    if not ret:
        print("Broken")
        break
    
    """2"""

    # frame = frame[top_crop:bottom_crop,left_crop:right_crop] #Cropping, should comment this out to check for sim

    print("framed")

    if spray_system_enable:
        print("sprayer")

        watchdog_frames += 1
                
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


        """3"""

        color = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(color, dark_green, light_green)
        print("masked")
        
        # kernel = np.ones((3,3), np.uint8)

        """5"""

        dilated_connect = cv2.dilate(mask, None, iterations=3 ) #Dilate to connect leaves
        eroded = cv2.erode(dilated_connect, None, iterations=4) #Erode to remove noise
        dilated = cv2.dilate(eroded, None, iterations=5 ) #Dilate to get correct size

        """6"""

        # Now that we have hopefully distinguished the coins, find and fit ellipses around the coins in the image.
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        number_of_sprays = 0
        number_of_sprays_left = 0
        number_of_sprays_right = 0
        
        for contour in contours:

            area = cv2.contourArea(contour)
            if area < 10:  # Set a lower bound on the elipse area.
                continue

            if area > 10000:
                continue
            
            if len(contour) < 5:  # The fitEllipse function requires at least five points on the contour to function.
                continue

            """7"""
                
            cv2.drawContours(frame, contours, -1, (0,0,255), 1)
            ellipse = cv2.fitEllipse(contour)  # Fit an ellipse to the points in the contour.

            cv2.ellipse(frame, ellipse, (0,255,0), 2)  # Draw the ellipse on the original image.
            
            # Use the moments of the contour to draw a dot at the centroid.
            moments = cv2.moments(contour)
            cX = int(moments["m10"] / moments["m00"])
            cY = int(moments["m01"] / moments["m00"])
            cv2.circle(frame, (cX, cY), 7, (0, 255, 0), -1) # Draw circles idenitified by moments

            if spray_line_bottom  < cY < spray_line_top:
                if area < 300:
                    number_of_sprays = 1
                elif 300 <= area < 500:
                    number_of_sprays = 1
                elif 500 <= area < 1000:
                    number_of_sprays = 1
                elif 1000 <= area < 5000:
                    number_of_sprays = 1 #2
                elif 5000 <= area < 8000:
                    number_of_sprays = 1 #3
                else:
                    number_of_sprays = 1 #4
                if cX < 240:
                    if abs(cX_old_left - cX) > WEED_THRESHOLD:
                        print("cX: {}, cX_old_left:{}".format(cX,cX_old_left))
                        cX_old_left = cX
                        xcord_deg_left = -math.degrees(math.atan(((cX-x_centre_left)*a)/150))
                        xcord_deg_right = 0
                        number_of_sprays_left = number_of_sprays
                        number_of_sprays_right = 0
                else: 
                    if abs(cX_old_right - cX) > WEED_THRESHOLD:
                        print("cX: {}, cX_old_right:{}".format(cX,cX_old_right))
                        cX_old_right = cX
                        xcord_deg_right = -math.degrees(math.atan(((cX-x_centre_right-240)*a)/150))
                        xcord_deg_left = 0
                        number_of_sprays_right = number_of_sprays
                        number_of_sprays_left = 0
                        
                input_array = [xcord_deg_left,0,number_of_sprays_left,xcord_deg_right,0,number_of_sprays_right]

                if number_of_sprays_left > 0 or number_of_sprays_right > 0:
                    # sprayer_msg.data = input_array
                    # sprayer_input.publish(sprayer_msg)
                    print("Sending this: ", input_array)
                    print("Area of contour: ", area)
        
        cv2.line(frame, (0, spray_line_top), (screen_width, spray_line_top), (0, 255, 0), 2)
        cv2.line(frame, (0, spray_line_bottom), (screen_width, spray_line_bottom), (0, 0, 255), 2)

        # Write_image(image_pub, frame)
        if (dev_mode):
            #print("in DEV")
            
            # Show images
            cv2.namedWindow('Colour Segmentation', cv2.WINDOW_AUTOSIZE)
            # frame = cv2.resize(frame, (int(frame.shape[1]*3), int(frame.shape[0]*3))) #For display
            cv2.imshow('Colour Segmentation', frame)

            # cv2.imshow('Mask', mask)5
            # cv2.imshow('Dilated Connect', dilated_connect)
            # cv2.imshow('Eroded', eroded)
            # cv2.imshow('dilated', dilated)

        if cv2.waitKey(100) & 0xFF == ord('q'):
            break
    
    else:
        cv2.line(frame, (0, spray_line_top), (screen_width, spray_line_top), (0, 255, 0), 2)
        cv2.line(frame, (0, spray_line_bottom), (screen_width, spray_line_bottom), (0, 0, 255), 2)

        # Write_image(image_pub, frame)

    # Write_image(image_pub, frame)
    print("end of if")

cap.release()
cv2.destroyAllWindows()

