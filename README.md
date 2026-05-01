# acadence-ai-voice-text
An academic tracker application enhanced with AI-powered voice-to-text technology, designed to streamline note-taking, progress monitoring, and task management for students and educators.

### 1. Prerequisites
If you are running from source code, ensure you have the following installed:
- **Python 3.10+**
- **FFmpeg** (Required for Whisper audio processing. Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to your system PATH).
- **PyAudio dependencies** (Windows users may need Visual Studio Build Tools if they face installation errors).

### 2. Installation
Clone the repository and install the required dependencies:
```bash
git clone https://github.com/yourusername/acadence-ai-voice-text.git
cd acadence-ai-voice-text
pip install -r requirements.txt
```

### 3. Whisper Local Model Setup (Crucial for Offline Mode)
Acadence utilizes the `small.en` Whisper model for lightning-fast, highly accurate offline transcription. Before launching the app, you must download this model.

Open your terminal and run this one-time command to download the model into your system cache:
```bash
python -c "import whisper; whisper.load_model('small.en')"
```
*(This will download ~460MB of weights. It only needs to be done once.)*

### 4. Run the Application
Launch the app directly via Python:
```bash
python main.py
```
> **Note:** On your first launch, Acadence will automatically generate a highly secure, local `database/acadence.db` file containing the default `admin` user.

---

## How to use the Voice AI

1. Navigate to any Subject's View.
2. Click the **Voice AI** button in the top right.
3. Wait for the status indicator to say `🟢 Listening...`
4. Speak naturally. For example:
> *"Ethics subject with a subject code 'GEED-008'"*
5. Click **Process**.
6. Acadence will parse your audio, automatically title-case the fields, add a subject description and insert it into your database.

---

## 📦 Building the Executable (.exe)

If you wish to distribute Acadence as a standalone Windows application to users who don't have Python installed, use the included build script:

```bash
python build_exe.py
```
This script leverages `PyInstaller` to bundle the entire Python runtime, CustomTkinter assets, SQLite schemas, and the PyTorch engine into a single folder.

1. Wait 5-15 minutes for the compilation to finish.
2. Navigate to the generated `dist/Acadence` folder.
3. Double-click `Acadence.exe` to launch the app natively!
