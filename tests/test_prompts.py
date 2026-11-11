import unittest

from core.prompts import REFINE_SYSTEM_PROMPT, build_refine_request


class TestRefineRequest(unittest.TestCase):

    def test_request_with_source(self):
        self.assertEqual(
            build_refine_request("  Kaynak metin.  ", "\nCurrent text.\n"),
            "<source_text>\nKaynak metin.\n</source_text>\n\n<current_text>\nCurrent text.\n</current_text>"
        )

    def test_request_without_source(self):
        for missing in ("", "   ", None):
            self.assertEqual(
                build_refine_request(missing, "Current text."),
                "<current_text>\nCurrent text.\n</current_text>"
            )


class TestRefinePrompt(unittest.TestCase):

    def test_prompt_is_about_editing_not_provenance(self):
        # The feature is style editing. Wording that frames it as hiding how a
        # text was produced must not come back into the prompt.
        lowered = REFINE_SYSTEM_PROMPT.lower()
        for term in ("bypass", "detect", "undetectable", "perplexity", "burstiness",
                     "indistinguishable", "humaniz", "human-written", "human writing"):
            self.assertNotIn(term, lowered)


if __name__ == '__main__':
    unittest.main()
