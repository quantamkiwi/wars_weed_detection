# 🌿 WARS Weed Detection

Developing a new weed detection algorithm for WARS.

## 🐍 Python Files

- **`video_processor.py`**
  - This file is the **old** video processor that is being improved upon.

- **`video_cutting.ipynb`**
  - This file is cuts the **first X seconds** off of the **start** of a video file. 

- **`flick_through_frames.py`**
  - This file flicks through frames at the push of a button. This is to **calibrate speed** (pixels per second) of the robot with respect to the camera.

- **`app/`**

  - **`sim_video_processor.py`**
    - This file is the **new** development video processor that runs videos to simulate a development environment.

  - **`kalman_filter.py`**
    - The kalman filter will be implemented here, the current contents are just GPT'd.

## 📁 Folders

- **`documents/`**
  - This folder holds the **development plan** for the new processor.
    - These are to note down development updates and refer to for what to develop next.

- **`test_content/`**
  - This folder holds the video content. It is ignored in all git updates **using .gitignore** because the files are **too large**.

- **`app/`**
  - This folder holds all of the files that the **new** application uses. 

---

Happy coding! 🚀