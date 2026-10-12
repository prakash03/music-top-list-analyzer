# My Global Music Atlas

An interactive Streamlit dashboard for exploring a multilingual music collection across languages, decades, genres, artists, musical characteristics, and listening metrics.

The current dataset contains English, Hindi, Telugu, Tamil, Spanish, and English/Spanish songs.

## Features

- Filter by language, artist country, release year, genre, and explicit content
- Explore songs by energy, danceability, valence, and acousticness
- Compare personal listening across languages and decades
- Analyze popularity versus personal affinity
- Compare selected songs with a musical-profile radar chart
- Explore artists and artist countries
- Search and sort the full song library
- Download the currently filtered dataset as CSV

## Project files

```text
app.py                         Streamlit application
music_visualizer_songs.csv    Source dataset
requirements.txt               Python dependencies
generate_music_dataset.mjs     Dataset-generation script
```

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the application

```bash
streamlit run app.py
```

Streamlit will provide a local browser address, typically:

```text
http://localhost:8501
```

## Dataset columns

The CSV includes song metadata, artist information, language, release year, genre, album, duration, BPM, musical-profile features, personal listening counts, popularity estimates, favorite scores, skip rates, and first-added dates.

The `my_listens` values are synthetic. YouTube and Spotify figures are estimates created for exploratory visualization, not live platform measurements.

## Adding songs

Add rows to `music_visualizer_songs.csv` using the existing column order. Keep numeric fields numeric and use one of the existing language labels, or add a new language label if expanding the collection.

The app reads the CSV when it starts and caches the loaded data. Restart Streamlit after making source-data changes:

```bash
streamlit run app.py
```
