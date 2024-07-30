import cv2
import numpy as np

# Define a function to initialize the Kalman Filter
def initialize_kalman_filter():
    kf = cv2.KalmanFilter(4, 2)

    # State vector [x, y, dx, dy]
    kf.transitionMatrix = np.array([[1, 0, 1 , 0],
                                    [0, 1, 0, 1],
                                    [0, 0, 1, 0],
                                    [0, 0, 0, 1]], np.float32)

    # Measurement matrix [x, y]
    kf.measurementMatrix = np.array([[1, 0, 0, 0],
                                     [0, 1, 0, 0]], np.float32)

    # Process noise covariance
    kf.processNoiseCov = np.array([[1, 0, 0, 0],
                                   [0, 1, 0, 0],
                                   [0, 0, 1, 0],
                                   [0, 0, 0, 1]], np.float32) * 0.03

    # Measurement noise covariance
    kf.measurementNoiseCov = np.array([[1, 0],
                                       [0, 1]], np.float32) * 0.1

    # Error covariance post
    kf.errorCovPost = np.eye(4, dtype=np.float32)

    return kf

# Example usage with a list of centroids
def main():
    # Create a Kalman Filter object
    kf = initialize_kalman_filter()

    # List of observed centroids
    centroids = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]

    # Initialize the Kalman Filter state with the first centroid
    kf.statePost = np.array([centroids[0][0], centroids[0][1], 0, 0], np.float32)

    # Iterate over the centroids
    for i, centroid in enumerate(centroids):
        # Predict the next state
        prediction = kf.predict()
        predicted_position = (prediction[0], prediction[1])
        print(f"Predicted position: {predicted_position}")

        # Update the Kalman Filter with the current measurement
        measurement = np.array([[centroid[0]], [centroid[1]]], np.float32)
        kf.correct(measurement)
        updated_position = (kf.statePost[0], kf.statePost[1])
        print(f"Updated position: {updated_position}")

if __name__ == "__main__":
    main()
