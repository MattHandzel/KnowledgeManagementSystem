import os
import pytest
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
sd = pytest.importorskip("sounddevice", reason="PortAudio not installed")

from server.audio_recorder import (
    AudioRecorder, 
    MicrophoneRecorder, 
    SystemAudioRecorder, 
    AudioRecordingManager
)


class MockAudioRecorder(AudioRecorder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mock_device_info = {'name': 'Mock Device', 'channels': 1}
        
    def _get_device_info(self):
        return self.mock_device_info
        
    def _get_stream_params(self):
        return {
            'samplerate': self.sample_rate,
            'channels': self.channels,
            'dtype': np.float32,
            'blocksize': self.chunk_size
        }


class TestAudioRecorder:
    def test_init(self):
        recorder = MockAudioRecorder()
        assert recorder.sample_rate == 44100
        assert recorder.channels == 1
        assert recorder.chunk_size == 1024
        assert not recorder.is_recording
        assert recorder.audio_data == []
        
    def test_set_waveform_callback(self):
        recorder = MockAudioRecorder()
        callback = Mock()
        recorder.set_waveform_callback(callback)
        assert recorder.waveform_callback == callback
        
    @patch('server.audio_recorder.sd.InputStream')
    def test_start_recording_success(self, mock_stream):
        recorder = MockAudioRecorder()
        
        mock_stream_instance = Mock()
        mock_stream.return_value.__enter__.return_value = mock_stream_instance
        
        result = recorder.start_recording()
        assert result is True
        assert recorder.is_recording is True
        assert recorder.recording_thread is not None
        
        recorder.stop_recording()
        
    def test_start_recording_already_recording(self):
        recorder = MockAudioRecorder()
        recorder.is_recording = True
        
        result = recorder.start_recording()
        assert result is False
        
    @patch('server.audio_recorder.sd.InputStream')
    def test_stop_recording(self, mock_stream):
        recorder = MockAudioRecorder()
        
        mock_stream_instance = Mock()
        mock_stream.return_value.__enter__.return_value = mock_stream_instance
        
        recorder.start_recording()
        time.sleep(0.1)
        
        result = recorder.stop_recording()
        assert result is True
        assert recorder.is_recording is False
        
    def test_stop_recording_not_recording(self):
        recorder = MockAudioRecorder()
        
        result = recorder.stop_recording()
        assert result is False
        
    def test_save_audio_no_data(self):
        recorder = MockAudioRecorder()
        
        with tempfile.NamedTemporaryFile(suffix='.wav') as tmp:
            result = recorder.save_audio(Path(tmp.name))
            assert result is False
            
    def test_save_audio_with_data(self):
        recorder = MockAudioRecorder()
        recorder.audio_data = [np.array([0.1, 0.2, 0.3]), np.array([0.4, 0.5, 0.6])]
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = Path(tmp.name)
            
        try:
            result = recorder.save_audio(tmp_path)
            assert result is True
            assert tmp_path.exists()
            assert tmp_path.stat().st_size > 0
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
                
    def test_calculate_waveform(self):
        recorder = MockAudioRecorder()
        
        audio_chunk = np.array([0.1, 0.2, 0.3, 0.4, 0.5] * 20)
        waveform = recorder._calculate_waveform(audio_chunk)
        
        assert len(waveform) == 50
        assert all(0 <= val <= 100 for val in waveform)
        
    def test_calculate_waveform_stereo(self):
        recorder = MockAudioRecorder()
        
        audio_chunk = np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]] * 20)
        waveform = recorder._calculate_waveform(audio_chunk)
        
        assert len(waveform) == 50
        assert all(0 <= val <= 100 for val in waveform)


class TestMicrophoneRecorder:
    @patch('sounddevice.query_devices')
    def test_get_device_info_success(self, mock_query):
        mock_query.return_value = {'name': 'Microphone', 'channels': 1}
        
        recorder = MicrophoneRecorder()
        device_info = recorder._get_device_info()
        
        assert device_info['name'] == 'Microphone'
        mock_query.assert_called_once_with(kind='input')
        
    @patch('sounddevice.query_devices')
    def test_get_device_info_failure(self, mock_query):
        mock_query.side_effect = Exception('No device')
        
        recorder = MicrophoneRecorder()
        device_info = recorder._get_device_info()
        
        assert device_info == {}
        
    def test_get_stream_params(self):
        recorder = MicrophoneRecorder()
        params = recorder._get_stream_params()
        
        expected = {
            'samplerate': 44100,
            'channels': 1,
            'dtype': np.float32,
            'blocksize': 1024
        }
        assert params == expected


class TestSystemAudioRecorder:
    @patch('sounddevice.query_devices')
    def test_get_device_info_with_loopback(self, mock_query):
        mock_devices = [
            {'name': 'Speakers', 'channels': 2},
            {'name': 'Loopback Device', 'channels': 2},
            {'name': 'Microphone', 'channels': 1}
        ]
        mock_query.return_value = mock_devices
        
        recorder = SystemAudioRecorder()
        device_info = recorder._get_device_info()
        
        assert device_info['name'] == 'Loopback Device'
        
    @patch('sounddevice.query_devices')
    def test_get_device_info_with_monitor(self, mock_query):
        mock_devices = [
            {'name': 'Speakers', 'channels': 2},
            {'name': 'Monitor of Built-in Audio', 'channels': 2},
            {'name': 'Microphone', 'channels': 1}
        ]
        mock_query.return_value = mock_devices
        
        recorder = SystemAudioRecorder()
        device_info = recorder._get_device_info()
        
        assert device_info['name'] == 'Monitor of Built-in Audio'
        
    @patch('sounddevice.query_devices')
    def test_get_device_info_fallback(self, mock_query):
        mock_devices = [
            {'name': 'Speakers', 'channels': 2},
            {'name': 'Microphone', 'channels': 1}
        ]
        
        def side_effect(*args, **kwargs):
            if kwargs.get('kind') == 'input':
                return {'name': 'Default Input', 'channels': 1}
            return mock_devices
            
        mock_query.side_effect = side_effect
        
        recorder = SystemAudioRecorder()
        device_info = recorder._get_device_info()
        
        assert device_info['name'] == 'Default Input'


class TestAudioRecordingManager:
    def test_init(self):
        manager = AudioRecordingManager()
        assert manager.recorders == {}
        assert manager.websocket_connections == {}
        
    def test_create_recorder_microphone(self):
        manager = AudioRecordingManager()
        
        result = manager.create_recorder('microphone', 'test_mic')
        assert result is True
        assert 'test_mic' in manager.recorders
        assert isinstance(manager.recorders['test_mic'], MicrophoneRecorder)
        assert 'test_mic' in manager.websocket_connections
        
    def test_create_recorder_system(self):
        manager = AudioRecordingManager()
        
        result = manager.create_recorder('system', 'test_sys')
        assert result is True
        assert 'test_sys' in manager.recorders
        assert isinstance(manager.recorders['test_sys'], SystemAudioRecorder)
        
    def test_create_recorder_invalid_type(self):
        manager = AudioRecordingManager()
        
        result = manager.create_recorder('invalid', 'test_invalid')
        assert result is False
        assert 'test_invalid' not in manager.recorders
        
    def test_create_recorder_already_exists(self):
        manager = AudioRecordingManager()
        manager.create_recorder('microphone', 'test_mic')
        
        result = manager.create_recorder('microphone', 'test_mic')
        assert result is False
        
    @patch('server.audio_recorder.sd.query_devices', return_value={'name': 'Default Input', 'channels': 1})
    @patch('server.audio_recorder.sd.InputStream')
    def test_start_recording(self, mock_stream, mock_query):
        manager = AudioRecordingManager()
        manager.create_recorder('microphone', 'test_mic')
        
        mock_stream_instance = Mock()
        mock_stream.return_value.__enter__.return_value = mock_stream_instance
        
        result = manager.start_recording('test_mic')
        assert result is True
        
        manager.stop_recording('test_mic')
        
    def test_start_recording_nonexistent(self):
        manager = AudioRecordingManager()
        
        result = manager.start_recording('nonexistent')
        assert result is False
        
    def test_get_recording_status_exists(self):
        manager = AudioRecordingManager()
        manager.create_recorder('microphone', 'test_mic')
        
        status = manager.get_recording_status('test_mic')
        assert status['exists'] is True
        assert status['is_recording'] is False
        assert status['sample_rate'] == 44100
        assert status['channels'] == 1
        
    def test_get_recording_status_nonexistent(self):
        manager = AudioRecordingManager()
        
        status = manager.get_recording_status('nonexistent')
        assert status['exists'] is False
        
    def test_websocket_connection_management(self):
        manager = AudioRecordingManager()
        manager.create_recorder('microphone', 'test_mic')
        
        mock_websocket = Mock()
        manager.add_websocket_connection('test_mic', mock_websocket)
        
        assert mock_websocket in manager.websocket_connections['test_mic']
        
        manager.remove_websocket_connection('test_mic', mock_websocket)
        assert mock_websocket not in manager.websocket_connections['test_mic']
        
    def test_cleanup_recorder(self):
        manager = AudioRecordingManager()
        manager.create_recorder('microphone', 'test_mic')
        
        manager.cleanup_recorder('test_mic')
        assert 'test_mic' not in manager.recorders
        assert 'test_mic' not in manager.websocket_connections


@pytest.fixture
def audio_manager():
    return AudioRecordingManager()


@pytest.fixture
def mock_websocket():
    websocket = Mock()
    websocket.send = Mock()
    return websocket


class TestAudioRecordingIntegration:
    def test_full_recording_workflow(self, audio_manager):
        recorder_id = 'integration_test'
        
        assert audio_manager.create_recorder('microphone', recorder_id)
        
        status = audio_manager.get_recording_status(recorder_id)
        assert status['exists'] is True
        assert not status['is_recording']
        
        audio_manager.cleanup_recorder(recorder_id)
        
        status = audio_manager.get_recording_status(recorder_id)
        assert not status['exists']
        
    def test_websocket_waveform_broadcast(self, audio_manager, mock_websocket):
        recorder_id = 'websocket_test'
        
        audio_manager.create_recorder('microphone', recorder_id)
        audio_manager.add_websocket_connection(recorder_id, mock_websocket)
        
        waveform_data = [10, 20, 30, 40, 50]
        audio_manager._broadcast_waveform(recorder_id, waveform_data)
        
        audio_manager.cleanup_recorder(recorder_id)
