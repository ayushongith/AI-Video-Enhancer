# AI Video Enhancer

A professional video enhancement tool with AI-powered upscaling, frame interpolation, and denoising.

## Requirements

- Python 3.11+
- FFmpeg (must be installed and available on system PATH)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Project Structure

- `app/gui/` - GUI components
- `app/core/` - Core functionality (video loading, FFmpeg detection)
- `app/utils/` - Utilities (config, logging, constants)
- `app/workers/` - Background workers
- `outputs/` - Processed video output directory
- `temp/` - Temporary file storage
- `logs/` - Application logs
