import cv2
import numpy as np

class InvalidImageException(Exception):
    pass

class ResizeImageException(Exception):
    pass


def resize_fbytes_image(fbytes_image, max_width):
    """
    Resizes the image to max_width, keeping the aspect ratio
    JPEG compression is left for the app
    """
    img_arr = np.frombuffer(fbytes_image, np.uint8)
    img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise InvalidImageException()

    w = img.shape[1]
    h = img.shape[0]
    ratio = w / max_width
    if ratio > 1:
        w = int(w / ratio)
        h = int(h / ratio)
    dim = (w, h)
    resized = cv2.resize(img, dim)
    res, resized_buffer = cv2.imencode('.jpg', resized)
    if not res:
        ResizeImageException()

    resized_fbytes_image = resized_buffer.tobytes()
    return resized_fbytes_image
