import asyncio
import json
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import wave
import numpy as np
import sounddevice as sd


class AudioRecorder(ABC):
    def __init__(
        self, sample_rate: int = 44100, channels: int = 1, chunk_size: int = 1024
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.is_recording = False
        self.audio_data: list = []
        self.waveform_callback: Optional[Callable[[list], None]] = None
        self.recording_thread: Optional[threading.Thread] = None

    def set_waveform_callback(self, callback: Callable[[list], None]):
        self.waveform_callback = callback

    @abstractmethod
    def _get_device_info(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def _get_stream_params(self) -> Dict[str, Any]:
        pass

    def start_recording(self) -> bool:
        if self.is_recording:
            return False

        try:
            device_info = self._get_device_info()
            if not device_info:
                return False

            self.is_recording = True
            self.audio_data = []
            self.recording_thread = threading.Thread(target=self._record_audio)
            self.recording_thread.start()
            return True
        except Exception as e:
            print(f"Failed to start recording: {e}")
            self.is_recording = False
            return False

    def stop_recording(self) -> bool:
        if not self.is_recording:
            return False

        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join()

        return True

    def save_audio(self, filepath: Path) -> bool:
        if not self.audio_data:
            return False

        try:
            with wave.open(str(filepath), "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)

                audio_array = np.concatenate(self.audio_data)
                audio_int16 = (audio_array * 32767).astype(np.int16)
                wf.writeframes(audio_int16.tobytes())

            return True
        except Exception as e:
            print(f"Failed to save audio: {e}")
            return False

    def _record_audio(self):
        stream_params = self._get_stream_params()

        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio callback status: {status}")

            if self.is_recording:
                self.audio_data.append(indata.copy())

                if self.waveform_callback:
                    waveform_data = self._calculate_waveform(indata)
                    self.waveform_callback(waveform_data)

        try:
            with sd.InputStream(callback=audio_callback, **stream_params):
                while self.is_recording:
                    time.sleep(0.1)
        except Exception as e:
            print(f"Recording error: {e}")
            self.is_recording = False

    def _calculate_waveform(self, audio_chunk: np.ndarray) -> list:
        if len(audio_chunk.shape) > 1:
            audio_chunk = np.mean(audio_chunk, axis=1)

        chunk_size = len(audio_chunk) // 50
        if chunk_size == 0:
            return [0] * 50

        waveform = []
        for i in range(0, len(audio_chunk), chunk_size):
            chunk = audio_chunk[i : i + chunk_size]
            amplitude = np.sqrt(np.mean(chunk**2)) * 100
            waveform.append(min(100, max(0, amplitude)))

        while len(waveform) < 50:
            waveform.append(0)

        return waveform[:50]


class MicrophoneRecorder(AudioRecorder):
    def _get_device_info(self) -> Dict[str, Any]:
        try:
            default_device = sd.query_devices(kind="input")
            return default_device
        except Exception as e:
            print(f"Failed to get microphone device info: {e}")
            return {}

    def _get_stream_params(self) -> Dict[str, Any]:
        return {
            "samplerate": self.sample_rate,
            "channels": self.channels,
            "dtype": np.float32,
            "blocksize": self.chunk_size,
        }


class SystemAudioRecorder(AudioRecorder):
    def _get_device_info(self) -> Dict[str, Any]:
        try:
            devices = sd.query_devices()
            for i, device in enumerate(devices):
                if (
                    "loopback" in device["name"].lower()
                    or "monitor" in device["name"].lower()
                ):
                    return device

            default_device = sd.query_devices(kind="input")
            return default_device
        except Exception as e:
            print(f"Failed to get system audio device info: {e}")
            return {}

    def _get_stream_params(self) -> Dict[str, Any]:
        device_info = self._get_device_info()
        device_index = None

        if device_info:
            devices = sd.query_devices()
            for i, device in enumerate(devices):
                if device["name"] == device_info["name"]:
                    device_index = i
                    break

        return {
            "samplerate": self.sample_rate,
            "channels": self.channels,
            "dtype": np.float32,
            "blocksize": self.chunk_size,
            "device": device_index,
        }


class AudioRecordingManager:
    def __init__(self):
        self.recorders: Dict[str, AudioRecorder] = {}
        self.websocket_connections: Dict[str, set] = {}

    def create_recorder(self, recorder_type: str, recorder_id: str) -> bool:
        if recorder_id in self.recorders:
            return False

        recorder: AudioRecorder
        if recorder_type == "microphone":
            recorder = MicrophoneRecorder()
        elif recorder_type == "system":
            recorder = SystemAudioRecorder()
        else:
            return False

        recorder.set_waveform_callback(
            lambda waveform: self._broadcast_waveform(recorder_id, waveform)
        )

        self.recorders[recorder_id] = recorder
        self.websocket_connections[recorder_id] = set()
        return True

    def start_recording(self, recorder_id: str) -> bool:
        if recorder_id not in self.recorders:
            return False
        return self.recorders[recorder_id].start_recording()

    def stop_recording(self, recorder_id: str) -> bool:
        if recorder_id not in self.recorders:
            return False
        return self.recorders[recorder_id].stop_recording()

    def save_recording(self, recorder_id: str, filepath: Path) -> bool:
        if recorder_id not in self.recorders:
            return False
        return self.recorders[recorder_id].save_audio(filepath)

    def get_recording_status(self, recorder_id: str) -> Dict[str, Any]:
        if recorder_id not in self.recorders:
            return {"exists": False}

        recorder = self.recorders[recorder_id]
        return {
            "exists": True,
            "is_recording": recorder.is_recording,
            "sample_rate": recorder.sample_rate,
            "channels": recorder.channels,
        }

    def add_websocket_connection(self, recorder_id: str, websocket):
        if recorder_id not in self.websocket_connections:
            self.websocket_connections[recorder_id] = set()
        self.websocket_connections[recorder_id].add(websocket)

    def remove_websocket_connection(self, recorder_id: str, websocket):
        if recorder_id in self.websocket_connections:
            self.websocket_connections[recorder_id].discard(websocket)

    def _broadcast_waveform(self, recorder_id: str, waveform_data: list):
        if recorder_id not in self.websocket_connections:
            return

        message = json.dumps(
            {"type": "waveform", "recorder_id": recorder_id, "data": waveform_data}
        )

        disconnected = set()
        for websocket in self.websocket_connections[recorder_id]:
            try:
                asyncio.create_task(websocket.send(message))
            except Exception:
                disconnected.add(websocket)

        for websocket in disconnected:
            self.websocket_connections[recorder_id].discard(websocket)

    def cleanup_recorder(self, recorder_id: str):
        if recorder_id in self.recorders:
            self.recorders[recorder_id].stop_recording()
            del self.recorders[recorder_id]

        if recorder_id in self.websocket_connections:
            del self.websocket_connections[recorder_id]
