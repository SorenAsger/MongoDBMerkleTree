import unittest

from crypto_util import HashFunction

class cryptoUtilTest(unittest.TestCase):

    def test_hashing_hash_correct_length_for_supported_types(self):
        h = HashFunction()
        h.update(1234854312341212134210)
        h.update("INeedBetterTests!!!!!")
        h.update(0.0129823478921374198237413)
        self.assertEqual(len(h.digest()), 32)

    def test_hashing_None_should_do_nothing(self):
        h1 = HashFunction()
        h2 = HashFunction()

        h1.update(12345)
        h2.update(12345)
        h2.update(None)
        self.assertEqual(h1.digest(), h2.digest())

if __name__ == '__main__':
    unittest.main()