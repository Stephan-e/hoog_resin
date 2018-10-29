import io
import time
from time import strftime, sleep
import picamera
from base_camera import BaseCamera

lastfile = "static/1"


def save_image():
    timestr = time.strftime("%Y%m%d-%H%M%S")
    lastfile = "static/snap_" + timestr + ".jpg"
    camera = picamera.PiCamera()
    camera.resolution = (640, 480)
    camera.start_preview()
    sleep(2)
    camera.capture(lastfile)
    camera.stop_preview()
    camera.close()

    return(lastfile)


# class Camera(BaseCamera):
#     @staticmethod
#     def frames():
#         with picamera.PiCamera() as camera:
#             # let camera warm up
#             time.sleep(2)

#             stream = io.BytesIO()
#             for _ in camera.capture_continuous(stream, 'jpeg',
#                                                  use_video_port=True):
#                 # return current frame
#                 stream.seek(0)
#                 yield stream.read()

#                 # reset stream for next frame
#                 stream.seek(0)
#                 stream.truncate()