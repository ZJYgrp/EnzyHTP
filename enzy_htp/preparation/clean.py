"""Module for remove irrelevant structure parts (such as solvents).
Science API:
+ remove_solvent

Author: Qianzhen (QZ) Shao <shaoqz@icloud.com>
Date: 2022-09-22
"""
import copy
from enzy_htp.structure import Structure, Residue
import enzy_htp.structure.structure_operation as stru_oper


def remove_solvent(stru: Structure, protect: str = None, in_place: bool = True) -> Structure:
    """
    remove solvent from the structure. all Solvent() object will be removed
    TODO support customized solvent name maybe in another function assign_solvent
    TODO support protect some solvent from removal maybe with another function assign_ligand (#9)
    Args:
        stru: the target Structure
        protect: protect some solvent from removal and change its rtype to Ligand. Use selection grammer
    Returns:
        a reference of the changed {stru}
        (or a copy if in_place = False)
    """
    # planning for #9
    # assign_ligand(stru, protect):
    # protect_solvents = structure.select(stru, protect).residues
    # res: Residue
    # for res in protect_solvents:
    #     if not res.is_solvent():
    #         _LOGGER.warning(f'protecting non-solvent: {res}')
    #     solvent_to_ligand(res, inplace=True) # this inplace allow it to also change its identity in .parent.children
    if not in_place:
        stru = copy.deepcopy(stru)
    stru_oper.remove_solvent(stru)
    # clean up empty chains (suggest doing this every time when residues are removed)
    stru_oper.remove_empty_chain(stru)

    return stru


def remove_hydrogens(stru: Structure, polypeptide_only: bool=True, in_place: bool=True) -> Structure:
    """Method that removes hydrogens from the supplied structure.
    
    Args:
        stru: the Structure object that the hydrogens need to be removed from.
        polypeptide_only: whether only remove Hs from polypeptide
        in_place: apply the change in place or in a copy

    Returns:
        The Structure object with no hydrogens. (a copy if in_place=False)
    """
    if not in_place:
        stru = copy.deepcopy(stru)

    stru_oper.remove_hydrogens(stru, polypeptide_only)

    return stru
