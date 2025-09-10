import os
from supabase.client import Client, create_client
from langchain_google_community import GoogleDriveLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.document_loaders import Docx2txtLoader, TextLoader
from dotenv import load_dotenv
from rag.drive_utils import download_file
import base64
load_dotenv()
import mimetypes
import speech_recognition as sr
import io
from pydub import AudioSegment
import noisereduce as nr
import librosa
import soundfile as sf
import tempfile
from moviepy.video.io import VideoFileClip


supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

def chunk_text(text, chunk_size=1000, overlap=200):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        # move the start forward but keep some overlap
        start += chunk_size - overlap

    return chunks

def load_documents():
    loader = GoogleDriveLoader(
        credentials_path="/home/ricko/ai-drive/rag/credentials/credentials.json",
        token_path="/home/ricko/ai-drive/rag/credentials/token.json",
        folder_id="root",
        file_types=["document", "pdf"],
        recursive=True,
        scopes=["https://www.googleapis.com/auth/drive.file"]
    )
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)
    for doc in docs:
        response = (
            supabase.table("documents")
            .insert({"content": doc.page_content})
            .execute()
        )
    print(f"Loaded {len(docs)} documents from Google Drive")

def load_document(file_id, ext=None):
    if ext==".docx":
        doc_byte = download_file(file_id)
        with tempfile.NamedTemporaryFile(suffix=ext) as temp_file:
            temp_file.write(doc_byte)
            temp_file.flush()
            loader = Docx2txtLoader(temp_file.name) 
    
    elif ext==".txt":
        doc_byte = download_file(file_id)
        with tempfile.NamedTemporaryFile(suffix=ext) as temp_file:
            temp_file.write(doc_byte)
            temp_file.flush()
            loader = TextLoader(temp_file.name, encoding="utf-8")
    else:
        loader = GoogleDriveLoader(
            credentials_path="/home/ricko/ai-drive/rag/credentials/credentials.json",
            token_path="/home/ricko/ai-drive/rag/credentials/token.json",
            file_ids=[file_id],
            scopes=["https://www.googleapis.com/auth/drive.file"]
        )
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)
    for doc in docs:
        response = (
            supabase.table("documents")
            .insert({"content": doc.page_content})
            .execute()
        )
    print(f"Loaded {len(docs)} documents from Google Drive")
    

def load_image(file_id, extension=".png"):
    file = download_file(file_id)
    base64_str = base64.b64encode(file).decode("utf-8")
    
    data_uri = f"data:image/{extension.split('.')[-1]};base64,{base64_str}"
    response = (
            supabase.table("documents")
            .insert({"content": data_uri})
            .execute()
        )
    print("Image loaded to database")

def audio_bytes_to_wav_bytes(audio_bytes: bytes) -> bytes:
    """
    Convert any audio format (mp3, wav, ogg, m4a, etc.) to 16kHz PCM WAV bytes.
    Requires ffmpeg or avlib installed.
    """
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    audio = audio.set_frame_rate(16000).set_channels(1)  # standard for ASR

    out_buffer = io.BytesIO()
    audio.export(out_buffer, format="wav")
    return out_buffer.getvalue()

def denoise_wav_bytes(wav_bytes: bytes) -> bytes:
    """Apply noise reduction to WAV bytes."""
    y, sr = librosa.load(io.BytesIO(wav_bytes), sr=None, mono=True)
    y_clean = nr.reduce_noise(y=y, sr=sr)
    out_buffer = io.BytesIO()
    sf.write(out_buffer, y_clean, sr, format="WAV", subtype="PCM_16")
    return out_buffer.getvalue()

def load_audio(file_id, ext, denoise=True):
    file = download_file(file_id)
    if ext != ".wav":
        file = audio_bytes_to_wav_bytes(file)                 # raw audio bytes (any format)
    if denoise:
        file = denoise_wav_bytes(file)            # optional noise reduction
    
    recognizer = sr.Recognizer()
    audio_file = io.BytesIO(file)

    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)

        try:
            text = recognizer.recognize_google(audio_data)
            print("Transcription: ", text)
        except sr.UnknownValueError:
            print("Speech recognition could not understand the audio.")
            return None
        except sr.RequestError as e:
            print(f"Could not request results from service; {e}")
            return None
    
    # Chunk & save to DB
    chunks = chunk_text(text)
    for chunk in chunks:
        supabase.table("documents").insert({"content": chunk}).execute()
    
    print(f"Loaded {len(chunks)} text chunks from audio file to database")


def load_videos(file_id, extension=".mp4"):
    video_bytes = download_file(file_id)
    with tempfile.NamedTemporaryFile(suffix=extension) as temp_file:
    # Write bytes to the temp file
        temp_file.write(video_bytes)
        temp_file.flush()  # ensure all data is written

        # Load into MoviePy
        clip = VideoFileClip(temp_file.name)
        print("Duration (s):", clip.duration)
        
        # Example: extract audio
        print("Extracting audio...")
        audio = clip.audio
        with tempfile.NamedTemporaryFile(suffix=".wav") as audio_file:
            audio.write_audiofile(audio_file.name)
            audio_file.flush()
            # Process audio bytes directly
            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_file.name) as source:
                audio_data = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio_data)
                    chunks = chunk_text(text)
                    for chunk in chunks:
                        supabase.table("documents").insert({"content": chunk}).execute()
                except (sr.UnknownValueError, sr.RequestError) as e:
                    print(f"Audio processing error: {e}")

        print("Extratings frames...")
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write frames to temp directory
            clip.write_images_sequence(
                os.path.join(tmpdir, "frame%04d.png"),
                fps=0.2  # adjust frame extraction rate
            )
            # Process each frame
            for frame_file in sorted(os.listdir(tmpdir)):
                frame_path = os.path.join(tmpdir, frame_file)
                with open(frame_path, "rb") as ff:
                    frame_bytes = ff.read()
                    base64_str = base64.b64encode(frame_bytes).decode("utf-8")
                    data_uri = f"data:image/png;base64,{base64_str}"
                    supabase.table("documents").insert({"content": data_uri}).execute()

def populate_vector_db(files=None):
    load_documents()

    for file in files or []:
        file_id = file["id"]
        ext = "." + file["name"].split(".")[-1]
        load_any_file(file_id, ext, populate_db=True)



def load_any_file(file_id, ext, populate_db=False):

    if ext in [".png", ".jpg", ".jpeg", ".svg"]:
        load_image(file_id, extension=ext)
    elif ext in [".mp4", ".mov", ".avi", ".mkv"]:
        load_videos(file_id, extension=ext)
    elif ext in [".mp3", ".wav", ".flac", ".aac"]:
        load_audio(file_id, ext=ext, denoise=True)
    elif ext in [".txt", ".pdf", ".docx"]:
        if populate_db:
            if ext in [".txt", ".docx"]:
                load_document(file_id, ext=ext)
        else:
            load_document(file_id, ext=ext)
    else:
        print(f"Unsupported file extension: {ext}")
    




# Example usage - commented out for production
# load_document(file_id="1fh3O1lbu_k9SSHu2WJQHMz2-bGUJsrb4")
