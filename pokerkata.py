#!/usr/local/bin/python3

from enum import Enum
from functools import total_ordering
from collections import defaultdict
import re
     
class Suit(Enum): CLUBS = 'C'; DIAMONDS = 'D'; HEARTS = 'H'; SPADES = 'S'

class Face:
    # the order in which they are listed determines their sort value in poker, ascending
    faces = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']

    def __init__(self, rep):
      self.value = Face.faces.index(rep)
      self.rep = rep

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return self.value == other.value
        return NotImplemented
      
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    def __repr__(self):
        return self.rep

    def __hash__(self):
        return hash(self.rep)

@total_ordering
class Card:
    def __init__(self, face, suit):
        self.face = face
        self.suit = suit

    def __repr__(self):
        return self.face.rep + self.suit.value

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return self.face == other.face
        return NotImplemented

    def __hash__(self):
        return hash((self.face, self.suit))

    # in poker, cards are only ever compared by face, never by suit
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.face.value < other.face.value
        return NotImplemented
        
    @staticmethod
    def fromRep(rep):
        return Card(Face(rep[0]), Suit(rep[1]))

class Hand:
    def __init__(self, colour, cards):
        self.colour = colour
        self.cards = cards
        self.faceCounts = {face: len(cardList) for (face, cardList) in self._grouped(lambda x: x.face).items()}
        self.suitCounts = {suit: len(cardList) for (suit, cardList) in self._grouped(lambda x: x.suit).items()}
        
    def __repr__(self):
        return self.colour + ': ' + str(self.cards)

    def descending(self):
        return sorted(self.cards, reverse=True)

    def _grouped(self, fun):
        grouped = defaultdict(list)
        for card in self.cards:
            grouped[fun(card)].append(card)
        return grouped

    def _facesOccuringTimes(self, numTimes):
        return sorted([face for face in self.faceCounts if self.faceCounts[face]==numTimes], reverse=True)

    def _suitsOccuringTimes(self, numTimes):
        return [suit for suit in self.suitCounts if self.suitCounts[suit]==numTimes]
    
    def pair(self):
        pairFaces = self._facesOccuringTimes(2)
        if pairFaces:
            return (pairFaces[0], Hand(self.colour, {card for card in self.cards if card.face!=pairFaces[0]}))
        else:
            return (None, self)

    def pairs(self):
        pairFaces = self._facesOccuringTimes(2)
        if len(pairFaces)>=2:
            return (pairFaces[0], pairFaces[1], Hand(self.colour, {card for card in self.cards if card.face not in (pairFaces[0], pairFaces[1])}))
        else:
            return (None, None, self)

    def triplet(self):
        tripletFaces = self._facesOccuringTimes(3)
        if tripletFaces:
            return (tripletFaces[0], Hand(self.colour, {card for card in self.cards if card.face!=tripletFaces[0]}))
        else:
            return (None, self)

    def straight(self):
        descendingFaceValues = [card.face.value for card in self.descending()]
        if( descendingFaceValues[0] - 1 == descendingFaceValues[1] and
            descendingFaceValues[1] - 1 == descendingFaceValues[2] and
            descendingFaceValues[2] - 1 == descendingFaceValues[3] and
            descendingFaceValues[3] - 1 == descendingFaceValues[4] ):
            return self.descending()[0].face

    def isFlush(self):
        return self._suitsOccuringTimes(5)

    def fullHouse(self):
        triplet, remainingHand = self.triplet()
        if triplet:
            pair, remainingHand = remainingHand.pair()
            if pair:
                return triplet

    def quartet(self):
        quartetFaces = self._facesOccuringTimes(4)
        if quartetFaces:
            return (quartetFaces[0], Hand(self.colour, {card for card in self.cards if card.face!=quartetFaces[0]}))
        else:
            return (None, self)
        
    @staticmethod
    def fromRep(rep):
        match = re.match('(.*): (.*)', rep)
        colour, cardreps = match.group(1), set(match.group(2).split(' '))
        return Hand(colour, {Card.fromRep(cardrep) for cardrep in cardreps})

class InvalidCardDeck(Exception): pass

class Result:
    def __init__(self, outcome, winningColour=None, reason=None):
        self.outcome = outcome
        self.winningColour = winningColour
        self.reason = reason

    def __eq__(self, other):
        return (self.outcome == other.outcome) and (self.winningColour == other.winningColour) and (self.reason == other.reason)

    def isDraw(self):
        return self.outcome == 'draw'

    @staticmethod
    def draw():
        return Result('draw')
    
    @staticmethod
    def fromRep(rep):
        try:
          match = re.match('Win (.*?), (.*)', rep)
          winningColour, reason = match.group(1), match.group(2)
          return Result('win', winningColour, reason)
        except Exception as exc:
          #print(exc)
          return Result.draw()

def compareFaces(face1, face2, hand1, hand2, reason):
    if face1 > face2: return Result('win', hand1.colour, reason + ': ' + str(face1) + ' over ' + str(face2))
    if face2 > face1: return Result('win', hand2.colour, reason + ': ' + str(face2) + ' over ' + str(face1))
    return Result.draw()

def neitherOrOnlyOne(appliesTo1, appliesTo2, hand1, hand2, reason):
    if not appliesTo1 and not appliesTo2: return None
    if     appliesTo1 and not appliesTo2: return Result('win', hand1.colour, reason)
    if not appliesTo1 and     appliesTo2: return Result('win', hand2.colour, reason)
    return Result.draw()

def highCard(hand1, hand2, reason='High Card'):
    def deepComparison(sortedCardToCard, reason):
        if sortedCardToCard:
            (highestCard1, highestCard2) = sortedCardToCard[0]
            result = compareFaces(highestCard1.face, highestCard2.face, hand1, hand2, reason)
            if result.isDraw(): return deepComparison(sortedCardToCard[1:], reason)
            else: return result
        else:
            return Result.draw()
    return deepComparison(list(zip(hand1.descending(), hand2.descending())), reason)

def twoOfAKind(hand1, hand2, reason='Two of a Kind'):
    (pairFace1, remainingHand1), (pairFace2, remainingHand2) = hand1.pair(), hand2.pair()
    result = neitherOrOnlyOne(pairFace1, pairFace2, hand1, hand2, reason)
    if not result: return result
    if result.isDraw():
        result = compareFaces(pairFace1, pairFace2, hand1, hand2, reason)
        if result.isDraw():
          result = highCard(remainingHand1, remainingHand2, reason)
    return result

def twoPairs(hand1, hand2, reason='Two Pairs'):
    (highPairFace1, lowPairFace1, remainingHand1), (highPairFace2, lowPairFace2, remainingHand2) = hand1.pairs(), hand2.pairs()
    result = neitherOrOnlyOne(highPairFace1 and lowPairFace1, highPairFace2 and lowPairFace2, hand1, hand2, reason)
    if not result: return result
    if result.isDraw():
        result = compareFaces(highPairFace1, highPairFace2, hand1, hand2, reason)
        if result.isDraw():
          result = compareFaces(lowPairFace1, lowPairFace2, hand1, hand2, reason)
          if result.isDraw():
            result = highCard(remainingHand1, remainingHand2, reason)
    return result

def threeOfAKind(hand1, hand2, reason='Three of a Kind'):
    (tripletFace1, remainingHand1), (tripletFace2, remainingHand2) = hand1.triplet(), hand2.triplet()
    result = neitherOrOnlyOne(tripletFace1, tripletFace2, hand1, hand2, reason)
    if not result: return result
    if result.isDraw():
        result = compareFaces(tripletFace1, tripletFace2, hand1, hand2, reason)
        if result.isDraw():
          raise InvalidCardDeck('Two triplets with same faces?')
    return result

def straight(hand1, hand2, reason='Straight'):
    straightFace1, straightFace2 = hand1.straight(), hand2.straight()
    result = neitherOrOnlyOne(straightFace1, straightFace2, hand1, hand2, reason)
    if not result: return result
    if result.isDraw():
        return compareFaces(straightFace1, straightFace2, hand1, hand2, reason) # this one CAN draw
    return result

def flush(hand1, hand2, reason='Flush'):
    result = neitherOrOnlyOne(hand1.isFlush(), hand2.isFlush(), hand1, hand2, reason)
    if not result: return result
    if result.isDraw():
        return highCard(hand1, hand2, reason)
    return result

def fullHouse(hand1, hand2, reason='Full House'):
    tripletFace1, tripletFace2 = hand1.fullHouse(), hand2.fullHouse()
    result = neitherOrOnlyOne(tripletFace1, tripletFace2, hand1, hand2, reason)
    if not result: return result
    if result.isDraw():
        result = compareFaces(tripletFace1, tripletFace2, hand1, hand2, reason)
        if result.isDraw():
            raise InvalidCardDeck('Two triplets with same faces?')
    return result
    
def fourOfAKind(hand1, hand2, reason='Four of a Kind'):
    (quartetFace1, remainingHand1), (quartetFace2, remainingHand2) = hand1.quartet(), hand2.quartet()
    result = neitherOrOnlyOne(quartetFace1, quartetFace2, hand1, hand2, reason)
    if not result: return result
    if result.isDraw():
        result = compareFaces(quartetFace1, quartetFace2, hand1, hand2, reason)
        if result.isDraw():
          raise InvalidCardDeck('Two quartets with same faces?')
    return result

def straightFlush(hand1, hand2, reason='Straight Flush'):
    result = neitherOrOnlyOne(hand1.straight() and hand1.isFlush(), hand2.straight() and hand2.isFlush(), hand1, hand2, reason)
    if not result: return result
    if result.isDraw():
        return highCard(hand1, hand2, reason)
    return result

def rank(hand1, hand2):
    for category in [straightFlush, fourOfAKind, fullHouse, flush, straight, threeOfAKind, twoPairs, twoOfAKind, highCard]:
        result = category(hand1, hand2)
        if result: return result

if __name__ == '__main__':

  testCases = [
      # Suggested test cases from the KATA, but not there they do indeed rank 3rd case wrong!
      ("Black: 2H 3D 5S 9C KD  White: 2C 3H 4S 8C AH", "Win White, High Card: A over K"),
      ("Black: 2H 4S 4C 2D 4H  White: 2S 8S AS QS 3S", "Win Black, Full House"),
      ("Black: 2H 3D 5S 9C KD  White: 2C 3H 4S 8C KH", "Win Black, High Card: 9 over 8"),
      ("Black: 2H 3D 5S 9C KD  White: 2D 3H 5C 9S KH", "Draw"),

      # High Card
      ("Black: 2D 3D 4D 5D 7D  White: 2C 3C 4C 5C 7C", "Draw"), # exact same faces all the way through
      ("Black: 2D 3C 6D 7D 8D  White: 2H 4C 6C 7C 8C", "Win White, High Card: 4 over 3"), # highest 3 faces same, but fourth makes white win
      ("Black: 2D 3C 4D 6D 8D  White: 2H 3C 4C 6C 7C", "Win Black, High Card: 8 over 7"), # highest face for black

      # Two of a Kind
      ("Black: 2D 3D 4D 5D 7D  White: 2C 3C 4C 5C 7C", "Not Ranked"), # no pairs
      ("Black: 2D 2C 4D 5D 6D  White: 2H 3C 4C 5C 7C", "Win Black, Two of a Kind"), # black has only pair
      ("Black: 2D 3D 4D 5D 7H  White: 2C 2H 4C 5C 6C", "Win White, Two of a Kind"), # white has only pair
      ("Black: 2D 2S 4D 5D 6D  White: 2C 2H 4C 5C 6C", "Draw"), # both have a pair, with same face value, and all remaining cards also match by face value
      ("Black: 2D 2C 4D 5D 6D  White: 3C 3H 4C 5C 6C", "Win White, Two of a Kind: 3 over 2"), # both have a pair, but white higher face
      ("Black: 4D 4C 7H 5D 6D  White: 2C 2H 4S 5C 6C", "Win Black, Two of a Kind: 4 over 2"), # both have a pair, but black higher face
      ("Black: 4D 4C 7D 5D 6D  White: 4H 4S 8D 5C 6C", "Win White, Two of a Kind: 8 over 7"), # both have a pair, but white has higher face on remaining cards

      # Two Pairs
      ("Black: 2D 3D 4D 5D 7D  White: 2C 3C 4C 5C 7C", "Not Ranked"), # no pairs
      ("Black: 2D 2C 3D 3C 6D  White: QC 2H 4C 5C 6C", "Win Black, Two Pairs"), # black has two pairs, white none
      ("Black: 2D 2S 4D 5D 6D  White: QC QH KC KS AC", "Win White, Two Pairs"), # black has one pair, white two
      ("Black: 2D 2S 3D 3S 6D  White: QC QH KC KS AC", "Win White, Two Pairs: K over 3"), # both two pairs, white has higher high pair
      ("Black: KD KS 3D 3S 6D  White: QC QH KC KH AC", "Win White, Two Pairs: Q over 3"), # both two pairs, same high pair faces, but white has higher low pair face
      ("Black: KD KS QD QS 6D  White: QC QH KC KH 2C", "Win Black, Two Pairs: 6 over 2"), # both two pairs, same high pair faces, same low pair faces, but remaining card makes black win

      # Three of a Kind
      ("Black: 2D 2C 2H 5D 6D  White: QH 3C 4C 5C 6C", "Win Black, Three of a Kind"), # black has only triplet
      ("Black: 2D 3D 4D 5D 7H  White: AC AH AD 5C 6C", "Win White, Three of a Kind"), # white has only triplet
      ("Black: 2D 2S 2H 5D 6D  White: 3D 3H 3C 5C 6C", "Win White, Three of a Kind: 3 over 2"), # both have triplet, but white the one with higher face
      ("Black: QD QS QH 5D 6D  White: AD AH AC AC 6C", "Win White, Three of a Kind: A over Q"), # both have triplet, but black the one with higher face

      # Straight
      ("Black: 2D 3C 4H 5D 6D  White: QH 3D 4C 5C 6C", "Win Black, Straight"), # black has only straight
      ("Black: 2D 3D 4D 5D 8H  White: 4C 5H 6D 7C 8C", "Win White, Straight"), # white has only straight
      ("Black: 2D 3S 4H 5D 6D  White: 3D 4D 5C 6C 7C", "Win White, Straight: 7 over 6"), # both have straight, but white the one with higher face
      ("Black: 2D 3S 4H 5D 6D  White: 2S 3D 4C 5C 6C", "Draw"), # both have a straight, with same highest face

      # Flush
      ("Black: 2D 3D 4D 5D 7D  White: QH 3H 4C 5C 6C", "Win Black, Flush"), # black has only flush
      ("Black: 2D 3D 4D 5D 8H  White: 4C 5C 6C 8C TC", "Win White, Flush"), # white has only flush
      ("Black: 2D 3D 4D 5D 8D  White: 4C 5C 6C 8C TC", "Win White, Flush: T over 8"), # both have flush, but white best high face

      # Full House
      ("Black: 2D 3D 4D 5D 7C  White: 2C 3C 4C 5H 7D", "Not Ranked"), # no full houses
      ("Black: 2D 2H 3D 3S 3C  White: QH 3H 4C 5C 6C", "Win Black, Full House"), # black has only full house
      ("Black: 2D 3D 4H 5D 8H  White: 4C 4D AS AC AD", "Win White, Full House"), # white has only full house
      ("Black: 2D 2H 3D 3S 3C  White: TC TH TD 8C 8D", "Win White, Full House: T over 3"), # both have full house, but white best high face among its triplet

      # Four of a Kind
      ("Black: 2D 2C 2H 2S 6D  White: QH 3C 4C 5C 6C", "Win Black, Four of a Kind"), # black has only quartet
      ("Black: 2D 3D 4D 7D 6H  White: AC AH AD AS 6C", "Win White, Four of a Kind"), # white has only quartet
      ("Black: TD TS TH TC 6D  White: AD AS AH AC 6C", "Win White, Four of a Kind: A over T"), # both have quartets, but white the one with higher face

      # Straight Flush
      ("Black: 2D 3D 4D 5D 6D  White: QH 3C 4C 5C 6C", "Win Black, Straight Flush"), # black has only straight flush
      ("Black: 2D 3D 4D 5D 9D  White: 6C 7C 8C 9C TC", "Win White, Straight Flush"), # white has only straight flush
      ("Black: 2D 3D 4D 5D 6D  White: 3H 4H 5H 6H 7H", "Win White, Straight Flush: 7 over 6"), # both have straight flush, but white the one with higher face
      
      # Since the individual Rankers have exhaustive unit tests each, this can focus on the question whether
      # they are applied in the right order with the right precedence
      ("Black: 2H 3H 4H 5H 6H  White: AC AH AS AS KH", "Win Black, Straight Flush"), # Straight Flush over Four of a Kind
      ("Black: 2H 2C 4H 4C 4D  White: AC AH AS AD KH", "Win White, Four of a Kind"), # Four of a Kind over Full House
      ("Black: 2H 2C 4H 4C 4D  White: 8C TC 5C 6C AC", "Win Black, Full House"), # Full House over Flush
      ("Black: 2H 3C 4H 5D 6D  White: 8C TC 5C 6C AC", "Win White, Flush"), # Flush over Straight
      ("Black: 2H 3C 4H 5D 6D  White: 8C 8D 8S 6H AC", "Win Black, Straight"), # Straight over Three of a Kind
      ("Black: 2H 2C 4H 4D 6D  White: 8C 8D 8S 6H AC", "Win White, Three of a Kind"), # Three of a Kind over Two Pairs
      ("Black: 2H 2C 4H 4D 6D  White: 8C 8D 7S 6H AC", "Win Black, Two Pairs"), # Two Pairs over Two of a Kind
      ("Black: AH 2C 4H 5D 6D  White: 8C 8D 7S 6H AC", "Win White, Two of a Kind") # Two of a Kind over High Card
    ]
  for testCase in testCases:
      handrep1, handrep2, expectedRep = *testCase[0].split('  '), testCase[1]
      hand1, hand2 = Hand.fromRep(handrep1), Hand.fromRep(handrep2)
      actual = rank(hand1, hand2)
      expected = Result.fromRep(expectedRep)
      if actual == expected:
          print('TEST OK: %s %s => %s' % (handrep1, handrep2, expectedRep))
      else:
          print('FAIL XX: %s %s => %s but actual %s' % (handrep1, handrep2, expectedRep, actual))
