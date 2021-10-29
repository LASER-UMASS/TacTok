
from collections import Counter
from typing import List, Dict, Tuple, Optional
import typing


class IndexedTrieNode:
    def __init__(self, char: str) -> None:
        self.char = char
        self.is_end = False
        self.index: Optional[int] = None
        self.children: Dict[str, IndexedTrieNode] = {}


class IndexedTrie:
    def __init__(self) -> None:
        self.root = IndexedTrieNode("")
    
    def insert(self, idx: int, token: str) -> None:
        cur_node = self.root
        for char in token:
            if char in cur_node.children:
                cur_node = cur_node.children[char]
            else:
                new_node = IndexedTrieNode(char)
                cur_node.children[char] = new_node
                cur_node = new_node
        cur_node.is_end = True
        cur_node.index = idx

    def longest_prefix(self, sentence: str) -> Optional[Tuple[int, str]]:
        cur_node = self.root
        longest_match: Optional[Tuple[int, str]] = None
        for idx, char in enumerate(sentence):
            if cur_node.is_end:
                assert cur_node.index is not None
                longest_match = (cur_node.index, sentence[:idx])
            if char in cur_node.children:
                cur_node = cur_node.children[char]
            else:
                return longest_match
        if cur_node.is_end:
            assert cur_node.index is not None
            longest_match = (cur_node.index, sentence)
        return longest_match


class BPETokenizer:
    def __init__(self, word_counts: Dict[str, int], merges: int,
                 include_unks: bool = False) -> None:
        self.include_unks = include_unks
        base_vocab = list(set([x for l in [list(word) for word in word_counts.keys()]
                               for x in l]))
        self.unk_index = len(base_vocab)
        self.vocab_size = len(base_vocab) + merges \
          + (1 if include_unks else 0)

        vocab = list(base_vocab) + (["<unk>"] if include_unks else [])
        word_breakdowns = [(list(word), count) for word, count in word_counts.items()]
        for i in range(merges):
            pair_counts: typing.Counter[Tuple[str, str]] = Counter()
            for chunks, count in word_breakdowns:
                for pair in zip(chunks[:-1], chunks[1:]):
                    pair_counts[pair] += count
            most_common_pair, mcp_count = pair_counts.most_common(1)[0]
            new_word_breakdowns = []
            for chunks, count in word_breakdowns:
                new_chunks = []
                i = 0
                while i + 1 < len(chunks):
                    if chunks[i] == most_common_pair[0] and \
                       chunks[i+1] == most_common_pair[1]:
                        new_chunks.append(most_common_pair[0] + most_common_pair[1])
                        i += 2
                    else:
                        new_chunks.append(chunks[i])
                        if i + 2 == len(chunks):
                            new_chunks.append(chunks[i+1])
                        i += 1
                new_word_breakdowns.append((new_chunks, count))
            word_breakdowns = new_word_breakdowns
            vocab.append(most_common_pair[0] + most_common_pair[1])

        self.vocab = vocab
        self.word_chunk_cache = {}
        for chunks, _ in word_breakdowns:
            self.word_chunk_cache["".join(chunks)] = [(vocab.index(chunk), chunk)
                                                      for chunk in chunks]
        self.tok_trie = IndexedTrie()
        for idx, word in enumerate(vocab):
            self.tok_trie.insert(idx, word)

    def pre_tokenize(self, sentence: str) -> List[str]:
        return sentence.split(" ")

    def tokenize_to_idx(self, sentence: str) -> List[int]:
        return [chunk_idx for chunk_idx, chunk_str in
                self.tokenize(sentence)]
    def tokenize(self, sentence: str) -> List[Tuple[int, str]]:
        words = self.pre_tokenize(sentence)
        tokens = []
        for word in words:
            if word in self.word_chunk_cache:
                tokens.extend(self.word_chunk_cache[word])
            else:
                rest_chars = word
                while len(rest_chars) > 0:
                    prefix_pair = self.tok_trie.longest_prefix(rest_chars)
                    if prefix_pair is None:
                        if self.include_unks:
                            tokens.append((self.unk_index, "<unk>"))
                        rest_chars = rest_chars[1:]
                    else:
                        pidx, prefix = prefix_pair
                        tokens.append((pidx, prefix))
                        rest_chars = rest_chars[len(prefix):]
        return tokens

if __name__ == "__main__":
    tokenizer = \
      BPETokenizer({"hug": 10,
                    "pug": 5,
                    "pun": 12,
                    "bun": 4,
                    "hugs": 5}, 2)
    print(tokenizer.tokenize("hug pug pun bug mug"))

