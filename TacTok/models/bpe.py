from collections import Counter
from typing import List, Dict, Tuple, Optional
import typing


# A Trie is a tree-based data structure for efficiently finding the longest
# matching prefix of a string among a vocabulary. This indexed Trie does the
# same thing, but also holds an index for each vocabulary word so they can be
# efficiently indexed during prefixing instead of having to scan through the
# vocabulary after.
class IndexedTrie:
    # A node of the indexed trie has a character, index, and whether or not a
    # vocab item ends at this node.
    class IndexedTrieNode:
        def __init__(self, char: str) -> None:
            self.char = char
            self.is_end = False
            self.index: Optional[int] = None
            self.children: Dict[str, self.IndexedTrieNode] = {}

    def __init__(self) -> None:
        self.root = self.IndexedTrieNode("")
    
    # Insert a string into the indexed trie with a given index.
    def insert(self, idx: int, token: str) -> None:
        # Start at the root
        cur_node = self.root
        # For each character in the string, descend the tree to the child
        # corresponding to that character.
        for char in token:
            if char in cur_node.children:
                cur_node = cur_node.children[char]
            else:
                # If the node doesn't already exist for that character, create
                # it.
                new_node = self.IndexedTrieNode(char)
                cur_node.children[char] = new_node
                cur_node = new_node
        # When we've reached the end of the inserted string, mark the current
        # node as a word end.
        cur_node.is_end = True
        # And set it's index to the inserted index.
        cur_node.index = idx

    # Take a string, and return the longest vocabulary word that matches a
    # prefix of the string. When successful, returns a tuple of the vocabulary
    # word index and the word itself; when unsuccessful, returns None.
    def longest_prefix(self, sentence: str) -> Optional[Tuple[int, str]]:
        # Start at the root
        cur_node = self.root
        longest_match: Optional[Tuple[int, str]] = None
        # Descend the tree for each character, keeping track of any node we hit
        # which is an allowed word end.
        for idx, char in enumerate(sentence):
            if cur_node.is_end:
                # If we hit a word end, keep track of it in case we don't find
                # any longer matches.
                assert cur_node.index is not None
                longest_match = (cur_node.index, sentence[:idx])
            # If we have a child for the next character, we can continue down
            # the tree. Otherwise, return the longest match we've found, or
            # None if we haven't found one.
            if char in cur_node.children:
                cur_node = cur_node.children[char]
            else:
                return longest_match
        # If the node we end on is an end node, then the whole thing is our
        # match
        if cur_node.is_end:
            assert cur_node.index is not None
            longest_match = (cur_node.index, sentence)
        return longest_match

# A tokenizer which takes a fixed vocabulary, and tokenizes strings into the
# greedy longest match of tokens from that vocabulary. Uses an IndexedTrie to
# do that effiently.
class LongestMatchTokenizer:
    def __init__(self, vocab: List[str], include_unks: bool = False) -> None:
        # Since there aren't going to be *that* many unique words, cache their
        # tokenizations.
        self.word_chunk_cache: Dict[str, List[Tuple[int, str]]] = {}

        # Store vocab for reference
        self.vocab = vocab

        # Includings unks is optional; if so, they get the last index, and
        # increase our vocab size by one.
        self.include_unks = include_unks
        self.vocab_size = len(vocab) \
          + (1 if include_unks else 0)
        self.unk_index = len(vocab)

        # Build vocab trie
        self.tok_trie = IndexedTrie()
        for idx, word in enumerate(vocab):
            self.tok_trie.insert(idx, word)

    def pre_tokenize(self, sentence: str) -> List[str]:
        return sentence.split(" ")

    # Tokenize to a list of vocabulary indices.
    def tokenize_to_idx(self, sentence: str) -> List[int]:
        return [chunk_idx for chunk_idx, chunk_str in
                self.tokenize(sentence)]
    
    # Tokenize to a list of tuples of vocabulary indices and token strings.
    def tokenize(self, sentence: str) -> List[Tuple[int, str]]:
        tokens = []
        # Pre-tokenize into space-separated words; our tokens will never span a
        # space.
        words = self.pre_tokenize(sentence)
        for word in words:
            # Use the word -> tokenlist cache if possible
            if word in self.word_chunk_cache:
                tokens.extend(self.word_chunk_cache[word])
            else:
                # Otherwise, build up a list of tokens for this word
                word_tokens: List[Tuple[int, str]] = []
                # The rest of the word to process
                rest_chars = str(word)
                # While there's still more in the word
                while len(rest_chars) > 0:
                    # Look up the longest matching prefix in our trie
                    prefix_pair = self.tok_trie.longest_prefix(rest_chars)
                    # If there's no match, treat the next single character as a token
                    if prefix_pair is None:
                        # If we're including unks, add an <unk> to the output
                        if self.include_unks:
                            word_tokens.append((self.unk_index, "<unk>"))
                        # Either way, move on to the next character
                        rest_chars = rest_chars[1:]
                    else:
                        # If we have a match, add it to our token list
                        pidx, prefix = prefix_pair
                        word_tokens.append((pidx, prefix))
                        # Take the match off the front of our "rest" string
                        rest_chars = rest_chars[len(prefix):]
                # Add the tokens for this word into the chunk cache
                self.word_chunk_cache[word] = word_tokens
                # And add them to the overall tokens list
                tokens.extend(word_tokens)
        return tokens

# The algorithm implemented here is based on the 
# https://huggingface.co/transformers/tokenizer_summary.html#byte-pair-encoding-bpe
def get_bpe_vocab(word_counts: Dict[str, int], merges: int) -> List[str]:
    # Our base vocab is every character in any word in our counts.
    base_vocab = list(set([x for l in [list(word) for word in word_counts.keys()]
                           for x in l]))

    # Initialize our vocab to our base vocab
    vocab = list(base_vocab)
    # Build a list, for each word, of the current chunks that make it up and
    # its count. Because our initial vocab is base characters, this means
    # initially splitting each word into it's characters. eg: ("best", 14) ->
    # (["b", "e", "s", "t"], 14).
    word_breakdowns = [(list(word), count) for word, count in word_counts.items()]
    for i in range(merges):
        # Keep the count of each subsequent pair of chunks in our current
        # iteration.
        pair_counts: typing.Counter[Tuple[str, str]] = Counter()
        for chunks, count in word_breakdowns:
            for pair in zip(chunks[:-1], chunks[1:]):
                pair_counts[pair] += count
        # Get the most common chunk pairing
        most_common_pair, mcp_count = pair_counts.most_common(1)[0]
        # Update the word breakdowns to merge that pair
        new_word_breakdowns = []
        for chunks, count in word_breakdowns:
            new_chunks = []
            i = 0
            # Loop through the chunks for each word, and merge any subsequent
            # ones that match the most common pair.
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
        # Finally, add the pair to the vocab list.
        vocab.append(most_common_pair[0] + most_common_pair[1])
    return vocab

