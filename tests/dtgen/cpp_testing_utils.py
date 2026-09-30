from typing import List
import itertools
import re

def cpp_normalize(s: str) -> List[str]:
    return cpp_tokenize(s)
    # return ' '.join(cpp_tokenize(s))

def cpp_tokenize(s: str) -> List[str]:
    chunks = s.split()
    split = itertools.chain(
        *[re.split(r'(::|//|\W|<<)', chunk) for chunk in chunks]
    )

    return [x for x in split if len(x) > 0]

