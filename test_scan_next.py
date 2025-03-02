import unittest

from word_tokens_tools import scan_next, split_into_words, split_into_sentences


class TestScanNext(unittest.TestCase):
    def test_basic_case(self):
        words = ["Hello", "world.", "This", "is", "a", "test."]
        paragraph, next_index = scan_next(words, 0, 2)
        self.assertEqual(paragraph, "Hello world.")
        self.assertEqual(next_index, 2)

    def test_punctuation_beyond_limit(self):
        words = ["This", "is", "a", "long", "sentence", "without", "punctuation", "until", "the", "end."]
        paragraph, next_index = scan_next(words, 0, 5)
        self.assertEqual(paragraph, "This is a long sentence without punctuation until the end.")
        self.assertEqual(next_index, len(words))  # Should reach the end

    def test_stops_naturally_at_punctuation(self):
        words = ["One", "two", "three.", "Four", "five", "six."]
        paragraph, next_index = scan_next(words, 0, 4)
        self.assertEqual(paragraph, "One two three. Four five six.")
        self.assertEqual(next_index, 6)

    def test_no_punctuation_case(self):
        words = ["These", "are", "just", "words", "without", "punctuation", "are", "just", "words", "without", "punctuation", "are", "just", "words", "without", "punctuation"]
        paragraph, next_index = scan_next(words, 0, 4, lookahead_limit=0)
        self.assertEqual(paragraph, "These are just words")
        self.assertEqual(next_index, 4)

    def test_last_word_edge_case(self):
        words = ["Only", "one", "word."]
        paragraph, next_index = scan_next(words, 1, 3)
        self.assertEqual(paragraph, "one word.")
        self.assertEqual(next_index, 3)

    def test_empty_input(self):
        words = []
        paragraph, next_index = scan_next(words, 0, 5)
        self.assertEqual(paragraph, "")
        self.assertEqual(next_index, 0)

    def test_single_word(self):
        words = ["Hello."]
        paragraph, next_index = scan_next(words, 0, 5)
        self.assertEqual(paragraph, "Hello.")
        self.assertEqual(next_index, 1)

    def test_only_punctuation(self):
        words = ["Hello", ",", "world", "!"]
        paragraph, next_index = scan_next(words, 0, 5)
        self.assertEqual(paragraph, "Hello , world !")
        self.assertEqual(next_index, 4)

    def test_long_strings(self):
        data = ["CHAPTER I.Down the Rabbit Hole.",
                 "Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do once or twice she had peeped into the book her sister was reading, but it had no pictures or conversations in it, and what is the use of a book, thought Alice without pictures or conversations?",
                 "So she was considering in her own mind as well as she could, for the hot day made her feel very sleepy and stupid , whether the pleasure of making a daisy chain would be worth the trouble of getting up and picking the daisies, when suddenly a White Rabbit with pink eyes ran close by her.",
                 "There was nothing soveryremarkable in that nor did Alice think it soverymuch out of the way to hear the Rabbit say to itself, Oh dear! Oh dear! I shall be late! when she thought it over afterwards, it occurred to her that she ought to have wondered at this, but at the time it all seemed quite natural but when the Rabbit actuallytook a watch out of its waistcoat pocket, and looked at it, and then hurried on, Alice started to her feet, for it flashed across her mind that she had never before seen a rabbit with either a waistcoat pocket, or a watch to take out of it, and burning with curiosity, she ran across the field after it, and fortunately was just in time to see it pop down a large rabbit hole under the hedge.",
                 "In another moment down went Alice after it, never once considering how in the world she was to get out again."]

        sentences = [sentence.strip() for paragraph in data for sentence in split_into_sentences(paragraph) if
                     sentence.strip()]
        words = split_into_words(sentences)
        paragraph, next_index = scan_next(words, 0, 40)
        self.assertEqual("CHAPTER I. Down the Rabbit Hole. Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do once or twice she had peeped into the book her sister was reading,", paragraph)
        self.assertEqual(next_index, 40)

        paragraph, next_index = scan_next(words, next_index, 20)
        self.assertEqual("but it had no pictures or conversations in it, and what is the use of a book, thought Alice without pictures or conversations?", paragraph)
        self.assertEqual(next_index, 63)


if __name__ == "__main__":
    unittest.main()
