import cv2
import numpy as np

class WeedTracker: 

    def __init__(self):
        self.fps = 7 # Probably going to need changing. Not used
        self.scale_factor = 10
        self.current_weeds = {0: [], 1: []}
        self.predicted_weeds = []
        self.ppf = 18
        self.min_contour_area = 10
        self.max_contour_area = 10000
        self.min_contour_points = 5
        self.sprayed_predictions = []

    def invalid_contour(self, contour, area):
        """Checks that the contour area is within a certain range and has more than 5 points."""
        return area < self.min_contour_area or area > self.max_contour_area or len(contour) < self.min_contour_points

    def is_contour_encapsulated(self, contour1, contour2):
        """
        Check if all points in contour2 are inside contour1
            contour2.dtype = np.int32
            contour1.dtype = np.int32
        """

        for point in contour2:
            # Convert point to tuple
            pt = (int(point[0][0]), int(point[0][1]))
            # pointPolygonTest returns:
            # > 0 if the point is inside the contour
            # 0 if the point is on the contour
            # < 0 if the point is outside the contour
            dist = cv2.pointPolygonTest(contour1, pt, False)
            if dist < 0:
                return False
        return True

    def known_contour(self, contour): 
        """
        Check if a particular contour is known. 
        """
        for known_contour in self.predicted_weeds: 
            if self.is_contour_encapsulated(known_contour, contour):
                return 1 
        return 0

    def process_new_contours(self, contours): 
        """
        Process all weeds seen in the current frame and allocate them
        to the dictionary based on whether we already knew about the weed
        or not.
        """

        self.current_weeds = {0: [], 1: []}

        for contour in contours:
           
            area = cv2.contourArea(contour)

            if self.invalid_contour(contour, area):
                continue

            self.current_weeds[self.known_contour(contour)].append(contour)
    
    def predict_new_contours(self): 
        """
        Predict where each weed is going to be in the proceeding frame. 
        """
        self.predicted_weeds = []
        for contour in self.current_weeds[1] + self.current_weeds[0]:
            self.predicted_weeds.append(self.next_predicted_location_scaled(contour))

    def next_predicted_location_scaled(self, contour):
        """
        A function to predict a spotted weed will be in the next frame.
        """ 
        # Convert the contour to a numpy array for easy manipulation
        contour_array = np.array(contour, dtype=np.float32)
        
        # Calculate the centroid of the contour for scaling
        M = cv2.moments(contour_array)
        if M['m00'] == 0:
            return contour  # Prevent division by zero if the contour is degenerate
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
        
        # Shift the contour
        shifted_contour = contour_array + np.array([0, self.ppf])
        
        # Scale the contour around the centroid
        scaled_contour = (shifted_contour - np.array([cx, cy])) * self.scale_factor + np.array([cx, cy])
        
        # Convert back to integer type
        scaled_contour = scaled_contour.astype(np.int32)
        print(f'scaled_contour:{scaled_contour}')
        print(f'original_contour: {contour}')
        
        return scaled_contour
    
    def input_sprayed_contours(self, contours):
        """
        Update the predicted location of sprayed weeds in the next frame. 
        """
        self.sprayed_predictions = []
        for contour in contours:
            self.sprayed_predictions.append(self.next_predicted_location_scaled(contour))

    def sprayed_contour(self, contour):
        """
        Check if a particular contour is known. 
        """
        for sprayed_contour in self.sprayed_predictions: 
            if self.is_contour_encapsulated(sprayed_contour, contour):
                return 1 
        return 0

    
    def set_ppf(self, ppf):
        """
        Set the pixels per frame speed. 
        """
        self.ppf = ppf
        
