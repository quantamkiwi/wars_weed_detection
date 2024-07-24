import cv2

def main():
    # Path to your video file
    video_path = 'test_content/test_vid_1.avi'

    # Open the video file
    cap = cv2.VideoCapture(video_path)

    # Check if the video file opened successfully
    if not cap.isOpened():
        print(f'Error: Cannot open video file {video_path}')
        return

    print("Press any key to advance to the next frame. Press 'q' to exit.")

    while True:
        # Read the next frame
        ret, frame = cap.read()

        # If the frame was not read successfully, break the loop
        if not ret:
            print("End of video reached or unable to read the video file.")
            break

        # Display the frame
        cv2.imshow('Video', frame)

        # Wait for a key press
        key = cv2.waitKey(0)  # Wait indefinitely for a key press

        # Exit the loop if 'q' is pressed
        if key == ord('q'):
            break

    # Release the video capture object and close the display window
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
