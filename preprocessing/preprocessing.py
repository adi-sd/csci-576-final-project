import warnings
import os
import cv2
import imagehash
import numpy as np
from PIL import Image
import time
import librosa
import pickle
import h5py

warnings.filterwarnings("ignore")

def calculate_histogram(frame):
	"""Calculate the color histogram for a frame."""
	hist = cv2.calcHist([frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
	hist = cv2.normalize(hist, hist).flatten()
	return hist

def histogram_similarity(hist1, hist2):
	"""Calculate similarity between two histograms."""
	return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

def get_video_segment_hashes(video_path, segment_length=3, overlap_fraction=0.3):
	# profiler = cProfile.Profile()
	# profiler.enable()
	start_time = time.time()
	cap = cv2.VideoCapture(video_path)
	video_fps = cap.get(cv2.CAP_PROP_FPS)
	segment_frames = int(video_fps * segment_length)
	overlap_frames = int(segment_frames * overlap_fraction)  # Calculate the number of frames to overlap
	hashes = []
	
	frame_count = 0
	frames = []
	
	while True:
		ret, frame = cap.read()
		if not ret:
			break
		
		frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
		
		if frame_count % segment_frames == 0 and frame_count != 0:
			# Process the segment
			avg_frame = np.mean(np.array(frames), axis=0).astype(np.uint8)
			frame_hash = imagehash.phash(Image.fromarray(avg_frame))
			bin_str = format(int(str(frame_hash), 16), '064b')
			hashes.append(bin_str)
			
			# Keep the last 'overlap_frames' for the next segment
			frames = frames[-overlap_frames:]
			
		frame_count += 1
		
		# Process the last segment
	if frames:
		avg_frame = np.mean(np.array(frames), axis=0).astype(np.uint8)
		frame_hash = imagehash.phash(Image.fromarray(avg_frame))
		bin_str = format(int(str(frame_hash), 16), '064b')
		hashes.append(bin_str)
		
	cap.release()
	end_time = time.time()
	computation_time = end_time - start_time  # Calculate the total time taken
	print(f"Hashes for {video_path} calculated in {computation_time:.2f} seconds")
	# profiler.disable()
	# stats = pstats.Stats(profiler).sort_stats('cumtime')
	# stats.print_stats()
	return hashes


def detect_shot_boundaries(video_path, threshold=0.5):
	start_time = time.time()
	video = cv2.VideoCapture(video_path)
	shot_boundaries = []
	frame_histograms = []
	ret, prev_frame = video.read()
	if not ret:
		print("Failed to read the first frame.")
		return shot_boundaries, frame_histograms
	
	prev_hist = calculate_histogram(prev_frame)
	frame_histograms.append(prev_hist)
	
	while True:
		ret, frame = video.read()
		if not ret:
			break
		
		frame_hist = calculate_histogram(frame)
		frame_histograms.append(frame_hist)
		similarity = histogram_similarity(prev_hist, frame_hist)
		if similarity < threshold:
			shot_boundary = int(video.get(cv2.CAP_PROP_POS_FRAMES) - 1)
			shot_boundaries.append(shot_boundary)
			
		prev_hist = frame_hist
		#includes first frame if no shot boundaries found
	video.release()
	video = cv2.VideoCapture(video_path)
	if not shot_boundaries:
		print("No main video shot boundaries")
		video.set(cv2.CAP_PROP_POS_FRAMES, 0)
		ret, first_frame = video.read()
		if ret:
			shot_boundary = round(video.get(cv2.CAP_PROP_POS_FRAMES))
			shot_boundaries.append(shot_boundary)
	video.release()
	end_time = time.time()
	computation_time = end_time - start_time  # Calculate the total time taken
	print(f"Boundaries for {video_path} calculated in {computation_time:.2f} seconds")
	return shot_boundaries, frame_histograms


def main():
	database = ['/Users/arshiabehzad/Downloads/Videos/video1.mp4',
		'/Users/arshiabehzad/Downloads/Videos/video2.mp4',
		'/Users/arshiabehzad/Downloads/Videos/video3.mp4',
		'/Users/arshiabehzad/Downloads/Videos/video4.mp4',
		'/Users/arshiabehzad/Downloads/Videos/video5.mp4',
		'/Users/arshiabehzad/Downloads/Videos/video6.mp4',
		'/Users/arshiabehzad/Downloads/Videos/video7.mp4',
		'/Users/arshiabehzad/Downloads/Videos/video8.mp4',
		'/Users/arshiabehzad/Downloads/Videos/video9.mp4',
		'/Users/arshiabehzad/Downloads/Videos/video10.mp4',
		'/Users/arshiabehzad/Downloads/Videos/video11.mp4',
		'/Users/arshiabehzad/Downloads/Videos/video12.mp4',
		'/Users/arshiabehzad/Downloads/Videos/video13.mp4',
		'/Users/arshiabehzad/Downloads/Videos/video14.mp4',
		'/Users/arshiabehzad/Downloads/Videos/video15.mp4',
		'/Users/arshiabehzad/Downloads/Videos/video16.mp4',
		'/Users/arshiabehzad/Downloads/Videos/video17.mp4',
		'/Users/arshiabehzad/Downloads/Videos/video18.mp4',
		'/Users/arshiabehzad/Downloads/Videos/video19.mp4',
		'/Users/arshiabehzad/Downloads/Videos/video20.mp4']
	video_hashes = {video_path: get_video_segment_hashes(video_path) for video_path in database}
	shot_boundaries_dict = {}
	frame_histograms_dict = {}
	for video in database:
		shot_boundaries, frame_histograms = detect_shot_boundaries(video, threshold=0.50)
		shot_boundaries_dict[video] = shot_boundaries
		frame_histograms_dict[video] = frame_histograms
		
		# Saving video hashes using Pickle
	with open('video_hashes.pkl', 'wb') as file:
		pickle.dump(video_hashes, file)
		
		# Saving shot boundaries and frame histograms using HDF5
	with open('shot_boundaries_dict.pkl', 'wb') as file:
		pickle.dump(shot_boundaries_dict, file)
		
		# Saving frame_histograms_dict
	with open('frame_histograms_dict.pkl', 'wb') as file:
		pickle.dump(frame_histograms_dict, file)
		
		
if __name__ == "__main__":
	main()