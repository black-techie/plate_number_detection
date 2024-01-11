import cv2
import os
import time
import threading
import requests


class System:
    def __init__(self):
        self.server_url = "http://192.168.8.244:5555"
        self.model_url = 'https://api.platerecognizer.com/v1/plate-reader/'
        self.servo_pin = 12
        self.sensor_pin = 11
        self.output_directory = "captured_frames"
        os.makedirs(self.output_directory, exist_ok=True)
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.start_time = time.time()
        self.capture_interval = 1.5
        self.print_thread = threading.Thread(target=self.inputs_and_outputs)
        self.print_thread.daemon = True
        self.print_thread.start()


    def capture_frames(self):
        while True:
            ret, frame = self.cap.read()
            cv2.imshow("Video Capture", frame)
            current_time = time.time()
            elapsed_time = current_time - self.start_time
            if elapsed_time >= self.capture_interval:
                frame_file_path = os.path.join(self.output_directory, "frame.jpg")
                cv2.imwrite(frame_file_path, frame)
                self.start_time = current_time
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        self.cap.release()
        cv2.destroyAllWindows()


    def inputs_and_outputs(self):
        while True:
            x = input("enter button state")
            x = int(x)
            if x == 1:
                res = None
                with open(os.path.join(self.output_directory, "frame.jpg"), 'rb') as fp:
                    response = requests.post(
                        self.model_url,
                        files=dict(upload=fp),
                        headers={'Authorization': 'Token 0f4e6a516d971208539d93590731da1e1c967136'})
                    res = response.json()["results"][0]["plate"]
                    print(res)
                api_endpoint = self.server_url + "/api/validate_payment"
                json_data = {"plate_number": res if (res != None or len(res) > 4) else " "}
                response = requests.post(api_endpoint, json=json_data)
                response_data = response.json()
                if "payment" in response_data:
                    print("car payed")
                else:
                    print("car not payed")
            time.sleep(1.5)


if __name__ == "__main__":
    system = System()
    capture_thread = threading.Thread(target=system.capture_frames)
    capture_thread.daemon = True
    capture_thread.start()
    capture_thread.join()
