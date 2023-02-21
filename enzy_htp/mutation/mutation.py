"""Submodule that defines the Mutation namedtuple() which describes a single point mutation in an 
enzyme. Additionally provides utility functions for determnining if Mutation()'s are defined
and if they satisfy certain change requirements.

Author: Chris Jurich <chris.jurich@vanderbilt.edu>
        QZ Shao <shaoqz@icloud.com>
Date: 2022-06-15
"""
import re
from collections import namedtuple
from typing import List, Dict, Tuple

from enzy_htp.core.exception import InvalidMutationFlagSyntax, InvalidMutation
from enzy_htp.core.general import get_copy_of_deleted_dict
from enzy_htp.core.logger import _LOGGER
from enzy_htp.chemical import ONE_LETTER_AA_MAPPER, THREE_LETTER_AA_MAPPER
import enzy_htp.chemical as chem
import enzy_htp.structure as es

Mutation = namedtuple("Mutation", "orig target chain_id res_idx")
Mutation.__doc__ = f"""Named tuple representing a single point mutation in an enzyme.
   

	Attributes:
   		orig: the one-letter code of the original amino acid. Can be in [ "{", ".join(ONE_LETTER_AA_MAPPER.keys())}"].
		target: the one-letter code of the target mutation. Can be in [ "{", ".join(ONE_LETTER_AA_MAPPER.keys())}"].
		chain_id: a single capital letter.
		res_idx: the 1-indexed int() of the residue to Mutate

        *In the case of WT, the tuple is defined as (None, "WT", None, None)
"""

SUPPORTED_MUTATION_TARGET_LIST = get_copy_of_deleted_dict(ONE_LETTER_AA_MAPPER, "U")
"""The list of EnzyHTP supported mutation target-residue list.
add upon supporting. will do ncaa in the future"""

def generate_from_mutation_flag(mutation_flag: str) -> Mutation:
    """XA##Y -> ("X", "Y", "A", ##)
    WT -> (None, "WT", None, None)
    XA##X -> (None, "WT", None, None)
    *we may need to support 3-letter mutation in the future like: TYQA##TYP"""

    mutation_flag = mutation_flag.strip()
    if mutation_flag == "WT":
        return Mutation(None, "WT", None, None)
    pattern = r"([A-Z])([A-Z])?([0-9]+)([A-Z])"
    flag_match = re.match(pattern, mutation_flag)
    if flag_match is None:
        raise InvalidMutationFlagSyntax(
            f"{mutation_flag} doesnt match ([A-Z])([A-Z])?([0-9]+)([A-Z])"
            )

    orig = flag_match.group(1)
    chain_id = flag_match.group(2)
    res_idx = int(flag_match.group(3))
    target = flag_match.group(4)

    if chain_id is None:
        chain_id = "A"
        _LOGGER.info(
            f"No chain id is provided in: {mutation_flag}. Using A as default."
        )
    if orig == target:
        _LOGGER.warning(f"equivalent mutation detected in {mutation_flag}. Making it WT.")
        return Mutation(None, "WT", None, None)

    return Mutation(orig, target, chain_id, res_idx)

def is_valid_mutation(mut: Mutation, stru: es.Structure) -> bool:
    """Checks if the supplied Mutation() namedtuple is valid according to the below criteria:
    (Non-WT cases)
    Mutation.orig: if match the original residue in the {stru}
    Mutation.target: a one-letter amino-acid code in the allowed list & different from orig
    Mutation.chain_id: should exist in {stru}
    Mutation.res_idx: should exist in {stru}

    Args:
        mut: The Mutation() namedtuple to be judged.
        stru: the reference structure

    Raise:
        enzy_htp.core.exception.InvalidMutation
    Returns:
        True if the Mutation() passes all checks.
    """
    # WT case
    if mut == (None, "WT", None, None):
        return True

    # get data type right
    if (not isinstance(mut.orig, str) or not isinstance(mut.target, str)
            or not isinstance(mut.chain_id, str)
            or not isinstance(mut.res_idx, int)):
        raise InvalidMutation(f"wrong data type in: {mut}")

    # Mutation.chain_id, Mutation.res_idx: should exist in {stru}, should not be empty
    if mut.chain_id.strip() is "":
        raise InvalidMutation(f"empty chain_id in: {mut}")
    if mut.chain_id not in stru.chain_mapper:
        raise InvalidMutation(
            f"chain id in {mut} does not exist in structure (in-stru: {stru.chain_mapper.keys()})"
        )
    if mut.res_idx not in stru[mut.chain_id].residue_idxs:
        raise InvalidMutation(
            f"res_idx in {mut} does not exist in structure (in-stru: {stru[mut.chain_id].residue_idx_interval()})"
        )

    # Mutation.orig: if match the original residue in the {stru}
    real_orig = stru[mut.chain_id].find_residue_idx(mut.res_idx).name
    real_orig = THREE_LETTER_AA_MAPPER.get(real_orig, real_orig) # 1 letter if in the map; 3 letter if not
    if real_orig != mut.orig:
        raise InvalidMutation(f"original residue does not match in: {mut} (real_orig: {real_orig})")

    # Mutation.target: a one-letter amino-acid code in the allowed list & different from orig
    if mut.target not in SUPPORTED_MUTATION_TARGET_LIST:
        raise InvalidMutation(f"unsupported target residue in: {mut}")
    if mut.target == mut.orig:
        raise InvalidMutation(f"equivalent mutation detected in: {mut}. Should be (None, \"WT\", None, None).")

    return True

def generate_mutation_from_traget_list(position: Tuple[str, int], orig_resi: str, target_list: str) -> Mutation:
    """generate a list of Mutation() objects from position and a list of target residues"""
    result = []
    for target in target_list:
        result.append(Mutation(
            orig=orig_resi,
            target=target,
            chain_id=position[0],
            res_idx=position[1]
            ))
    return result

# == TODO ==
def generate_all_mutations(
    structure: es.Structure, ) -> Dict[Tuple[str, int], List[Mutation]]:
    """Creates all possible mutations for a given Structure() object. Puts all the mutations into a dict()
    where the (key, value) pairs are ((chain_id, residue), List[Mutation]). The List[Mutation] is all mutations
    from the existing residue to the other 20 residues. For a given enzyme with N residues, there will be a total
    of N*20 Mutation() objects in the dict().


    Args:
        structure: The Structure() object to build mutations from.

    Returns:
        A dict() with (key, value) pairs of ((chain_id, residue), List[Mutation]).
    """
    result = dict()
    residues: List[es.Residue] = structure.residues
    residues = list(filter(lambda rr: rr.is_canonical(), residues))
    for res in residues:
        (chain_id, num) = res.key()
        orig: str = res.name
        if len(orig) != 1:
            orig = chem.convert_to_one_letter(orig)
        result[res.key()] = list(
            map(
                lambda ch: Mutation(orig=orig, target=ch, chain_id=chain_id, res_idx=num),
                chem.one_letters_except(orig),
            ))

    # a last check
    for mut_list in result.values():
        for mt in mut_list:
            assert is_valid_mutation(mt)
    return result


def size_increase(mut: Mutation) -> bool:
    """Checks if the mutation described in the supplied namedtuple describes an increase in
        size for the selected residue. DOES NOT check if the Mutation() is valid.

    Args:
        mut: The Mutation() namedtuple to be judged.

    Returns:
        If the described mutation leads to an increase in size.
    """

    return chem.RESIDUE_VOLUME_MAPPER[mut.target] > chem.RESIDUE_VOLUME_MAPPER[mut.orig]


def size_decrease(mut: Mutation) -> bool:
    """Checks if the mutation described in the supplied namedtuple describes an decrease in
        size for the selected residue. DOES NOT check if the Mutation() is valid.

    Args:
        mut: The Mutation() namedtuple to be judged.

    Returns:
        If the described mutation leads to a decrease in size.
    """

    return chem.RESIDUE_VOLUME_MAPPER[mut.target] < chem.RESIDUE_VOLUME_MAPPER[mut.orig]


def polarity_change(mut: Mutation) -> bool:
    """Checks if the mutation described in the supplied namedtuple describes a change in polarity.
    DOES NOT check if the Mutation() is valid.

    Args:
        mut: The Mutation() namedtuple to be judged.

    Returns:
        If the described mutation leads to a change in polarity.
    """
    return chem.residue.residue_polarity(mut.orig) != chem.residue.residue_polarity(
        mut.target)


def same_polarity(mut: Mutation) -> bool:
    """Checks if the mutation described in the supplied namedtuple does not describe a change in
    polarity. DOES NOT check if the Mutation() is valid.

    Args:
        mut: The Mutation() namedtuple to be judged.

    Returns:
        If the described mutation leads to no change in polarity.
    """
    return not polarity_change(mut)
