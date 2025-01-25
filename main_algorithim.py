#!/usr/bin/env python3

import warnings
import sys
import os
import cv2
import imagehash
import numpy as np
from PIL import Image
import time
import librosa
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import pickle
from gui import play_video 

warnings.filterwarnings("ignore")

current_directory = os.path.dirname(os.path.abspath(__file__))
# Get the path to the preprocessing directory
preprocessing_directory = os.path.join(current_directory, 'preprocessing')

def calculate_histogram(frame):
	"""Calculate the color histogram for a frame."""
	hist = cv2.calcHist([frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
	hist = cv2.normalize(hist, hist).flatten()
	return hist

def hamming_distance(hash1, hash2):
	# Assuming hash1 and hash2 are binary strings
	xor_result = int(hash1, 2) ^ int(hash2, 2)  # Convert to integers and XOR
	return bin(xor_result).count('1')  # Count the number of 1s

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

def format_timestamp(start_timestamp):
	minutes = int(start_timestamp/60)
	if minutes < 10:
		minutes = f"0{int(start_timestamp/60)}"
	seconds = int(start_timestamp%60)
	if seconds < 10:
		seconds = f"0{int(start_timestamp%60)}"
	return f"{minutes}:{seconds}"

def histogram_similarity(hist1, hist2):
	"""Calculate similarity between two histograms."""
	return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

def get_filename(file_path):
	# Extract the base name (e.g., 'file.ext' from '/path/to/file.ext')
	base_name = os.path.basename(file_path)
	
	# Split the base name into name and extension and return just the name
	file_name = os.path.splitext(base_name)[0]
	
	return file_name

def get_filepath_without_extension(file_path):
	# Split the file path into the path without the extension and the extension
	path_without_extension, _ = os.path.splitext(file_path)
	
	return path_without_extension

def extract_key_frames_v2(clip_video_path):
	clip_video = cv2.VideoCapture(clip_video_path)
	key_frames = []
	indices = []
	
	total_frames = round(clip_video.get(cv2.CAP_PROP_FRAME_COUNT))
	frame_step = total_frames // 120
	current_frame_index = 0
	
	while current_frame_index < total_frames:
		ret, frame = clip_video.read()
		if not ret:
			break
		
		if current_frame_index % frame_step == 0 or current_frame_index == 0:
			key_frames.append(frame)
			indices.append(current_frame_index)
			
		current_frame_index += 1
		
	clip_video.release()
	return key_frames, indices


def get_frame_count(video_path):
	# Create a VideoCapture object
	cap = cv2.VideoCapture(video_path)
	
	# Check if video opened successfully
	if not cap.isOpened():
		print("Error: Could not open video.")
		return None
	
	# Get the number of frames in the video
	frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
	
	# Release the VideoCapture object
	cap.release()
	
	return frame_count


def compare_rgb_data_first_frame(rgb_data1, rgb_data2):
	"""
	Compares the first frame of two sets of RGB data and checks for an exact match.

	Args:
	rgb_data1, rgb_data2 (List of bytes): Two lists containing RGB data for comparison.

	Returns:
	bool: True if the first frames are exactly the same, False otherwise.
	"""
	if not rgb_data1 or not rgb_data2:
		return False  # One of the lists is empty
	
	return rgb_data1[0] == rgb_data2[0]

def extract_rgb_data(video_path, start_frame, end_frame, frame_width, frame_height):
	"""
	Extracts RGB data from a video file for a specified range of frames.

	Args:
	video_path (str): Path to the video file.
	start_frame (int): The starting frame number.
	end_frame (int): The ending frame number.
	frame_width (int): The width of a frame in pixels.
	frame_height (int): The height of a frame in pixels.

	Returns:
	List of tuples: A list where each element is a tuple representing the RGB data of a frame.
	"""
	frame_data = []
	bytes_per_frame = frame_width * frame_height * 3  # 3 bytes per pixel (RGB)
	
	with open(video_path, 'rb') as file:
		file.seek(start_frame * bytes_per_frame)  # Jump to the start frame
		for _ in range(start_frame, end_frame):
			frame_bytes = file.read(bytes_per_frame)
			if not frame_bytes:
				break  # End of file
			frame_data.append(frame_bytes)
			
	return frame_data

def find_best_match_per_video(clip_hashes, video_hashes):
	# profiler = cProfile.Profile()
	# profiler.enable()
	best_matches = []
	
	for video_path, segment_hashes in video_hashes.items():
		min_distance = float('inf')
		for clip_hash in clip_hashes:
			for segment_hash in segment_hashes:
				distance = hamming_distance(clip_hash, segment_hash)
				if distance < min_distance:
					min_distance = distance
				if distance < 5:
					break
				
		best_matches.append((video_path, min_distance))
		
		# Sort the list by distance (second item of the tuple), from smallest to largest
	sorted_best_matches = sorted(best_matches, key=lambda x: x[1])
	# profiler.disable()
	# stats = pstats.Stats(profiler).sort_stats('cumtime')
	# stats.print_stats()
	return sorted_best_matches


def find_clip_start(main_video_path, clip_video_path, main_video_rgb, clip_video_rgb, shot_boundaries, frame_histograms, frame_threshold, use_rgb_verification):
	# Gets key frames for clip and its histograms
	start_time = time.time()
	key_frames, key_frame_indices = extract_key_frames_v2(clip_video_path)
	end_time = time.time()
	computation_time = end_time - start_time  # Calculate the total time taken
	print(f"Key frames extracted in {computation_time:.2f} seconds")
	start_time = time.time()
	key_frame_histograms = [calculate_histogram(frame) for frame in key_frames]
	end_time = time.time()
	computation_time = end_time - start_time  # Calculate the total time taken
	print(f"Calculated histograms in {computation_time:.2f} seconds")
	average_hist = sum(key_frame_histograms)/len(key_frame_histograms)
	clip_hist = key_frame_histograms[0]
	#find the shot boundary that the clip is within
	similarity_rankings = []
	start_time = time.time()
	for boundary in shot_boundaries:
		frame_hist = frame_histograms[boundary]
		similarity = histogram_similarity(average_hist, frame_hist)
		similarity_rankings.append((boundary, similarity))
		# Sort shot boundaries by similarity, in descending order
	similarity_rankings.sort(key=lambda x: x[1], reverse=True)
	# Narrow down to exact frame within the identified shot segment
	candidates = []
	end_time = time.time()
	for boundary, similarity in similarity_rankings:
		boundary_index = shot_boundaries.index(boundary)
		start_index = shot_boundaries[boundary_index] + 1 if boundary_index > 0 else 0
		end_index = shot_boundaries[boundary_index + 1] if boundary_index < len(shot_boundaries) - 1 else len(frame_histograms) - 1
		
		# Initialize the average similarity calculation
		best_similarity = 0
		start_best_index = -1
		# Compare each key frame within the identified segment
		for i in range(start_index, end_index + 1):
			total_similarity = 0
			average_similarity = 0
			frame_count = 0
			# Calculates average similarity for every key frame in this position
			for j, key_frame_hist in enumerate(key_frame_histograms):
				if i+key_frame_indices[j] >= len(frame_histograms):
					break
				frame_hist = frame_histograms[i+key_frame_indices[j]]
				similarity = histogram_similarity(key_frame_hist, frame_hist)
				if similarity > frame_threshold:
					total_similarity += similarity
					frame_count += 1
				else:
					break
				
				# Only calculates average if every frame had a similarity score above frame_threshold
			if frame_count == len(key_frame_histograms):
				average_similarity = total_similarity / frame_count
				candidates.append( {'index': i, 'similarity': average_similarity})
				
				# The best average similarity is the one we keep
			if average_similarity > best_similarity and not use_rgb_verification:
				best_similarity = average_similarity
				start_best_index = i
				
		# RGB verification
		#print(candidates)
		if best_similarity > 0 and not use_rgb_verification:
			return start_best_index
		if not candidates:
			continue
		candidates = sorted(candidates, key=lambda x: x['similarity'], reverse=True)
		if use_rgb_verification:
			for candidate in candidates:
				# Extract RGB data for the first frame of the candidate segment from the main video
				main_video_rgb_first_frame = extract_rgb_data(main_video_rgb, candidate['index'], candidate['index'] + 1, 352, 288)
				
				# Extract RGB data for the first frame of the query clip
				clip_rgb_first_frame = extract_rgb_data(clip_video_rgb, 0, 1, 352, 288)
				
				# Check if the first frames are identical
				if compare_rgb_data_first_frame(main_video_rgb_first_frame, clip_rgb_first_frame):
					print("Found exact match")
					start_best_index = candidate['index']
					return start_best_index
				
	return start_best_index

def process_video(video, clip_path, clip_rgb, shot_boundaries_dict, frame_histograms_dict, frame_threshold, found_match=None):
	if found_match and found_match.is_set():
		return video, -1, None  # Early return if match already found
	
	shot_boundaries = shot_boundaries_dict[video]
	frame_histograms = frame_histograms_dict[video]
	
	path_no_extension = get_filepath_without_extension(video)
	start_frame = find_clip_start(video, clip_path, f"{path_no_extension}.rgb", clip_rgb, shot_boundaries,
		frame_histograms, frame_threshold, use_rgb_verification=True)
	fps = cv2.VideoCapture(video).get(cv2.CAP_PROP_FPS)
	return video, start_frame, fps

def adaptive_video_search(matching_videos, clip_path, clip_rgb, shot_boundaries_dict,
	frame_histograms_dict, frame_threshold, start_time_main, switch_to_parallel_threshold=2):
	found_match = threading.Event()
	
	# Process the first few videos sequentially
	for video in matching_videos[:switch_to_parallel_threshold]:  # Adjust the number as needed
		_, start_frame, fps = process_video(video[0], clip_path, clip_rgb, shot_boundaries_dict, frame_histograms_dict, frame_threshold)
		if start_frame != -1:
			start_timestamp = start_frame / fps
			formated_timestamp = format_timestamp(start_timestamp)
			computation_time = time.time() - start_time_main
			print(f"Match found in {computation_time:.2f} seconds")
			print(f"Clip starts at frame: {start_frame}, in {get_filename(video[0])} which is at timestamp: {formated_timestamp}")
			return video[0], start_frame
		else:
			print(f"Clip not found in the {get_filename(video[0])}. Searching next best...")
		
	# If no match found, proceed with parallel processing
	print("Match not found in first few videos. Switching to parallel processing...")
	with ThreadPoolExecutor(max_workers=4) as executor:
		future_to_video = {executor.submit(process_video, video[0], clip_path, clip_rgb, shot_boundaries_dict, frame_histograms_dict, frame_threshold, found_match): video for video in matching_videos[switch_to_parallel_threshold:]}
		
		for future in as_completed(future_to_video):
			video, start_frame, fps = future.result()
			if start_frame != -1:
				found_match.set()  # Signal that a match has been found
				start_timestamp = start_frame / fps
				formated_timestamp = format_timestamp(start_timestamp)
				computation_time = time.time() - start_time_main
				print(f"Clip starts at frame: {start_frame}, in {get_filename(video)} which is at timestamp: {formated_timestamp}")
				print(f"Match found in {computation_time:.2f} seconds")
				return video, start_frame
			
			
def main(clip_path, clip_rgb):
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
	
	video_hashes_path = os.path.join(preprocessing_directory, 'video_hashes.pkl')
	shot_boundaries_dict_path = os.path.join(preprocessing_directory, 'shot_boundaries_dict.pkl')
	frame_histograms_dict_path = os.path.join(preprocessing_directory, 'frame_histograms_dict.pkl')
	
	with open(video_hashes_path, 'rb') as file:
		video_hashes = pickle.load(file)
		
		# Loading shot_boundaries_dict
	with open(shot_boundaries_dict_path, 'rb') as file:
		shot_boundaries_dict = pickle.load(file)
		
		# Loading frame_histograms_dict
	with open(frame_histograms_dict_path, 'rb') as file:
		frame_histograms_dict = pickle.load(file)
		
	start_time_main = time.time()
	clip_hash = get_video_segment_hashes(clip_path,  segment_length=3)
	matching_videos = find_best_match_per_video(clip_hash, video_hashes)
	end_time = time.time()
	computation_time = end_time - start_time_main  # Calculate the total time taken
	print(f"Video rankings found in {computation_time:.2f} seconds")
	video_path, start_frame = adaptive_video_search(matching_videos, clip_path, clip_rgb, shot_boundaries_dict, frame_histograms_dict, start_time_main=start_time_main, frame_threshold=0.95)
	print("\n")
	
	if video_path is not None and start_frame != -1:
		# Call the function from the second script
		play_video(video_path, start_frame)
	
	
if __name__ == "__main__":
	if len(sys.argv) > 2:
		main(sys.argv[1], sys.argv[2])
	else:
		print("This script requires at least 2 arguments (clip.mp4 clip.rgb).")
		