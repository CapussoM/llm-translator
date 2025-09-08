import os
import io
from google.cloud import texttospeech
from services.ai_service import AIService

class GoogleCloudTTSService(AIService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = texttospeech.TextToSpeechClient()
        self.speakers = {"male": [], "female": []}

        # Map languages to Google voices
        self.languages = {
            "english": {
                "male": "en-US-Wavenet-D",
                "female": "en-US-Wavenet-F"
            },
            "spanish": {
                "male": "es-ES-Wavenet-A",
                "female": "es-ES-Wavenet-B"
            },
            "japanese": {
                "male": "ja-JP-Wavenet-D",
                "female": "ja-JP-Wavenet-C"
            }
        }

    def run_tts(self, message):
        sentence = message['translation']
        language = message['translation_language']
        voice_type = message.get('voice', 'male')  # default to male
        sid = message['participantId']

        if language not in self.languages:
            raise Exception(
                f"Google TTS doesn't support {language}. Supported: {', '.join(self.languages.keys())}"
            )

        # Round-robin selection of speakers for this session id
        if sid not in self.speakers[voice_type]:
            self.speakers[voice_type].append(sid)
        voice_name = self.languages[language][voice_type]

        synthesis_input = texttospeech.SynthesisInput(text=sentence)
        voice_params = texttospeech.VoiceSelectionParams(
            language_code=voice_name.split("-")[0],
            name=voice_name
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000
        )

        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config
        )

        # Yield audio in chunks like PlayHT (here we just yield 1024-byte chunks)
        b = response.audio_content
        chunk_size = 1024
        for i in range(0, len(b), chunk_size):
            yield b[i:i+chunk_size]
