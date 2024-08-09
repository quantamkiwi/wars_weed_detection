import cv2

def main():
    # Initialize the camera
    cap = cv2.VideoCapture(1)  # Use personal camera

    # Check if the camera opened successfully
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    # Set up the line positions
    spray_line_top = 210
    spray_line_bottom = 200

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        # If the frame was not read correctly, break the loop
        if not ret:
            print("Error: Could not read frame.")
            break

        # Get the width of the frame
        screen_width = frame.shape[1]

        # Draw the lines on the frame
        cv2.line(frame, (0, spray_line_top), (screen_width, spray_line_top), (0, 255, 0), 2)
        cv2.line(frame, (0, spray_line_bottom), (screen_width, spray_line_bottom), (0, 0, 255), 2)

        # Display the resulting frame
        cv2.imshow('Camera with Lines', frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # When everything done, release the capture and close windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()