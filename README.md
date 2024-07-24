# ZeusVision: Drone Surveillance System with Enhanced YOLO Object Detection

## Overview

ZeusVision is an innovative drone surveillance system designed to revolutionize the way we approach security and monitoring tasks. By integrating a mobile device onto a drone, ZeusVision captures live footage, transmitting it to a computer for real-time object detection and analysis. Utilizing the advanced capabilities of the YOLO (You Only Look Once) algorithm, our system offers unprecedented accuracy and speed in identifying various objects within the drone's visual field. This project is inspired by the need for more agile and intelligent surveillance systems in both civilian and military applications.

## Key Features

- **Real-Time Object Detection**: Leverages the latest YOLO algorithms for fast and accurate object detection.
- **Mobile Integration**: Utilizes a mobile device mounted on the drone for efficient live video capture and transmission.
- **Enhanced Surveillance**: Offers a versatile solution for monitoring public spaces, critical infrastructure, and private properties.
- **YOLO Improvements**: Incorporates modifications to the traditional YOLO architecture, including adjustments for better performance with drone-captured imagery.

## Installation

### Prerequisites

- Python 3.8 or later
- PyTorch 1.7.1
- OpenCV 4.5
- A DJI drone with a mobile device mounting capability that supports MSDK V5, 
- A computer for processing the live feed

### Setup

1. Clone this repository to your local machine.
2. Install the required Python packages: `pip install -r requirements.txt`
3. Ensure your drone's mobile device has an app capable of transmitting live video to a designated IP address.
4. Run the `zeusvision.py` script on your computer to start analyzing the incoming video stream.

## Usage

1. Mount the mobile device securely onto the drone.
2. Start the video transmission app on the mobile device.
3. Launch `zeusvision.py` with the appropriate IP configuration: `python zeusvision.py --ip <IP_ADDRESS>`
4. Deploy the drone to your area of interest. ZeusVision will begin processing the live feed, detecting and reporting objects in real-time.

## Customization

ZeusVision allows for customization of the object detection process. Users can modify the `config.yml` file to adjust detection parameters, including confidence thresholds and specific object classes to track. For advanced users, there's the option to retrain the YOLO model with custom datasets, enabling detection of unique objects relevant to specific surveillance needs.

## Contributions

We welcome contributions from the community. Whether it's improving the code, adding new features, or expanding our dataset, your input is invaluable. Please see our `CONTRIBUTING.md` for guidelines on how to make a contribution.


## Acknowledgments

Our project benefits from the work and research conducted in the fields of computer vision and drone technology. We extend our gratitude to the creators of the YOLO algorithm and the developers.
