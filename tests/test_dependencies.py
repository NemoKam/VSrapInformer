import random
import string
from datetime import datetime

import unittest

from core import config
from fastapp import dependencies, schemas


class TestDependencies(unittest.TestCase):
    def test_generate_random_string(self):
        test_length: int = random.randint(1, 128)
        test_only_digits: bool = True if random.randint(0, 1) == 1 else False
        
        test_random_string = dependencies.generate_random_string(length=test_length, only_digits=test_only_digits)
        
        self.assertIs(type(test_random_string), str)
        self.assertEqual(len(test_random_string), test_length)
        
    
    def test_hash_password(self):
        test_password: str = dependencies.generate_random_string()
        
        test_hashed_password: str = dependencies.hash_password(test_password)

        self.assertNotEqual(test_password, test_hashed_password)

    
    def test__get_utc_now(self):
        test_current_utc_time: datetime = dependencies._get_utc_now()

        self.assertIs(type(test_current_utc_time), datetime)

    
    def test__create_token(self):
        test_payload: dict = {
            f"{dependencies.generate_random_string(10)}": f"{dependencies.generate_random_string(10)}",
            f"{dependencies.generate_random_string(10)}": f"{dependencies.generate_random_string(10)}" 
        }

        minutes: int = random.randint(1, 30)

        test_token: schemas.JwtTokenCreate = dependencies._create_token(test_payload, minutes)

        self.assertIs(type(test_token), schemas.JwtTokenCreate)
        self.assertIs(type(test_token.expire), datetime)

    
    # Not Finished
    # def test_create_token_pair(self):
    #     test_token_pair: dict = dependencies.create_token_pair()

    #     self.assertIs(test_token_pair, schemas.TokenPair)

