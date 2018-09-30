"""A module for camera calibration using a chessboard."""

import json
import numpy as np
import cv2
from event import Event

MIN_CALIBRATION_FRAMES = 20

class CameraCalibration():
    """This class performs camera calibration."""

    def __init__(self):
        self.chessboard_size = (9, 6)
        self.record_min_num_frames = MIN_CALIBRATION_FRAMES
        self.record_cnt = 0
        self._recording = False
        self._mean_error = 0
        self._is_calibrated = False
        self._camera_matrix = None
        self._dist_coeff = None
        self._calibration_file = None

        # events
        self.calibrated = Event()
        self.on_progress = Event()

        # arrays to store object points and image points from all the images
        self.obj_points = []
        self.img_points = []

        # prepare object points
        self.objp = np.zeros((np.prod(self.chessboard_size), 3), dtype=np.float32)
        self.objp[:, :2] = np.mgrid[0:self.chessboard_size[0],
                                    0:self.chessboard_size[1]].T.reshape(-1, 2)

    @property
    def mean_error(self):
        """Mean re-projection error."""
        return self._mean_error

    @property
    def is_calibrated(self):
        """True if calibrated, False otherwise."""
        return self._is_calibrated

    @property
    def camera_matrix(self):
        """Intrinsic camera matrix."""
        return self._camera_matrix

    @property
    def dist_coeff(self):
        """Distortion vector."""
        return self._dist_coeff

    @property
    def calibration_file(self):
        """Calibration file."""
        return self._calibration_file

    @property
    def is_calibrating(self):
        """Flag is True if calibration is in progress."""
        return self._recording

    @property
    def can_undistort(self):
        """Flag is True if an image can be undistorted using calibration parameters."""
        return self.is_calibrated and not self._recording

    def reset_recording(self):
        """Disable recording mode and reset data structures."""
        self.record_cnt = 0
        self.obj_points = []
        self.img_points = []

    def start_calibration(self):
        """Start camera calibration process."""
        self.reset_recording()
        self._recording = True
        self._is_calibrated = False
        self._calibration_file = None

    def cancel_calibration(self):
        """Cancel camera calibration process."""
        self._recording = False
        self._is_calibrated = False
        self.reset_recording()

    def calibrate(self, frame):
        """Processes each frame.

        Args:
            frame (image): input image: 8-bit unsigned, 16-bit unsigned,
            or single-precision floating-point.
        """
        if not self._recording:
            return

        if self.record_cnt < self.record_min_num_frames:

            img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.uint8)
            ret, corners = cv2.findChessboardCorners(img_gray, self.chessboard_size, None)
            if ret:
                cv2.drawChessboardCorners(frame, self.chessboard_size, corners, ret)

                # refine found corners.
                # process of corner position refinement stops either after
				# criteria maxCount iterations or when the corner position moves
				# by less than criteria epsilon on some iteration.
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                cv2.cornerSubPix(img_gray, corners, (9, 9), (-1, -1), criteria)

                self.obj_points.append(self.objp)
                self.img_points.append(corners)
                self.record_cnt += 1

                # report progress
                message = "%d of %d frames" % (self.record_cnt, self.record_min_num_frames)
                self.on_progress(message)
        else:
            # calculate the intrinsic camera matrix (k) and the distortion vector (dist)
            self._recording = False
            image_height, image_width = frame.shape[:2]

            # get the camera matrix, distortion coefficients, rotation and translation vectors
            ret, k, dist, rvecs, tvecs = cv2.calibrateCamera(
                self.obj_points, self.img_points,
                (image_height, image_width),
                None, None)

            self._camera_matrix = k
            self._dist_coeff = dist

            # calculate re-projection error.
            # this should be as close to zero as possible.
            self._mean_error = 0

            for i in range(len(self.obj_points)):
                # transform the object points to image points.
                img_points2, _ = cv2.projectPoints(self.obj_points[i], rvecs[i], tvecs[i], k, dist)

                # calculate the absolute norm between what we got with our transformation
                # and the corner finding algorithm.
                error = cv2.norm(self.img_points[i], img_points2, cv2.NORM_L2) / len(img_points2)
                self._mean_error += error

            self._is_calibrated = True
            self.reset_recording()
            self.calibrated()

    def undistort(self, frame):
        """Undistort a frame.

        Args:
            frame (image): input image: 8-bit unsigned, 16-bit unsigned,
            or single-precision floating-point.
        Returns:
            undistorted frame of the same size as the original one.
        """
        if not self._is_calibrated:
            return frame

        # undistort
        height, width = frame.shape[:2]
        size = (width, height)
        new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
            self._camera_matrix, self._dist_coeff, size, 1, size)
        dst = cv2.undistort(frame, self._camera_matrix, self._dist_coeff, None, new_camera_matrix)

        # crop the image
        x, y, w, h = roi
        dst = dst[y:y+h, x:x+w]
        new_image = np.zeros((height, width, 3), np.uint8)
        new_image[y:y+h, x:x+w] = dst
        return new_image

    def save_calibration(self, pathname):
        """Save camera calibration parameters in json file."""
        data = {
            "camera_matrix": self._camera_matrix.tolist(),
            "dist_coeff": self._dist_coeff.tolist(),
            "mean_error": self._mean_error
            }
        with open(pathname, "w") as file:
            json.dump(data, file)
            self._calibration_file = pathname

    def load_calibration(self, pathname):
        """Load camera calibration parameters from a file."""
        self._calibration_file = None
        with open(pathname, "r") as file:
            data = json.load(file)
            self._camera_matrix = np.array(data['camera_matrix'])
            self._dist_coeff = np.array(data['dist_coeff'])
            self._mean_error = data['mean_error']
            self._calibration_file = pathname
            self._is_calibrated = True
