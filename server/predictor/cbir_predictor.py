import cv2
import numpy as np

from app.utils.encoding import nparraybytes_to_nparray, nparray_to_nparraybytes

NMATCHES = 5
MODEL_VERSION = "cbir_v1"
MAX_IMG_WIDTH = 512
CV_LOAD_IMAGE_GRAYSCALE = 0
MAX_FEATURES = 450
MATCH_DISTANCE_THRESHOLD = 137
MATCHER = "flann"  # or "bf"


class InvalidImageException(Exception):
    pass


class CBIRPredictor:
    """
    This class defines how the Content Based Image Retrieval predictor:
    1. Processes the image
    2. Finds descriptors
    3. Calculates distances from each image based on descriptors
    """
    def __init__(self):
        self.init_matcher(MATCHER)
        self.orb = cv2.ORB_create(MAX_FEATURES)

    def init_matcher(self, matcher):
        if matcher == "bf":
            self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        elif matcher == "flann":
            index_params = {
                'algorithm': 6,
                'table_number': 1,
                'key_size': 10,
                'multi_probe_level': 1
            }
            search_params = {'checks': 50}
            self.matcher = cv2.FlannBasedMatcher(index_params, search_params)


    def get_model_version(self):
        return MODEL_VERSION

    def process_image(self, fbytes_image):
        """
        The input image needs to be the right format, colour and size
        JPEG compression is left for the app
        """
        img_arr = np.frombuffer(fbytes_image, np.uint8)
        img = cv2.imdecode(img_arr, CV_LOAD_IMAGE_GRAYSCALE)
        if img is None:
            raise InvalidImageException()

        # resizing required for the predictor
        w = img.shape[1]
        h = img.shape[0]
        ratio = w / MAX_IMG_WIDTH
        if ratio > 1:
            w = int(w / ratio)
            h = int(h / ratio)
        dim = (w, h)
        resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
        return resized

    def generate_descriptors(self, img):
        """
        Obtains keypoints and their descriptors for an image
        """
        _, des = self.orb.detectAndCompute(img, None)
        if des is None:
            raise InvalidImageException()
        return des

    def calc_record_distances(self, des, routes_and_images, nmatches):
        """
        Obtains match distances for the query image with all available descriptors
        """
        for i in routes_and_images:
            i_descriptors = nparraybytes_to_nparray(i['route_image'].descriptors)
            matches = self.matcher.match(des, i_descriptors)
            matches = sorted(matches, key=lambda x: x.distance)
            # TODO: should check that we have NMATCHES to start with
            dist = sum([x.distance for x in matches[:nmatches]])
            i['distance'] = dist
        return routes_and_images

    def predict_route(self, fbytes_image, routes_and_images, top_n_categories):
        """Makes a route predictions for a single image"""
        img = self.process_image(fbytes_image)
        des = self.generate_descriptors(img)
        routes_and_images = self.calc_record_distances(des, routes_and_images, NMATCHES)
        prediction = CBIRPrediction(des, top_n_categories, routes_and_images)
        return prediction


class CBIRPrediction:
    """
    This class defines individual prediction made by CBIRPredictor for a provided image
    """
    def __init__(self, des, top_n_categories, routes_and_images):
        self.des = des
        self.top_n_predictions = self.find_top_predictions(routes_and_images, top_n_categories)

    def find_top_predictions(self, routes_and_images, top_n_categories):
        """
        Using distances from each descriptor array, finds n route_id's that match best
        """

        def filter_non_matches(routes_and_images):
            return [r for r in routes_and_images if r['distance'] <= MATCH_DISTANCE_THRESHOLD]

        def distinct_with_order(seq):
            """ Distinct elements in list preserving order """
            seen = set()
            seen_add = seen.add
            return [x for x in seq if not (x['route'].id in seen or seen_add(x['route'].id))]

        routes_and_images_filtered = filter_non_matches(routes_and_images)
        routes_and_images_sorted = sorted(routes_and_images_filtered, key=lambda x: x['distance'])
        distinct_prediction_route_images = distinct_with_order(routes_and_images_sorted)
        top_n_route_images = distinct_prediction_route_images[:top_n_categories]
        return top_n_route_images

    def get_predicted_routes_and_images(self):
        return self.top_n_predictions

    def descriptor_bytes(self):
        return nparray_to_nparraybytes(self.des)
