import unittest

from cryptoUtil import HashFunction
import struct


class cryptoUtilTest(unittest.TestCase):

    def test_hashing_hash_correct_length_for_supported_types(self):
        h = HashFunction()
        h.update(1234854312341212134210)
        h.update("INeedBetterTests!!!!!")
        h.update(0.0129823478921374198237413)
        self.assertEqual(len(h.digest()), 32)

if __name__ == '__main__':
    unittest.main()