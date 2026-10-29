# Copyright (c) 2026 KEITER78
"""Translation-input regression tests using an echo engine, without models."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from local_translation import LocalTranslator


class RecordingProcessor:
    def __init__(self):
        self.encoded_texts = []

    def encode(self, text, out_type):
        self.encoded_texts.append(text)
        return text.split()

    def decode(self, pieces):
        return ' '.join(pieces)


class EchoEngine:
    """Record the actual model inputs and echo content without language tags."""
    def __init__(self):
        self.inputs = []

    def translate_batch(self, batch, target_prefix, **options):
        results = []
        for index, tokens in enumerate(batch):
            self.inputs.append(list(tokens))
            prefix = target_prefix[min(index, len(target_prefix) - 1)]
            results.append(SimpleNamespace(hypotheses=[[*prefix, *tokens[1:-1], '</s>']]))
        return results


class LocalTranslationTests(unittest.TestCase):
    def setUp(self):
        self.translator = LocalTranslator(model_dir='unused-test-model')
        self.translator.processor = RecordingProcessor()
        self.translator.engine = EchoEngine()
        self.translator.load = Mock()

    @property
    def model_content(self):
        return [tokens[1:-1] for tokens in self.translator.engine.inputs]

    def test_screen_wrapped_sentence_reaches_model_as_one_sentence(self):
        result = self.translator.translate('You should go to\nthe store.', 'en', 'ja')
        self.assertEqual(self.translator.processor.encoded_texts, ['You should go to the store.'])
        self.assertEqual(self.model_content, [['You', 'should', 'go', 'to', 'the', 'store.']])
        self.assertEqual(result, 'You should go to the store.')

    def test_blank_line_preserves_paragraph_boundary_without_mixing_model_inputs(self):
        result = self.translator.translate('The first paragraph\ncontinues here.\n\nThe second\nstarts here.', 'en', 'ja')
        self.assertEqual(self.translator.processor.encoded_texts,
                         ['The first paragraph continues here.', 'The second starts here.'])
        self.assertEqual([' '.join(tokens) for tokens in self.model_content],
                         ['The first paragraph continues here.', 'The second starts here.'])
        self.assertEqual(result, 'The first paragraph continues here.\n\nThe second starts here.')

    def test_whitespace_only_lines_are_paragraph_boundaries(self):
        result = self.translator.translate('First paragraph.\n \t \nSecond paragraph.', 'en', 'ja')
        self.assertEqual(self.translator.processor.encoded_texts,
                         ['First paragraph.', 'Second paragraph.'])
        self.assertEqual(result, 'First paragraph.\n\nSecond paragraph.')

    def test_pasted_windows_crlf_input_uses_same_wrapping_and_paragraph_rules(self):
        result = self.translator.translate('You should go to\r\nthe store.\r\n\r\nThen return\r\nhome.', 'en', 'ja')
        self.assertEqual(self.translator.processor.encoded_texts,
                         ['You should go to the store.', 'Then return home.'])
        self.assertEqual(result, 'You should go to the store.\n\nThen return home.')

    def test_consecutive_blank_lines_do_not_create_empty_model_calls(self):
        result = self.translator.translate('First paragraph.\n\n \n\t\nSecond paragraph.', 'en', 'ja')
        self.assertEqual(self.translator.processor.encoded_texts,
                         ['First paragraph.', 'Second paragraph.'])
        self.assertEqual(result, 'First paragraph.\n\nSecond paragraph.')

    def test_long_wrapped_paragraph_is_not_truncated_and_keeps_chunk_limit(self):
        words = [f'word{number}' for number in range(850)]
        wrapped = ' '.join(words[:350]) + '\n' + ' '.join(words[350:])
        result = self.translator.translate(wrapped, 'en', 'ja')
        self.assertEqual(self.translator.processor.encoded_texts, [' '.join(words)])
        chunks = self.model_content
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(0 < len(chunk) <= 400 for chunk in chunks))
        self.assertEqual([token for chunk in chunks for token in chunk], words)
        self.assertEqual(result.split(), words)

    def test_empty_or_whitespace_only_input_is_returned_unchanged_without_loading(self):
        for text in ('', ' ', '\r\n\t '):
            with self.subTest(text=repr(text)):
                self.assertEqual(self.translator.translate(text, 'en', 'ja'), text)
        self.translator.load.assert_not_called()
        self.assertEqual(self.translator.processor.encoded_texts, [])
        self.assertEqual(self.translator.engine.inputs, [])

    def test_same_language_preserves_original_text_without_loading(self):
        original = '  You should go to\r\nthe store.\r\n\r\nThen return.  '
        self.assertEqual(self.translator.translate(original, 'en', 'en'), original)
        self.translator.load.assert_not_called()
        self.assertEqual(self.translator.processor.encoded_texts, [])
        self.assertEqual(self.translator.engine.inputs, [])

    def test_invalid_language_pair_still_fails_before_model_use(self):
        with self.assertRaises(ValueError):
            self.translator.translate('Text', 'unknown-language', 'ja')
        self.translator.load.assert_not_called()
        self.assertEqual(self.translator.engine.inputs, [])


if __name__ == '__main__':
    unittest.main()
