# Video Library Search with Video Clip Query

This project, developed as part of the CSCI 576 Multimedia Systems course at USC (Fall 2023), focuses on creating a system to search and index videos and audio snippets. The system allows users to query a database of videos using a short video snippet with synchronized audio and retrieves the exact match along with its starting position in the database video.

## Project Objective

To implement a system that:
1. Preprocesses database videos to compute digital signatures for efficient searching.
2. Matches a query video (with synchronized audio) to a database video.
3. Displays the match in a custom video player with functionalities like **Play**, **Pause**, and **Reset**.

## Key Features

- **Digital Signature Generation**:
  - Extracts features such as:
    - **Shot Boundaries**: Detects scene transitions for faster indexed searches.
    - **Color Information**: Analyzes dominant color patterns.
    - **Motion Statistics**: Measures movement in frames.
    - **Audio Analysis**: Quantifies sound frequency and amplitude.

- **Signature Matching**:
  - Matches query signatures to database signatures using efficient pattern-matching techniques.

- **Custom Video Player**:
  - Displays the matched video with synchronized audio.
  - Supports Play, Pause, and Reset functionalities.
  - Automatically starts at the matched frame.

## Workflow

1. **Preprocessing**:
   - Generate digital signatures for all database videos.
   - Create sub-signatures for query videos.

2. **Matching**:
   - Compare the query sub-signature with database signatures.
   - Identify the best match based on calculated similarity metrics.

3. **Display**:
   - Render the matched video and navigate to the exact frame offset where the query video starts.

## Usage

The project can be executed using the following command:
```bash
MyProject.exe QueryVideo.rgb QueryAudio.wav
