"""Describes the SeqRes dataclass which is used to annotate a protein's 
sequence and describe which amino acids are present and which are missing.

Author: Chris Jurich <chris.jurich@vanderbilt.edu>
Date: 2024-05-28
"""

from __future__ import annotations
from typing import Tuple
from dataclasses import dataclass

from .residue import convert_to_one_letter, THREE_LETTER_AA_MAPPER

@dataclass
class SeqRes:
    """Simple dataclass representing a Sequence Residue or SeqRes. In this description,
    each residue has a chain id, index, name, and may or may not be missing. Since it can
    be missing, it is used to represent the total sequence of a protein, including which
    residues are missing. Note that for sorting, the (chain id, idx) key is used.
    """
    model:int
    chain:str
    idx:int
    name:str
    missing:bool
    seq_idx:int

    def one_letter(self) -> str:
        """What is this residue's one letter code?"""
        return convert_to_one_letter(self.name)

    @property
    def key(self) -> Tuple[str, int]:
        """The residues (chain id, idx) key."""
        return (self.chain, self.idx)

    def is_canonical(self) -> bool:
        """Is this residue one of the 20 canonical amino acids?"""
        return self.name in THREE_LETTER_AA_MAPPER

    def same_aa(self, other: SeqRes) -> bool:
        """Do these two SeqRes objects have the same amino acid?"""
        return self.one_letter() == other.one_letter()

    def __gt__(self, other: SeqRes) -> bool:
        return self.key > other.key


    def __lt__(self, other:SeqRes) -> bool:
        return self.key < other.key


def same_aa_sequence( list_a:List[SeqRes], list_b:List[SeqRes]) -> bool:
    """Do the two List[SeqRes] have the same amino acid sequence? Fail if not the same length
    or if the two have different amino acid identities.

    Args:
        list_a: First List[SeqRes] to compare.
        list_b: First List[SeqRes] to compare.
    
    Returns:
        Whether the two List[SeqRes] have the same amino acid sequence.
    """
    if len(list_a) != len(list_b):
        return False

    for la, lb in zip(list_a, list_b):
        if not la.same_aa( lb ):
            return False

    return True
