from collections import deque
from math import ceil

import numpy as np
import onnxruntime as ort
import sounddevice as sd

SAMPLE_RATE = 16000
BLOCK_SIZE = 512
BLOCK_MS = 1000 * BLOCK_SIZE / SAMPLE_RATE


class SileroVAD:
    def __init__(self, model_path):
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(
            str(model_path), sess_options=options, providers=["CPUExecutionProvider"]
        )
        self.sample_rate = np.array(SAMPLE_RATE, dtype=np.int64)
        self.reset()

    def reset(self):
        self.state = np.zeros((2, 1, 128), dtype=np.float32)
        self.context = np.zeros((1, 64), dtype=np.float32)

    def probability(self, block):
        samples = np.concatenate((self.context, block.reshape(1, BLOCK_SIZE)), axis=1)
        score, self.state = self.session.run(
            None, {"input": samples, "state": self.state, "sr": self.sample_rate}
        )
        self.context = samples[:, -64:]
        return score.item()


class SpeechBuffer:
    def __init__(self, silence_ms, threshold):
        self.silence_blocks = ceil(silence_ms / BLOCK_MS)
        self.threshold = threshold
        self.pre_roll = deque(maxlen=8)
        self.reset()

    def reset(self):
        self.pre_roll.clear()
        self.blocks = []
        self.onset = 0
        self.voiced = 0
        self.quiet = 0

    def push(self, block, probability):
        if not self.blocks:
            self.pre_roll.append(block)
            self.onset = self.onset + 1 if probability >= self.threshold else 0
            if self.onset == 2:
                self.blocks = list(self.pre_roll)
                self.voiced = self.onset
            return None

        self.blocks.append(block)
        if probability >= max(0.01, self.threshold - 0.15):
            self.voiced += 1
            self.quiet = 0
        else:
            self.quiet += 1

        # Limita a memória caso a entrada seja classificada continuamente como fala.
        if self.quiet < self.silence_blocks and len(self.blocks) < ceil(25000 / BLOCK_MS):
            return None

        end = len(self.blocks) - max(0, self.quiet - 3)
        segment = np.concatenate(self.blocks[:end]) if self.voiced >= 5 else None
        self.reset()
        return segment


def ouvir(vad, silence_ms, threshold, on_level=None, should_stop=None):
    vad.reset()
    buffer = SpeechBuffer(silence_ms, threshold)
    # A saída do contexto fecha o microfone antes de processar ou falar.
    with sd.InputStream(
        samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE, channels=1, dtype="float32"
    ) as stream:
        while True:
            if should_stop and should_stop():
                return None
            audio, overflow = stream.read(BLOCK_SIZE)
            if should_stop and should_stop():
                return None
            if overflow:
                vad.reset()
                buffer.reset()
                continue
            block = audio[:, 0]
            if on_level:
                on_level(float(np.sqrt(np.mean(block * block))))
            segment = buffer.push(block, vad.probability(block))
            if segment is not None:
                return segment
