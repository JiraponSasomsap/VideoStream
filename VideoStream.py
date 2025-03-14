import cv2
import threading
import time

class VideoStream2:
    def __init__(self, source, lock_fps=-1):
        self.source = source
        self.is_running = False
        self.lock_fps = lock_fps

        self.current_frame = None
        self.fps = None
        self.height = None
        self.width = None
        self.frame_count = None

        self._thread = None
        self._cam_connect = False 

    def cam_connect(self):
        self.frame_count = 0
        cap = cv2.VideoCapture(self.source)
        self.fps = int(cap.get(cv2.CAP_PROP_FPS))
        self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

        if cap.isOpened():
            print(f'Connected to source : {self.source}')
            self._cam_connect = True
        else:
            print(f'Failed to connect to source : {self.source}')
            self._cam_connect = False
        return cap

    def _runThread(self):
        cap = self.cam_connect()
        while self.is_running:
            ret, frame = cap.read()
            if ret:
                if self.lock_fps == -1 or self.fps < self.lock_fps:
                    self.current_frame = frame.copy()
                elif self.fps >= self.lock_fps:
                    if self.frame_count % (self.fps//self.lock_fps) == 0:
                        self.current_frame = frame.copy()
                self.frame_count += 1   
            else:
                cap.release()
                print(f'Lost connection to source: {self.source}. Reconnecting...')
                cap = self.cam_connect()
            time.sleep(1/self.fps)
        cap.release()

    @property
    def get(self):
        if not self._cam_connect:
            self.cam_connect()
        if self._cam_connect:
            return _GetVideoStream(self)
        else:
            raise ConnectionError('Camera Connection Error!')
    
    def wait(self):
        while self.current_frame is None:
            pass

    def start(self):
        self.is_running = True
        self._thread = threading.Thread(target=self._runThread, daemon=True)
        self._thread.start()
        self.wait()
        return _GetVideoStream(self)
    
    def stop(self):
        self.is_running = False
    
class _GetVideoStream:
    def __init__(self, instance:VideoStream2):
        self._videoStream = instance
    
    def get_cam_fps(self):
        return self._videoStream.fps
    
    def get_frame_height(self):
        return self._videoStream.height
    
    def get_frame_width(self):
        return self._videoStream.width
    
    def get_frame(self):
        if self._videoStream.current_frame is None:
            return None
        frame = self._videoStream.current_frame.copy()
        self._videoStream.current_frame = None
        return frame

    def get_fps(self):
        if self._videoStream.lock_fps == -1 or self._videoStream.fps < self._videoStream.lock_fps:
            return self._videoStream.fps
        elif self._videoStream.fps >= self._videoStream.lock_fps:
            return self._videoStream.lock_fps 
        
    def get_time_gap(self):
        return 1/self.get_fps()
        
if __name__ == '__main__':
    import numpy as np
    video_source = r"C:\Users\JiraponSasomsap\ArticulusProjects\projects\EGAT\EGAT_Demo\videos\EGAT_test.mp4"
    stream = VideoStream2(video_source, 1)
    streaming = stream.start()
    frame_tmp = None
    while stream.is_running:
        frame = streaming.get_frame()
        if frame is not None:
            frame_tmp = frame
            frame_tmp = cv2.resize(frame_tmp, np.array([frame_tmp.shape[1]*0.5, frame_tmp.shape[0]*0.5], dtype=np.int32))
        
        if frame_tmp is not None:
            cv2.imshow('hello', frame_tmp)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stream.stop()
    cv2.destroyAllWindows()