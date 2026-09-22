from aicaller.audio.aec import NLMSAcousticEchoCanceller
from aicaller.audio.aec_reference import AECReferenceBuffer
from aicaller.audio.agc import AutomaticGainController
from aicaller.audio.format import AudioEncoding, AudioFormat, NormalizedAudioFrame
from aicaller.audio.noise_suppression import AdaptiveNoiseSuppressor
from aicaller.audio.utterance import UtteranceBuffer
from aicaller.audio.vad import EnergyVAD, VADConfig

FMT = AudioFormat(AudioEncoding.PCM16_LE, 8000)


def frame(sequence: int, timestamp: int, sample: int) -> NormalizedAudioFrame:
    return NormalizedAudioFrame(
        "stream-1",
        sequence,
        timestamp,
        int(sample).to_bytes(2, "little", signed=True) * 160,
        FMT,
    )


def test_phase2_audio_processing_chain_preserves_frame_boundary() -> None:
    source = frame(1, 0, 5000)
    reference = AECReferenceBuffer()
    reference.add(frame(1, 0, 500), FMT)

    aligned = reference.find_aligned("stream-1", 1)
    assert aligned is not None

    aec_frame = NLMSAcousticEchoCanceller().process(near_end=source, far_end_reference=aligned)
    denoised = AdaptiveNoiseSuppressor().process(aec_frame)
    leveled = AutomaticGainController().process(denoised)
    vad = EnergyVAD(VADConfig(min_speech_frames=1, min_silence_frames=2))
    result = vad.process(leveled)

    assert result.is_speech
    assert leveled.stream_sid == source.stream_sid
    assert leveled.sequence_number == source.sequence_number
    assert leveled.timestamp_ms == source.timestamp_ms
    assert leveled.format == source.format


def test_phase2_audio_processing_chain_closes_utterance() -> None:
    vad = EnergyVAD(VADConfig(speech_rms_threshold=0.1, min_speech_frames=1, min_silence_frames=2))
    utterances = UtteranceBuffer()

    speech = frame(1, 0, 5000)
    silence1 = frame(2, 20, 0)
    silence2 = frame(3, 40, 0)

    assert utterances.process(speech, vad.process(speech)) is None
    assert utterances.process(silence1, vad.process(silence1)) is None
    result = utterances.process(silence2, vad.process(silence2))

    assert result is not None
    assert result.stream_sid == "stream-1"
    assert result.started_at_ms == 0
    assert result.ended_at_ms == 40
    assert result.payload
