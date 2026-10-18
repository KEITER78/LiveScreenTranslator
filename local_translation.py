# Copyright (c) 2026 KEITER78
"""CPU-only machine translation. No API client, prompt, or chat history."""
from pathlib import Path
import re

from languages import validate_pair
from prepare_translation import MODEL_DIR, model_ready

class LocalTranslator:
    def __init__(self, model_dir=MODEL_DIR):
        self.model_dir = Path(model_dir)
        self.engine = None
        self.processor = None

    def load(self):
        if self.engine is not None:
            return
        if not model_ready(self.model_dir):
            raise RuntimeError('先に「翻訳モデルを準備」を実行してください。')
        import ctranslate2
        import sentencepiece
        self.processor = sentencepiece.SentencePieceProcessor(
            model_file=str(self.model_dir/'sentencepiece.bpe.model'))
        self.engine = ctranslate2.Translator(str(self.model_dir), device='cpu',
            compute_type='int8', intra_threads=4, inter_threads=1)

    def translate(self, text, source, target):
        validate_pair(source, target)
        if not text.strip() or source == target:
            return text
        self.load()
        output = []
        for paragraph in text.splitlines():
            if not paragraph.strip():
                output.append('')
                continue
            # Bound memory without silently truncating long screen text.
            pieces = self.processor.encode(paragraph, out_type=str)
            translated = []
            for offset in range(0, len(pieces), 400):
                tokens = [f'__{source}__', *pieces[offset:offset+400], '</s>']
                result = self.engine.translate_batch([tokens],
                    target_prefix=[[f'__{target}__']], beam_size=2,
                    max_decoding_length=512)[0].hypotheses[0]
                result = [t for t in result if not re.fullmatch(r'__[a-z]+__', t)
                          and t not in ('</s>', '<s>', '<pad>')]
                translated.append(self.processor.decode(result))
            output.append(' '.join(translated))
        return '\n'.join(output)
