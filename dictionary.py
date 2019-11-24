import json
import os.path
import logging
from typing import Iterator, List, Dict, Set, NamedTuple, Optional, Union, NewType

logger = logging.getLogger("dictionary")


class WordCouple(NamedTuple):
    """Stores potential cross words - word_str is the word and index the indice of the joker in the word"""
    index: int
    word_str: str


Mask = NewType('Mask', list)


class MaskItem():
    """Provide readability and performance on mask items meaning and access"""

    def __init__(self, item: Optional[Union[dict, str]]):
        """Initialise a mask item and compute boolean attributes"""
        assert isinstance(item, (dict, str)) or item is None

        self.data = item
        self.has_no_letter, \
        self.has_letter, \
        self.is_cross_word, \
        self.is_open_to_any_letter, \
        self.is_usable, \
        self.is_not_usable = False, False, False, False, False, False
        if isinstance(item, dict):
            self.has_no_letter = True
            self.is_usable = True
            if item:
                self.is_cross_word = True
            else:
                self.is_open_to_any_letter = True
        elif item is None:
            self.has_no_letter = True
            self.is_not_usable = True
        elif isinstance(item, str):
            self.has_letter = True
        else:
            raise ValueError("MaskItem must be dict, str or None")

    def __eq__(self, other: 'MaskItem') -> bool:
        return self.data == other.data

    def __ne__(self, other: 'MaskItem') -> bool:
        return not (self == other)

    def __iter__(self) -> Iterator:
        """Default Iterator of the class"""
        self.n = 0
        return self

    def __next__(self) -> str:
        """Default Iterator of the class - Adapted to the type of this item"""
        # MAY BE USING METACLASS CAN GENERATE THE ITERATOR TUNED FOR THE very type hosted in self.data
        if self.data is None:
            if self.n == 1:
                raise StopIteration
            else:
                self.n += 1
                return ""

        elif isinstance(self.data, str):
            if self.n == 1:
                raise StopIteration
            else:
                self.n += 1
                return self.data

        elif isinstance(self.data, dict):
            if self.n == len(self.data):
                raise StopIteration
            else:
                self.n += 1
                return [_ for _ in self.data.keys()][self.n - 1]

    def __repr__(self) -> str:
        return self.data.__repr__()


class Node:
    """Provide support for nodes in the tree that implements the dictionary data"""
    node_id = 0

    def __init__(self, is_termination=False):
        """Initialise a new node"""
        self.is_termination = is_termination
        self.edges_out = {}  # key is letter and value is node_out for this edge
        self.edge_in = None  # tuple (preceding Node, letter)
        self.node_id = __class__.node_id
        __class__.node_id += 1  # this is for the __hash__ implementation

    def __eq__(self, other: 'Node') -> bool:
        return (self.is_termination == other.is_termination
                and self.edges_out == other.edges_out and
                self.edge_in == other.edge_in)

    def __ne__(self, other: 'Node') -> bool:
        return not (self == other)

    def __hash__(self) -> int:
        return self.node_id

    def __repr__(self) -> str:

        string = ""
        if self.edge_in:
            _, preceding_letter = self.edge_in
        else:
            preceding_letter = ""
        string += "edge_in=" + preceding_letter + " | "
        string += "edges_out=" + "".join(sorted(list(self.edges_out.keys()))) + " | "
        if self.is_termination:
            string += " TERMINATION"
        else:
            string += " CONNECT"

        return string


class Trie:
    """Manage dictionary as a tree model"""

    # list hosting all nodes indexed at 1st level by node depth in the tree
    def __init__(self, lang='FR'):
        """Initialise Trie object - create a tree made of its empty structure and root node"""
        self.trie = [[]]
        self.trie[0].append(Node())  # create root node
        self.lang = lang

    def load_from_json_word_list(self, json_file_name: str):
        """Load dictionary from a json file"""
        assert os.path.exists(json_file_name)

        # load dictionary from json
        with open(json_file_name, 'r') as fp:
            word_list = json.load(fp)
        word_set = set(word_list)  # set of all words

        for nb_words, word in enumerate(word_set):
            self._add_word(word)

        logger.info("%s words loaded from %s" % (str(nb_words), json_file_name))

    def _root(self) -> Node:
        """Return the root node for the dict"""
        assert len(self.trie[0]) == 1
        return self.trie[0][0]

    def _nodes_of_rank_n_iterator(self, n: int) -> Iterator[Node]:
        """Iterator providing all nodes of dict for a given depth provided in n parameter"""
        assert isinstance(n, int)
        assert n < self._max_depth()
        if self._max_depth():
            for node in self.trie[n]:
                yield node
        else:
            raise StopIteration

    def _max_depth(self) -> int:
        """Return maximum depth of the tree supporting dict"""
        return len(self.trie)

    def _add_node_at_rank_n(self, node: Node, rank: int) -> bool:
        """Insert a node in the list of node of rank parameter - rank is depth in tree starting at 0 for root"""
        assert isinstance(node, Node)
        assert isinstance(rank, int)
        assert rank <= self._max_depth()

        # add a level to the tree
        if rank == self._max_depth():
            self.trie.append([])

        self.trie[rank].append(node)

        return True

    def _add_word(self, string: str) -> bool:
        """Add a word in the dict - return False if word already exists - True otherwise"""
        assert isinstance(string, str)
        assert string.isalpha()
        assert string.isupper()
        assert 1 < len(string) <= 15

        current_node = self._root()
        for i, letter in enumerate(string):
            try:
                current_node = current_node.edges_out[letter]
            except KeyError:  # create edge and node out
                new_node = Node()
                self._add_node_at_rank_n(new_node, i + 1)
                current_node.edges_out[letter] = new_node
                new_node.edge_in = (current_node, letter)
                current_node = new_node
        # word parsing is completed - mark current node as a termination
        if not current_node.is_termination:
            current_node.is_termination = True
            return True
        else:
            logger.warning("word %s already existing in tree" % string)
            return False

    def _word_list(self, node: Node) -> Iterator[str]:
        for letter in node.edges_out.keys():
            if node.edges_out[letter].is_termination:
                yield letter
            if node.edges_out[letter].edges_out:
                for l in self._word_list(node.edges_out[letter]):
                    yield letter + l

    def this_is_a_valid_word(self, string: str) -> bool:
        """Return True if word exists in dictionary, False otherwise"""
        assert isinstance(string, str)
        assert string.isalpha()
        assert string.isupper()
        assert 1 < len(string) <= 15

        node = self._root()
        for i, letter in enumerate(string):
            try:
                node = node.edges_out[letter]
            except KeyError:
                return False
        if node.is_termination and i == len(string) - 1:
            return True
        else:
            return False

    def word_set_of_given_length(self, length: int) -> Set[str]:
        """Return all words of a given length as a set"""
        assert isinstance(length, int)
        assert 1 < length <= 14

        word_set = set()
        for word_node in [node for node in self.trie[length] if node.is_termination]:
            word_set.add(self._word_for_termination_node(word_node))

        return word_set

    # noinspection PyUnusedLocal
    @staticmethod  # TODO why is this method static ?
    def _word_for_termination_node(node: Node) -> str:
        """Return word corresponding to the termination node parameter - as a string"""
        assert isinstance(node, Node)
        assert node.is_termination

        word = ""
        current_node = node
        while node.edge_in:
            next_node, letter = node.edge_in
            word = letter + word
            node = next_node

        return word

    # noinspection PyUnusedLocal
    def possible_word_set_from_string(self, string: str) -> Dict[str, WordCouple]:
        """
        Get all words for a string that contains exactly ONE blank interpreted as a wildcard letter

        this is required to build the list of cross words and the letters that are possible on the main line

        :param string: str of upper case letter containing exactly one blank that is interpreted as wildcard/joker to
                       identify all possible words
        :return: {...,
                  "letter": WordCouple(index of letter in word: int , words as str),
                  "letter": WordCouple(index of letter in word: int , words as str),
                  ....
                  }
                        or
                  {} empty dict if no solution identified
                  WordCouple is a namedtuple:  WordCouple = namedtuple("WordCouple", ["index", "word_str"])

        """
        assert isinstance(string, str)
        assert string.replace(" ", "A").isalpha()
        assert string.replace(" ", "A").isupper()
        assert len(string) <= 15
        assert string.count(" ") == 1  # " " is the wildcard letter and there must be only one

        word_dict = {}
        joker_index = string.index(" ")
        for letter in list(map(chr, range(65, 91))):  # alphabet uppercase letters
            string_2_be_tested = string.replace(" ", letter)
            if self.this_is_a_valid_word(string_2_be_tested):
                word_dict[letter] = WordCouple(index=joker_index, word_str=string_2_be_tested)

        return word_dict

    def possible_words_for_mask_with_rack(self, mask: 'Mask',
                                          tile_list: List[str],
                                          min_length: int) -> Set[str]:
        """
        Identify all possible words doable with tile_list that (1) matches the mask and (2) are of minimum length

        this method represents over 40% of total compute time for a game
        :param mask:
        :param tile_list: list of upper case letters
        :param min_length:
        :return: set of possible words in str format
        """
        assert len(mask) <= self._max_depth()
        if min_length == 0:  # TODO move case out so that test is made before calling function = better perf
            return set()
        assert min_length > 0

        termination_node_set = set()  # store identified termination node for word that works
        upper_alphabet_set = frozenset({chr(k) for k in range(65, 65 + 26)})

        words_are_long_enough_to_be_collected = False
        """
         pw stands for potential words
         this structure stores potential word per level in the tree
         higher level list is per node level
         each list item is a dict which keys are nodes still to be explored and values are tile list that 
         contains the list of tile still not used for this node/path

         example is :
         [  {...},                                               
            {Node: ["A", "B", "E", "C", "Z", "F"],
             Node: ["A", "B", "E", "C", " "],
             ....              
                  },
            {...}
         ]
        """
        pw = [{self._root(): tile_list.copy()}]  # pw ==> potential word TODO find a better name
        for mask_i, mask_item in enumerate(mask):
            pw_i = mask_i + 1  # skip root node  - pw indices are +1 as compared to mask
            if pw_i >= min_length:
                words_are_long_enough_to_be_collected = True
            pw.append({})  # new item in pw for this level in the Trie

            if mask_item.is_cross_word:  # existing cross-word case - mask_item is a set of letter
                for node in pw[pw_i - 1]:

                    pw_node_tilelist_ref = pw[pw_i - 1][node]  # store ref to avoid look-up and speed-up next calls

                    if " " in pw_node_tilelist_ref:
                        joker_case = True
                    else:
                        joker_case = False
                    letter_2_be_scan_set = {l for l in pw_node_tilelist_ref if l in mask_item.data}
                    # mask_item never contains blank so no need to remove from letter_2_be_scan_set like in
                    # genuine empty position case (with no cross-words)

                    letter_4_next_set = letter_2_be_scan_set.intersection({l for l in node.edges_out})

                    for letter in letter_4_next_set:
                        good_node = node.edges_out[letter]
                        pw[pw_i][good_node] = pw_node_tilelist_ref.copy()
                        pw[pw_i][good_node].remove(letter)

                    if joker_case:
                        for letter in {l for l in mask_item.data}.intersection({l for l in node.edges_out}) \
                                      - letter_4_next_set:
                            good_node = node.edges_out[letter]
                            pw[pw_i][good_node] = pw_node_tilelist_ref.copy()
                            pw[pw_i][good_node].remove(" ")

            elif mask_item.is_open_to_any_letter:  # empty position - any tile could fit
                for node in pw[pw_i - 1]:

                    pw_node_tilelist_ref = pw[pw_i - 1][node]

                    letter_2_be_scan_set = {l for l in pw_node_tilelist_ref}
                    if " " in letter_2_be_scan_set:
                        joker_case = True
                        letter_2_be_scan_set.discard(" ")
                    else:
                        joker_case = False

                    letter_4_next_set = letter_2_be_scan_set.intersection({l for l in node.edges_out})

                    for letter in letter_4_next_set:
                        good_node = node.edges_out[letter]
                        pw[pw_i][good_node] = pw_node_tilelist_ref.copy()
                        pw[pw_i][good_node].remove(letter)

                    if joker_case:
                        for letter in upper_alphabet_set.intersection({l for l in node.edges_out}) \
                                      - letter_4_next_set:
                            good_node = node.edges_out[letter]
                            pw[pw_i][good_node] = pw_node_tilelist_ref.copy()
                            pw[pw_i][good_node].remove(" ")

            elif mask_item.has_letter:  # letter already on board
                letter = mask_item.data
                for node in pw[pw_i - 1]:
                    if letter in node.edges_out:
                        pw[pw_i][node.edges_out[letter]] = pw[pw_i - 1][node].copy()

            elif mask_item.is_not_usable:  # position can't be used - adjacent letter with no possible cross-word
                break  # this is the end of the usable mask

            if words_are_long_enough_to_be_collected:
                termination_node_set |= {n for n in pw[pw_i] if n.is_termination}

        # return set of words generated from termination node
        return {self._word_for_termination_node(termination_node) for termination_node in termination_node_set}
