import pytest
import requests

import scrabble
from scrabble import *
from test_results import *


class TestDirection(object):

    def test_direction(self):

        with pytest.raises(AssertionError) as e_info:
            assert Direction(1)
            assert Direction("diagonale")

        v = Direction("down")
        assert str(v) == "Down"
        assert v.is_down

        h = Direction("accross")
        assert str(h) == "Accross"
        assert h.is_accross

        assert v.ortho().is_accross
        assert h.ortho().is_down

    def test_eq_ne(self):

        v = Direction("Down")
        v1 = Direction("Down")
        assert v == v1
        assert not v != v1
        assert v == v
        v2 = Direction("Accross")
        assert v != v2
        assert not v == v2


class TestLine(object):

    def test_line(self):
        with pytest.raises(AssertionError) as e_info:
            assert Line("vertical", 12)
            assert Line(Direction("Down"), "12")
            assert Line(Direction("Down"), 16)
            assert Line(Direction("Down"), -1)

        # __repr__
        assert str(Line(Direction("Down"), 1)) == "col=01"
        assert str(Line(Direction("Accross"), 1)) == "row=01"

        row_01 = Line(Direction("Accross"), 1)
        col_01 = Line(Direction("Down"), 1)

        # __ contains__
        assert Position(1, 12) in row_01
        assert Position(10, 1) in col_01

        # __getitem__
        assert row_01[1] == Position(1, 1)
        assert col_01[10] == Position(10, 1)

        # __iter__ __next__
        assert [p for p in row_01] == [Position(1, i) for i in range(15)]
        assert [p for p in col_01] == [Position(i, 1) for i in range(15)]

        # __hash__
        dict = {}
        dict[row_01] = 1
        assert dict[row_01]


class TestPosition(object):

    def test_position_values(self):
        with pytest.raises(AssertionError) as e_info:
            assert Position(0, 15)
        with pytest.raises(AssertionError) as e_info:
            assert Position(15, 0)
        with pytest.raises(AssertionError) as e_info:
            assert Position(0, "A")
        with pytest.raises(AssertionError) as e_info:
            assert Position(-1, 0)

    def test_eq_ne(self):
        p = Position(0, 0)
        p1 = Position(1, 1)
        p2 = Position(0, 0)

        assert not (p == p1)
        assert p == p2
        assert p != p1
        assert not (p != p2)

    def test_next(self):

        p = Position(0, 12)
        assert [pos for pos in p.next_accross()] == [Position(0, 13), Position(0, 14)]
        assert [pos for pos in p.next(Direction("Accross"))] == [Position(0, 13), Position(0, 14)]
        p = Position(12, 0)
        assert [pos for pos in p.next_down()] == [Position(13, 0), Position(14, 0)]
        assert [pos for pos in p.next(Direction("Down"))] == [Position(13, 0), Position(14, 0)]
        p = Position(0, 14)
        assert [pos for pos in p.next_accross()] == []
        assert [pos for pos in p.next(Direction("Accross"))] == []
        p = Position(14, 0)
        assert [pos for pos in p.next_down()] == []
        assert [pos for pos in p.next(Direction("Down"))] == []

    def test_prev(self):

        p = Position(0, 2)
        assert [pos for pos in p.prev_accross()] == [Position(0, 1), Position(0, 0)]
        assert [pos for pos in p.prev(Direction("Accross"))] == [Position(0, 1), Position(0, 0)]
        p = Position(2, 0)
        assert [pos for pos in p.prev_down()] == [Position(1, 0), Position(0, 0)]
        assert [pos for pos in p.prev(Direction("Down"))] == [Position(1, 0), Position(0, 0)]
        p = Position(7, 0)
        assert [pos for pos in p.prev_accross()] == []
        assert [pos for pos in p.prev(Direction("Accross"))] == []
        p = Position(0, 7)
        assert [pos for pos in p.prev_down()] == []
        assert [pos for pos in p.prev(Direction("Down"))] == []

    def test_is_filled_empty(self, board):

        board.put_on_board(Word("TEST", Direction("Accross"), Position(7, 7)))

        assert Position(7, 7).is_filled(board)
        assert not Position(7, 7).is_empty(board)

        assert Position(6, 7).is_empty(board)
        assert not Position(6, 7).is_filled(board)


class TestScrabbleWord(object):

    def word_reverse(self, word):
        word_list = [car for car in word]
        return "".join(word_list)

    def word_position(self, word):
        position_list = [position.coordinate for position in word.positions()]
        return position_list

    def test_eq_ne(self):
        mot = Word("test", Direction("Accross"), Position(7, 7))
        mot1 = Word("test", Direction("Accross"), Position(7, 7))
        mot2 = Word("teste", Direction("Accross"), Position(7, 7))

        assert mot == mot1
        assert not mot != mot1
        assert mot != mot2
        assert not mot == mot2

        mot2 = Word("test", Direction("Down"), Position(7, 7))
        assert mot != mot2
        assert not mot == mot2

        mot2 = Word("test", Direction("Accross"), Position(8, 7))
        assert mot != mot2
        assert not mot == mot2

    def test_word_creation(self):

        mot = Word("allez", Direction("Down"), Position(7, 7))
        assert self.word_reverse(mot) == "ALLEZ"
        assert self.word_position(mot) == [(7, 7), (8, 7), (9, 7), (10, 7), (11, 7)]

        mot1 = Word("malade", Direction("Accross"), Position(7, 6))
        assert self.word_reverse(mot1) == "MALADE"
        assert self.word_position(mot1) == [(7, 6), (7, 7), (7, 8), (7, 9), (7, 10), (7, 11)]

        mot2 = Word("test", Direction("Down"), Position(0, 0))
        assert self.word_reverse(mot2) == "TEST"
        assert self.word_position(mot2) == [(0, 0), (1, 0), (2, 0), (3, 0)]

        mot3 = Word("sella", Direction("Down"), Position(4, 14))
        assert self.word_reverse(mot3) == "SELLA"
        assert self.word_position(mot3) == [(4, 14), (5, 14), (6, 14), (7, 14), (8, 14)]

    @pytest.mark.parametrize("mot", [
        "1234-&",
        "12345678",
        ""
    ])
    def test_word_creation_exceptions(self, mot):
        with pytest.raises(AssertionError):
            assert Word(mot, Direction("Down"), Position(7, 7))

    @pytest.mark.parametrize("mot, subset", [
        (Word("allez", Direction("Down"), Position(7, 7)), Word("allez", Direction("Down"), Position(7, 7))),
        (Word("allez", Direction("Down"), Position(7, 7)), Word("alle", Direction("Down"), Position(7, 7))),

    ])
    def test_is_subset_true(self, mot, subset):
        assert mot.is_subset(subset)  # mot is a subset of itself

    @pytest.mark.parametrize("mot, subset", [
        (Word("allez", Direction("Down"), Position(7, 7)), Word("allezle", Direction("Accross"), Position(7, 7))),
        (Word("allez", Direction("Down"), Position(7, 7)), Word("test", Direction("Accross"), Position(0, 0))),

    ])
    def test_is_subset_false(self, mot, subset):
        assert not mot.is_subset(subset)  # mot is a subset of itself


class TestScrabbleBag(object):

    def test_bag(self, bag):

        assert len(bag) == 102
        assert bag.is_full
        temp = [bag.get_tile() for _ in range(len(bag))]

        assert bag.is_empty

        for letter in temp:
            bag.put_tile_back(letter)

        assert bag.is_full
        assert len(bag) == 102


class TestScrabbleRack(object):

    def test_rack(self, bag, rack):

        assert len(rack) == 7
        pattern = rack.get_letters()
        rack.remove_list_of_letters([l for l in pattern])
        assert len(rack) == 0
        rack.fill_rack(bag)
        assert len(rack) == 7

        rack.fill_rack_for_testing_purpose("aabcdef")
        assert rack.get_letters() == "aabcdef"
        rack.remove_list_of_letters(["a", "b"])
        assert rack.get_letters() == "acdef"


@pytest.mark.skip(reason="WIP")
class TestNode(object):

    def test_node(self):

        n = Node()
        n.edges_out["a"] = Node()
        n.edge_in = (Node(), "c")
        print("node = ", n)
        t = set()
        t.add(n)
        print(t)


@pytest.mark.skip(reason="WIP")
class TestTrie(object):

    def test_word_list(self, full_trie, lex):

        assert lex.word_set == set(full_trie._word_list(full_trie._root()))

    def test_this_is_a_valid_word(self, light_trie):

        # assert full_trie.this_is_a_valid_word("TESTENT")

        light_trie._add_word("CA")
        light_trie._add_word("CAFEINE")
        light_trie._add_word("CAFEINERA")
        assert light_trie.this_is_a_valid_word("CA")
        assert not light_trie.this_is_a_valid_word("CAFE")
        assert light_trie.this_is_a_valid_word("CAFEINE")
        assert light_trie.this_is_a_valid_word("CAFEINERA")
        assert not light_trie.this_is_a_valid_word("CAFEINERAIENT")

    def test_possible_word_set_from_string(self, full_trie):

        assert full_trie.possible_word_set_from_string("ALL Z") == ({"E"}, {"ALLEZ"})
        assert full_trie.possible_word_set_from_string("ALL S") == ({"A", "E"}, {"ALLAS", "ALLES"})

    def test_word_set_of_given_length(self, light_trie, full_trie):

        light_trie._add_word("CA")
        light_trie._add_word("ET")
        light_trie._add_word("LE")
        light_trie._add_word("CACA")
        light_trie._add_word("CAC")
        light_trie._add_word("ETE")
        light_trie._add_word("CAS")
        light_trie._add_word("ICI")
        light_trie._add_word("ICIETLA")

        assert light_trie.word_set_of_given_length(2) == {"CA", "ET", "LE"}
        assert light_trie.word_set_of_given_length(3) == {"CAC", "CAS", "ETE", "ICI"}
        assert light_trie.word_set_of_given_length(4) == {"CACA"}

        assert full_trie.word_set_of_given_length(3) == res

    def test_possible_words_for_mask_with_rack(self, full_trie, rack, bag):
        # TODO this is performance assessment only ==> real test to be impplemented

        rack.change_all_letters(bag)
        print("\n=============")
        rack.fill_rack_for_testing_purpose("AEINMLS")
        print("rack= ", rack.get_letters())
        # for w in full_trie.possible_words_for_mask_with_rack(["C",
        #                                                       dict(),
        #                                                       dict(),
        #                                                       dict(),
        #                                                       {"A", "E"},
        #                                                       "O",
        #                                                       dict(),
        #                                                       "E",
        #                                                       "T",
        #                                                       # None,
        #                                                       dict(),
        #                                                       {"U": (2, "LEU"), "C": (0, "CE")},
        #                                                       "A",
        #                                                       {},
        #                                                       "H",
        #                                                       "E"],
        #                                                      list(rack.get_letters())):
        #     print(w)
        # print(full_trie.possible_words_for_mask_with_rack([
        #                                                       "C",
        #                                                       dict(),
        #                                                       dict(),
        #                                                       dict(),
        #                                                       {"A", "E"},
        #                                                       "O",
        #                                                       dict(),
        #                                                       "E",
        #                                                       "T",
        #                                                       # None,
        #                                                       dict(),
        #                                                       {"U": (2, "LEU"), "C": (0, "CE")},
        #                                                       "A",
        #                                                       {},
        #                                                       "H",
        #                                                       "E"],
        #                                                    list(rack.get_letters()))
        #       )
        print(full_trie.possible_words_for_mask_with_rack([
            {},
            {},
            {},
            {"A": (1, "LA"), "E": (0, "ET")},
            "S",
            dict_object(),
            dict_object(),
        ],
            list(rack.get_letters()),
            5)
        )
        # assert full_trie.possible_words_for_mask_with_rack([
        #                                                       {},
        #                                                       {},
        #                                                       {},
        #                                                       {"A": (1, "LA"), "E": (0, "ET")},
        #                                                       "S",
        #                                                       dict(),
        #                                                       dict(),
        #                                                        ],
        #                                                    list(rack.get_letters()),
        #                                                    5) == {"MINASSE", "LIMASSE"}

        print("\n========= TEST TWO LETTERS ====")
        rack.fill_rack_for_testing_purpose("KKKKKEL")
        print("rack= ", rack.get_letters())
        print(sorted(list(full_trie.possible_words_for_mask_with_rack([
            {},
            {},
            # {"A": (1, "LA"), "E": (0, "ET")},
            # "S",
        ],
            list(rack.get_letters()),
            2)
        )))

        print("\n========= TEST NO JOKER ====")
        rack.fill_rack_for_testing_purpose("GRKAKKK")
        print("rack= ", rack.get_letters())
        print(sorted(list(full_trie.possible_words_for_mask_with_rack([
            {},
            {},
            {"A": (1, "LA"), "E": (0, "ET")},
            "S",
        ],
            list(rack.get_letters()),
            4)
        )))

        print("\n========= TEST ONE JOKER ====")
        rack.fill_rack_for_testing_purpose("GRAK KK")
        print("rack= ", rack.get_letters())
        print(full_trie.possible_words_for_mask_with_rack([
            {},
            {},
            {"A": (1, "LA"), "E": (0, "ET")},
            "S",
        ],
            list(rack.get_letters()),
            4)
        )

        print("\n========= TEST TWO JOKERS ====")
        rack.fill_rack_for_testing_purpose("GRK K K")
        print("rack= ", rack.get_letters())
        print(full_trie.possible_words_for_mask_with_rack([
            {},
            {},
            # {},
            {"A": (1, "LA"), "E": (0, "ET")},
            "S",
        ],
            list(rack.get_letters()),
            4)
        )


class TestScrabbleBoard(object):

    def test_adjacent_letters_2_line(self):

        # TODO TO BE COMPLETED AS OUTPUT FORMAT AS CHANGED AS COMPARE TO WORD TESTS
        # Horizontal word
        board = Board()
        horiz = Word("tic", Direction("Accross"), Position(7, 7))
        board.put_on_board(horiz)
        assert board.adjacent_letters_2_line(Line(Direction("Accross"), 7)) == {"side_lower": [], "side_higher": []}
        lower_horiz = Word("abc", Direction("Accross"), Position(6, 7))
        board.put_on_board(lower_horiz)
        higher_horiz = Word("abc", Direction("Accross"), Position(8, 7))
        board.put_on_board(higher_horiz)
        print(board.adjacent_letters_2_line(Line(Direction("Accross"), 7)))
        assert board.adjacent_letters_2_line(Line(Direction("Accross"), 7)) == {"side_lower": [Position(6, 7),
                                                                                    Position(6, 8),
                                                                                    Position(6, 9)],
                                                                     "side_higher": [Position(8, 7),
                                                                                     Position(8, 8),
                                                                                     Position(8, 9)]}
        board.print_board()

        # vertical word
        board = Board()
        vert = Word("tic", Direction("Down"), Position(7, 7))
        board.put_on_board(vert)
        assert board.adjacent_letters_2_line(Line(Direction("Down"), 7)) == {"side_lower": [], "side_higher": []}
        lower_vert = Word("abc", Direction("Down"), Position(7, 6))
        board.put_on_board(lower_vert)
        higher_vert = Word("abc", Direction("Down"), Position(7, 8))
        board.put_on_board(higher_vert)

        assert board.adjacent_letters_2_line(Line(Direction("Down"), 7)) == {
            "side_lower": [Position(7, 6),
                           Position(8, 6),
                           Position(9, 6)],
            "side_higher": [Position(7, 8),
                            Position(8, 8),
                            Position(9, 8)]}
        board.print_board()

        # Horizontal words on edges and corners
        board = Board()
        no_head_no_lower = Word("top", Direction("Accross"), Position(0, 0))
        board.put_on_board(no_head_no_lower)
        assert board.adjacent_letters_2_line(Line(Direction("Accross"), 0)) == {"side_lower": [], "side_higher": []}
        board.put_on_board((Word("a", Direction("Accross"), Position(1, 1))))
        board.put_on_board((Word("a", Direction("Accross"), Position(0, 3))))
        assert board.adjacent_letters_2_line(Line(Direction("Accross"), 0)) == {"side_lower": [],
                                                                                "side_higher": [Position(1, 1)]}
        board.print_board()

        board = Board()
        no_head_no_higher = Word("bottom", Direction("Accross"), Position(14, 0))
        board.put_on_board(no_head_no_higher)
        assert board.adjacent_letters_2_line(Line(Direction("Accross"), 14)) == {"side_lower": [], "side_higher": []}
        board.put_on_board((Word("a", Direction("Accross"), Position(14, 6))))
        board.put_on_board((Word("a", Direction("Accross"), Position(13, 3))))
        assert board.adjacent_letters_2_line(Line(Direction("Accross"), 14)) == {"side_lower": [Position(13, 3)],
                                                                                 "side_higher": []}
        board.print_board()

    def test_build_mask_for_line(self, full_trie):

        global dict_object
        dict_object = full_trie
        print(type(full_trie), type(dict_object))  # TODO dict object is of type dictionary.Trie instead of dictionary

        board = Board()
        board.put_on_board(Word("XXXX", Direction("Accross"), Position(1, 4)))
        board.put_on_board(Word("ES", Direction("Accross"), Position(2, 4)))
        board.put_on_board(Word("AS", Direction("Accross"), Position(5, 1)))
        board.put_on_board(Word("IS", Direction("Accross"), Position(5, 4)))
        board.put_on_board(Word("ENT", Direction("Down"), Position(8, 3)))
        board.print_board()
        """
           [00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 ]
        00 [_ __ __ __ __ __ __ __ __ __ __ __ __ __ __ _]
        01 [_ __ __ __ __X__X__X__X__ __ __ __ __ __ __ _]
        02 [_ __ __ __ __E__S__ __ __ __ __ __ __ __ __ _]
        03 [_ __ __ __ __ __ __ __ __ __ __ __ __ __ __ _]
        04 [_ __ __ __ __ __ __ __ __ __ __ __ __ __ __ _]
        05 [_ __A__S__ __I__S__ __ __ __ __ __ __ __ __ _]
        06 [_ __ __ __ __ __ __ __ __ __ __ __ __ __ __ _]
        07 [_ __ __ __ __ __ __ __ __ __ __ __ __ __ __ _]
        08 [_ __ __ __E__ __ __ __ __ __ __ __ __ __ __ _]
        09 [_ __ __ __N__ __ __ __ __ __ __ __ __ __ __ _]
        10 [_ __ __ __T__ __ __ __ __ __ __ __ __ __ __ _]
        11 [_ __ __ __ __ __ __ __ __ __ __ __ __ __ __ _]
        12 [_ __ __ __ __ __ __ __ __ __ __ __ __ __ __ _]
        13 [_ __ __ __ __ __ __ __ __ __ __ __ __ __ __ _]
        14 [_ __ __ __ __ __ __ __ __ __ __ __ __ __ __ _]
        """
        # print(board.build_mask_for_line(full_trie, Line(Direction("Down"), 3)))
        assert board.build_mask_for_line(Line(Direction("Down"), 3)) == Mask([
            MaskItem({}), MaskItem(None),
            MaskItem(
                {"C": WordCouple(index=0, word_str="CES"),
                 "D": WordCouple(index=0, word_str="DES"),
                 "L": WordCouple(index=0, word_str="LES"),
                 "M": WordCouple(index=0, word_str="MES"),
                 "N": WordCouple(index=0, word_str="NES"),
                 "S": WordCouple(index=0, word_str="SES"),
                 "T": WordCouple(index=0, word_str="TES"),
                 "V": WordCouple(index=0, word_str="VES")
                 }),
            MaskItem({}), MaskItem({}),
            MaskItem(
                {"S": WordCouple(index=2, word_str="ASSIS"),
                 "T": WordCouple(index=2, word_str="ASTIS")
                 }),
            MaskItem({}), MaskItem({}), MaskItem("E"), MaskItem("N"), MaskItem("T"), MaskItem({}), MaskItem({}),
            MaskItem({}), MaskItem({})
        ])

    @pytest.mark.parametrize("mask_inputs, expected",
                             [  # empty line
                                 ([{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}],
                                  []),
                                 # full line
                                 (["A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A"],
                                  []),

                                 ([{}, {}, {}, {}, "C", "E", "S", {}, {}, {}, {}, {}, {}, {}, {}],
                                  [Position(3, 7)]),

                                 ([{}, {}, None, {}, "C", "E", "S", {}, {}, {}, {}, {}, {}, {}, {}],
                                  [Position(3, 7)]),

                                 ([{}, {}, {}, None, "C", "E", "S", {}, {}, {}, {}, {}, {}, {}, {}],
                                  [Position(3, 7)]),
                                 # single blank between two words
                                 ([{}, "E", "S", {}, "L", "E", {}, {}, {}, {}, {}, {}, {}, {}, {}],
                                  [Position(0, 7), Position(3, 7)]),
                                 # last position empty with non blank on pos 13
                                 ([{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, None, {}, "T", "E", {}],
                                  [Position(11, 7)]),
                             ])
    def test_get_anchor_positions(self, board, mask_inputs, expected):
        mask = Mask([MaskItem(m) for m in mask_inputs])
        assert board.get_anchor_positions_from_line(Line(Direction("Down"), 7), mask) == expected

    @pytest.mark.parametrize("mask_inputs, expected", [
        (  # empty line - no solution as no hook
         [{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}],
         []),
        # full line - could be a 15 letter word !
        (["A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A"],
         [AnchorTuple(Position(0, 7), 0)]),
        # regular case
        ([{}, {}, {}, {}, "C", "E", "S", {}, {}, {}, {}, {}, {}, {}, {}],
         [AnchorTuple(Position(3, 7), 0),
          AnchorTuple(Position(3, 7), 1),
          AnchorTuple(Position(3, 7), 2),
          AnchorTuple(Position(3, 7), 3),
          AnchorTuple(Position(3, 7), 4)]),
        # None before word returns only word
        ([{}, {}, {}, None, "C", "E", "S", {}, {}, {}, {}, {}, {}, {}, {}],
         [AnchorTuple(Position(3, 7), 4)]),
        # single blank yields only scan of word on right
        ([{}, {}, {}, None, "C", "E", "S", {}, "F", "I", {}, {}, {}, {}, {}],
         [AnchorTuple(Position(3, 7), 4),
          AnchorTuple(Position(7, 7), 8)]),
        #
        (["C", "E", "S", {}, "F", "I", {}, {}, {}, {}, {}, {}, {}, {}, {}],
         [AnchorTuple(Position(0, 7), 0),
          AnchorTuple(Position(3, 7), 4)]),
        #
        ([{}, {}, {}, None, "C", "E", "S", {}, {}, "F", "I", {}, {}, {}, {}],
         [AnchorTuple(Position(3, 7), 4),
          AnchorTuple(Position(8, 7), 8),
          AnchorTuple(Position(8, 7), 9)]),
        # limit worfscanning to 7 tile
        ([{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, "F", "I"],
         [AnchorTuple(Position(12, 7), 6),
          AnchorTuple(Position(12, 7), 7),
          AnchorTuple(Position(12, 7), 8),
          AnchorTuple(Position(12, 7), 9),
          AnchorTuple(Position(12, 7), 10),
          AnchorTuple(Position(12, 7), 11),
          AnchorTuple(Position(12, 7), 12),
          AnchorTuple(Position(12, 7), 13)]),
        # unique word starting on edge
        (["F", "I", {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}],
         [AnchorTuple(Position(0, 7), 0)]),

    ])
    def test_build_left_mask_list(self, board, mask_inputs, expected):
        mask = Mask([MaskItem(m) for m in mask_inputs])
        assert board.build_left_masks_list(Line(Direction("Down"), 7), mask) == expected

    def test_put_on_board(self, board):

        tic = Word("tic", Direction("Accross"), Position(7, 7))
        board.put_on_board(tic)
        assert board.word_set == {tic}
        assert board.position_to_words == {
            Position(7, 7): [tic],
            Position(7, 8): [tic],
            Position(7, 9): [tic]
        }
        tics = Word("tics", Direction("Accross"), Position(7, 7))
        board.put_on_board(tics)
        assert board.word_set == {tics}
        assert board.position_to_words == {
            Position(7, 7): [tics],
            Position(7, 8): [tics],
            Position(7, 9): [tics],
            Position(7, 10): [tics]
        }

    @pytest.mark.skip(reason="WIP")
    def test_find_best_word_for_rack(self, lex, board, rack):

        rack.fill_rack_for_testing_purpose("AEIPRRX")
        assert str(board.find_best_solution_for_rack(lex, rack)) == str((54, Word("EXPIRA", Direction("Accross"), Position(7, 2))))

        rack.fill_rack_for_testing_purpose("ADEIMNT")
        assert str(board.find_best_solution_for_rack(lex, rack)) == str((72, Word("DEMINAT", Direction("Accross"), Position(7, 1))))

    @pytest.mark.parametrize("word, expected_value", [
        # first word is doubled as using Position(7,7)
        (Word("desk", Direction("Accross"), Position(7, 4)), 28),
        # scrabble with triple letters
        (Word("etiolent", Direction("Down"), Position(2, 5)), 62),
        # double letter and double word
        (Word("vermet", Direction("Accross"), Position(3, 0)), 28),
        # Scrabble with double letters
        (Word("floutas", Direction("Down"), Position(1, 8)), 62),
        # double letter with triple word
        (Word("Zorro", Direction("Down"), Position(0, 0)), 45),
    ])
    def test_compute_word_value(self, board, word, expected_value):
        # remember that compute woord doesn(t compute value of cross words - this is done at Solution level
        # So here only very elementary tests are performed
        assert board.compute_word_value(word) == expected_value

    @pytest.mark.skip(reason="WIP")
    def test_get_potential_solutions_for_line(self, full_trie, rack, board, board_populated):
        rack.fill_rack_for_testing_purpose("ABCDEFG")
        # board.put_on_board(Word("test", Direction("Down"), Position(4, 1)))
        board.put_on_board(Word("XXXXX", Direction("Accross"), Position(9, 2)))
        board.put_on_board(Word("is", Direction("Accross"), Position(13, 2)))
        board.put_on_board(Word("e", Direction("Down"), Position(14, 1)))

        board.print_board()
        line = Line(Direction("Down"), 1)
        print(rack)
        print(line)

        print(board.get_potential_solutions_for_line(full_trie, line, rack))

        # board_populated.print_board()
        # print(rack)
        # print(line)
        #
        # print(board_populated.get_potential_solutions_for_line(full_trie, line, rack))
        # print(board_populated.get_potential_solutions_for_line(full_trie, Line(Direction("Accross"), 5), rack))

        # board.put_on_board(Word("LASSE", Direction("Down"), Position(2, 0)))
        # board.put_on_board(Word("VISSE", Direction("Down"), Position(8, 0)))
        # board_populated.print_board()
        # for _ in range(1):
        #     rack.change_all_letters()
        #     print("RACK= |", rack, "|")
        #     for direction in [Direction("Accross"), Direction("Down")]:
        #         for index in range(15):
        #             line = Line(direction, index)
        #             print("    ", line)
        #             print(board_populated.get_potential_solutions_for_line(full_trie, line, rack))
        # print(board_populated.get_potential_solutions_for_line(es, Direction("Accross"), 2, rack))

    @pytest.mark.skip(reason="WIP")
    def test_get_potential_solutions_for_line_new(self, full_trie, board_populated, rack):

        rack.fill_rack_for_testing_purpose("AEIMNLS")

        board_populated.print_board()
        # board_populated.get_potential_solutions_for_line(
        #     light_trie,
        #     Line(Direction("Down"), 2),
        #     rack)
        #
        # board_populated.get_potential_solutions_for_line(
        #     light_trie,
        #     Line(Direction("Down"), 3),
        #     rack)
        for _ in range(1):
            # rack.change_all_letters()
            print(rack)
            for i in range(15):
                for direction in [Direction("Accross"), Direction("Down")]:
                    print(i, direction)
                    board_populated.get_potential_solutions_for_line(
                        full_trie,
                        Line(direction, i),
                        rack)


class TestSolution(object):

    def test_solution_value(self, board, load_solution_list_4_word_computation_checks):
        """Check correctness of word value computation """
        for sol in load_solution_list_4_word_computation_checks:
            val = board.compute_word_value(sol.main_word, sol.joker_set)
            joker_index_list = {joker_tuple.index for joker_tuple in sol.joker_set}
            for crossword in sol.cross_word_list:
                joker_at_crossing = True if sol.main_word.intersection_index(crossword.word) in joker_index_list \
                                         else False
                val += board.compute_cross_word_value(crossword, joker_at_crossing)
            assert val == sol.value
            board.put_on_board(sol.main_word, sol.joker_set)
            board.print_board()


class TestSchema(object):
    """Test Mashmallow Schemas for the various classes of the project"""

    def test_joker_tuple_schema(self):

        jt = JokerTuple(1, "F")
        ret = JokerTupleSchema().dumps(jt)

        print(ret)

        imp = JokerTupleSchema().loads(ret)

        print(imp)

        assert imp == jt

    def test_direction_schema(self):

        d = Direction("Down")
        ret = DirectionSchema().dumps(d)

        print(ret)
        #
        imp = DirectionSchema().loads(ret)

        print(imp)
        #
        assert imp == d

    def test_position_schema(self):

        p = Position(1, 2)

        ret = PositionSchema().dumps(p)

        print(ret)

        imp = PositionSchema().loads(ret)

        print(type(imp), imp)

        assert imp == p

    def test_word_schema(self):

        w = Word("test", Direction("Accross"), Position(0, 0))

        ret = WordSchema().dumps(w)

        print(ret)

        imp = WordSchema().loads(ret)

        print(type(imp), imp)

        assert imp == w

    def test_rack_schema(self, bag, rack):

        ret = RackSchema().dumps(rack)

        print(ret)

        imp = RackSchema().loads(ret)

        print(type(imp), imp)

        assert imp == rack

    def test_cross_word_schema(self, bag, rack):

        cw = CrossWord(Word("test", Direction("Down"), Position(1, 2)), index_of_main_word_line=1)

        ret = CrossWordSchema().dumps(cw)

        print(ret)

        imp = CrossWordSchema().loads(ret)

        print(type(imp), imp)

        assert imp == cw

    def test_bag_of_tile_schema(self, bag, rack):

        bag = BagOfTile()

        ret = BagOfTileSchema().dumps(bag)

        print(ret)

        imp = BagOfTileSchema().loads(ret)

        print(type(imp), imp)

        assert imp == bag

    def test_board_schema(self, board_populated):

        ret = BoardSchema().dumps(board_populated)

        print(json.dumps(json.loads(ret), indent=4))

        imp = BoardSchema().loads(ret)

        print(type(imp), imp)

        assert imp == board_populated

    def test_solution_schema(self, solution_with_cross_word_and_joker_new):
        ret = SolutionSchema().dumps(solution_with_cross_word_and_joker_new)

        print(ret)

        imp = SolutionSchema().loads(ret)

        print(imp)
        #
        assert imp == solution_with_cross_word_and_joker_new

    def test_play_item_schema(self, play_item_list):

        ret_list = PlayItemSchema(many=True).dumps(play_item_list)

        print(ret_list)

        imp_list = PlayItemSchema(many=True).loads(ret_list)

        assert all("".join(play_item.tile_list) == "".join(imp.tile_list)
                   and play_item.solution == imp.solution
                   for play_item, imp in zip(play_item_list, imp_list)
                   )

    def test_game_record_schema(self, game_record):

        ret = GameRecordSchema().dumps(game_record)

        print(ret)

        imp = GameRecordSchema().loads(ret)

        print(type(imp), imp)

        assert imp == game_record

    # @pytest.mark.skip(reason="WIP")
    def test_game_schema(self, game_sample):

        ret = GameSchema().dumps(game_sample)

        print("ret ==> ", ret)

        imp = GameSchema().loads(ret)

        print(type(imp), imp)

        assert imp == game_sample
    # @pytest.mark.skip(reason="WIP")


class TestGamePerformance(object):

    @pytest.mark.parametrize("nb_cycle, duration_limit", [
        (1, 5)  # 10 games with an average duration per game shorter than 2s
    ])
    def test_game_auto(self, load_dictionary, nb_cycle, duration_limit):
        players_ordered_dict = OrderedDict({"Thibault": "auto",
                                            "Unbeatable": "auto"})

        game_duration = []
        for i in range(nb_cycle):
            t = time.time()
            game = Game(players_dict=players_ordered_dict)
            while not game.automatic_play(record=True):
                pass
            game_duration.append(time.time() - t)
            print(game.board.print_board())
            print(game.game_record.get_formated_game_summary())
            # if solution_dump_found:
            #     break
            with open("test-scenario\game_record_test.json", "w") as fp:
                fp.write(GameRecordSchema().dumps(game.game_record))
            print(pretty_print_json(GameRecordSchema().dumps(game.game_record)))  # TODO WORK ON GOING TO BE REMOVED

        print(game_duration)
        print("max=", max(game_duration))
        print("min=", min(game_duration))
        print("avg=", sum(game_duration) / len(game_duration))

        assert sum(game_duration) / len(game_duration) <= duration_limit

    @pytest.mark.parametrize("nb_cycle, duration_limit", [
        (5, 2.3)  # 10 games with an average duration per game shorter than 2s
    ])
    def test_game_manual_all_skip(self, load_dictionary, nb_cycle, duration_limit):
        players_ordered_dict = OrderedDict({"Thibault": "manual",
                                            "Unbeatable": "auto"})

        # with open("test-scenario/game_1.json", "w") as fp:
        game_duration = []
        for i in range(nb_cycle):
            t = time.time()
            game = Game(players_dict=players_ordered_dict)
            while not game.manual_play(player_name="Thibault", play_instruction=(SKIP, None)):
                pass
            # fp.write(GameSchema().dumps(game))
            game_duration.append(time.time() - t)
            print(game.board.print_board())
            print(game.game_record.get_formated_game_summary())

        print(game_duration)
        print("max=", max(game_duration))
        print("min=", min(game_duration))
        print("avg=", sum(game_duration) / len(game_duration))

        assert sum(game_duration) / len(game_duration) <= duration_limit


class TestProposedWord(object):

    def test_create_validate(self):
        res = proposed_word(word_struct=
        {
            "word": {"text": "TEST",
                     "origin": {"row": 8, "col": 1},
                     "direction": {"down": "true"}},
            "word_mask": "TEST"
        }
        )
        print(res)
        # assert not res["errors"]


class TestProposedPlay(object):

    # TODO check all parameter validation cases
    def test_proposed_play_validation(self, load_dictionary, board):
        input = '{"proposed_word": {\
            "word": {"text": "TEST",\
                     "origin": {"row": 8, "col": 1},\
                     "direction": {"down": "true"}},\
            "word_mask": "TEST"},\
            "type_of_play": {"type_of_play": "1"},\
            "board": {\
                "board": [\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " ",\
                    " "\
                ],\
                "board_values": [\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0,\
                    0\
                ],\
                "nb_moves": 0,\
                "position_to_words": {},\
                "word_set": []\
                    }\
                }'

        # input2 = '{"proposed_word":  null, "type_of_play": {"type_of_play": "2"}}'
        input2 = '{"type_of_play": {"type_of_play": "3"}}'

        p = ProposedPlaySchema()

        try:
            ret = p.loads(input)
        except ValidationError as e:
            print(e)
            raise ValueError("".join([k + "==>" + str(v) + "\n" for k, v in e.messages.items()]))

        type_of_play, sol = ret
        print(type_of_play,
              sol)


class TestGameStateless(object):

    def test_start_game(self):

        res = start_game(lang="Français", player_name="JoeBlow")

        print("res ==>", res)
        print(pretty_print_json(res))

    @pytest.mark.skip(reason="NEED_WEB_SITE")
    def test_start_game_hug(self):

        # url = "http://localhost:8000/start_game"
        url = "http://localhost/start_game"  # nginx access on default port 80

        params = {"lang": "Français",
                  "player_name": "JoeBlow"}

        r = requests.post(url=url, json=params)

        print(r.status_code)
        print(r.headers)
        print(r.content)
        data = r.json()

        print(data)

    def test_start_game_hug_test(self):

        player_name = "JoeBlow"

        params = {"lang": "Français",
                  "player_name": player_name}

        for _ in range(100):
            r = hug.test.post(scrabble, "start_game", params=params)
            print("status=", r.status)
            print("data=", r.data)
            assert r.status == "200 OK"

    def test_play_4_player(self):

        game_over = False
        player_name = "JoeBlow"
        game_json_stringinfyied = start_game(lang="Français", player_name=player_name)

        res_dict = json.loads(game_json_stringinfyied)
        game_json_stringinfyied = res_dict['game']

        while not game_over:
            res_dict = json.loads(
                play_4_player(player_name=player_name,
                              raw_proposed_play={"type_of_play": {"type_of_play": "2"}},
                              game=json.loads(game_json_stringinfyied))
            )
            game_over = res_dict['game_over']
            game_json_stringinfyied = res_dict['game']
            # print(game_json_stringinfyied)

        print(game_json_stringinfyied)

    @pytest.mark.skip(reason="NEED_WEB_SITE")
    def test_play_4_player_hug(self):

        # http_server = "http://localhost:8000/"  # direct access to hug or waitress
        http_server = "http://localhost/"  # nginx access on default port 80
        player_name = "JoeBlow"

        params = {"lang": "Français",
                  "player_name": player_name}

        r = requests.post(url=http_server + "start_game", json=params)
        print(r.status_code == requests.codes.ok)
        print(r.headers)
        game_json = r.json()
        print(game_json)

        game_over = False
        while not game_over:
            params = {"player_name": player_name,
                      "proposed_play": {"type_of_play": {"type_of_play": "2"}},
                      "game": json.loads(game_json)}
            r = requests.post(url=http_server + "play_4_player", json=params)
            print("HTTP response code: ", r.status_code)
            if r.status_code != 200:
                print("Request failed with HTTP error code: %s" % HTTP_STATUS_CODES[r.status_code])
                break

            # print(r.headers)
            result_dict = json.loads(r.json())
            game_json = result_dict['game']
            game_over = result_dict['game_over']
            # print(result_dict)
            print(game_json)

    @pytest.mark.skip(reason="NEED_WEB_SITE")
    def test_ping_hug(self):

        # url = "http://localhost:8000/ping_hug"  # direct access to hug or waitress
        url = "http://localhost/ping_hug"  # nginx access on default port 80
        test = "OK hug is functional"
        for i in range(3):
            r = requests.get(url=url, json={"test": test})
            assert r.status_code == 200
            assert r.json() == test

            # print("HTTP response code: ", r.status_code)
            # if r.status_code != 200:
            #     print("Request failed with HTTP error code: %s" % HTTP_STATUS_CODES[r.status_code])
            #     break
            # print(r.headers)
            # data = r.json()
            # print(data)

    def test_ping_hug_test(self):

        test = "OK hug is functional"
        for i in range(3):
            r = hug.test.get(scrabble, "ping_hug", params={"test": test})
            print("status=", r.status)
            print("data=", r.data)
            assert r.status == "200 OK"
            assert r.data == test


