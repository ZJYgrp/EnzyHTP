"""Define functions for mutate Structure(). 
Science API:
    +mutate_stru()
    +assign_mutation()

Mutation is carried out by an underlying engine and the supported engines currently include:
    + Amber/tleap

Author: Qianzhen (QZ) Shao <shaoqz@icloud.com>
Date: 2022-10-24
"""

import copy
from typing import Dict, List, Tuple
import numpy as np

from enzy_htp.core.logger import _LOGGER
from enzy_htp.structure import Structure
from .mutation import (
    Mutation,
    check_repeat_mutation,
    is_valid_mutation,
    remove_repeat_mutation)
from .mutation_pattern import decode_mutation_pattern


def assign_mutant(
    stru: Structure,
    pattern: str,
    chain_sync_list: List[tuple] = None,
    chain_index_mapper: Dict[str, int] = None,
    random_state: int = 100,
) -> List[List[Mutation]]:
    """
    This science API assigns mutants targeted in the study.
    decode the user assigned {pattern} based on the {stru} and get a list of mutants defined by
    a list of mutation objects each.

    Args:
        stru: the target structure
        pattern: the pattern that defines the mutation (see syntax below)
        chain_sync_list: a list like [(A,C),(B,D)] to indicate homo-chains in enzyme ploymer
            (like dimer). Mutations will be **copied** to the correponding homo-chains as it
            is maybe experimentally impossible to only do mutations on one chain of a homo-dimer
            enzyme.
        random_state: The int() seed for the random number generator. Default value is 100.
        (temp)
        chain_index_mapper: TODO(qz): add biopython pairwise2.align.globalxx
            A temp solution for cases that residue index in each chain is not aligned. (e.g.:
            for a pair of homo-dimer below:
            "A": ABCDEFG (start from 7)
            "B": BCDEFGH (start from 14)
            the chain_sync_mapper should be {"A":0, "B":6} and index conversion is done by
            A_res_idx - 0 + 6 = B_res_idx)
    Raises:
        enzy_htp.core.exception.InvalidMutationPatternSyntax
    Return:
        a list of mutants defined each by a list of mutation objects.

    *Pattern Syntax:*
        "mutant_1,mutant_2,mutant_3,..."
        The top layer of the mutation_pattern specify mutants with comma seperated patterns
        In the pattern of each mutant, there could be more than one sections, but if multiple
        sections are used, {} is needed to group those sections.
        "{section_a1,section_a2,section_a3},{section_b1,section_b2,section_b3},..."
        Each section can be one of the format below:
        1. direct indication                    : XA###Y
        2. random M, N-point mutation in a set  : r:N[mutation_esm_patterns]*M
                                                  or r:NR[mutation_esm_patterns]*MR
                                                  (N and M are int,
                                                  R stands for allowing repeating mutations in randomization)
        3. all mutation in a set: a             : a:[mutation_esm_patterns]
                                                  or a:M[mutation_esm_patterns]
                                                  (M stands for force mutate each position so that
                                                  no mutation on any position is not allowed)

        The mutation_esm_patterns is seperated by comma and each describes 2 things:
        1. position_pattern: a set of positions
                            (check selection syntax in .mutation_pattern.position_pattern)
                            NOTE: all non polypeptide part are filtered out.
        2. target_aa_pattern: a set of target mutations apply to all positions in the current set
                            (check syntax in .mutation_pattern.target_aa_pattern)
        The two pattern are seperated by ":" and a mutation_esm_patterns looks like:
        "position_pattern_0:target_aa_pattern_0, ..."

        *In 2&3 the pattern may indicate a mutant collection, if more than one mutant collection
        are indicated in the same {}, all combination of them is considered.

        Overall an example of pattern will be:
        "{RA154W, DA11G}, r:2[resi 289 around 4 and not resi 36:larger, proj(id 1000, id 2023, positive, 10):more_negative_charge]*100"
        * here proj() is a hypothetical selection function

    Details:
        Which mutations should we study is a non-trivial question. Mutations could be assigned
    from a database or a site-saturation requirement. It reflexs the scientific question defined
    Assigning the mutation requires converting chemical/structural language to strict mutation
    definitions. Some fast calculations can also be done during the selection of mutations. (e.g.:
    calculating residues aligned with the projection line of the reacting bond [ref])
        There are no existing software besides EnzyHTP addressing this challenge.
        A language that helps user to assign mutations is defined above.
    """
    # decode the pattern
    np.random.seed(random_state)  # this changes globaly
    mutants = decode_mutation_pattern(stru, pattern)
    # sync over polymers
    if chain_sync_list:
        mutants = sync_mutation_over_chains(mutants, chain_sync_list, chain_index_mapper)
    # san check of the mutation_flagss
    for mutant in mutants:
        for mutation in mutant:
            assert is_valid_mutation(mutation, stru)
    return mutants

def sync_mutation_over_chains(mutants: List[List[Mutation]],
                              chain_sync_list: List[Tuple[str]],
                              chain_index_mapper: Dict[str, int] = None) -> List[List[Mutation]]:
    """synchronize mutations of each mutant in {mutants} to correponding chains. Return a copy
    of mutants with addition mutations in each mutant.
    Args:
        mutants: 
            a list of target mutant
        chain_sync_list: 
            a list like [(A,C),(B,D)] to indicate homo-chains in enzyme ploymer
            (like dimer). Mutations will be **copied** to the correponding homo-chains as it
            is maybe experimentally impossible to only do mutations on one chain of a homo-dimer
            enzyme.
        chain_index_mapper: TODO(qz): add biopython pairwise2.align.globalxx
            A temp solution for cases that residue index in each chain is not aligned. (e.g.:
            for a pair of homo-dimer below:
            "A": ABCDEFG (start from 7)
            "B": BCDEFGH (start from 14)
            the chain_sync_mapper should be {"A":0, "B":6} and index conversion is done by
            A_res_idx - 0 + 6 = B_res_idx)

    Return:
        copy of the modified {mutants}

    Example:
        sync_mutation_over_chains([[mut_A1, mut_A2], [mut_B1]], chain_sync_list = ["A","B"])
        >>> [[mut_A1, mut_A2, mut_B1, mut_B2], [mut_B3, mut_A3]]
    """
    result = []
    if not chain_index_mapper:
        chain_index_mapper = {}
    mutants_copy = copy.deepcopy(mutants)
    for mutant in mutants_copy:
        new_mutant = []
        for mut in mutant:
            # 1. have the original mutation
            new_mutant.append(mut)
            # 2. check if the mutation needs sync
            orig_chain_id = mut.chain_id
            for chain_sync_group in chain_sync_list:
                if orig_chain_id in chain_sync_group:
                    sync_targets = filter(lambda x: x != orig_chain_id, chain_sync_group)
                    for sync_target in sync_targets:
                        new_res_idx = mut.res_idx - chain_index_mapper.get(orig_chain_id, 0) + chain_index_mapper.get(sync_target, 0)
                        new_mut = mut._replace(chain_id=sync_target, res_idx=new_res_idx)
                        # TODO(qz): this does not work in most of the cases.
                        # The index of the corresponding residue needs to be find by *pair-wise align* of the target and origin sequence and
                        # get the same aligned index.
                        new_mutant.append(new_mut)
                    break # one chain id can only be in one group
        result.append(list(set(new_mutant)))
    return result

def mutate_stru(
    stru: Structure,
    mutant: List[Mutation],
    engine: str = "tleap_min",
    in_place: bool = False,
    **kwargs
) -> Structure:
    """
    This science API solves the problem of protein structural prediction upon mutation.
    It means to determine which mutation to address and determine the structure of the
    mutant of the source protein caused by residue substitution, deletion, and insertion.
    (see also: structure_prediction module for an alternative solution)
    Args:
        stru: the target structure
        mutation_list: a target list of mutation objects. (normally generated by the assign_mutant
            function. Generally dont recommand generating them manually)
        engine: the engine (method) used for determine the mutated structure
            (current available keywords):
            tleap_min
            # TODO may need to add more arg when deletion and insertion are supported
            # (e.g.: engine_del, engine_ins)
        in_place: if change the structure in-place and return the reference
                  False means return a changed structure_obj and keep the original object
                  intact
                  (default is False since wild-type structure is expected to also available
                  in many applications)
    Raises:
        enzy_htp.core.exception.UnsupportedMethod if the supplied engine is not supported.
    Returns:
        the reference/copy of the changed structure (depends on the in_place value)

    Details:
        Unlike predicting the whole protein structure from sequence and smiles, mutating a
    structure from a reference structure involves only changes on a limit number of residues
    and perturbation of the rest of the structure (especially ligand binding, protonation state etc.)
    As a result, it can be solved using more efficient methods and predicting the whole structure
    from sketch. Note that the accuracy of the resulting structure varies base on the need. If followed
    by MD, the structure only needs to be good starting point of MD.
        There are 3 types of mutations in protein sequence: substitution, deletion, and insertion.
        Substitution is the most common type of the mutation. In this case, only the side-chain is
    replaced by another type of the side-chain. And determining the conformation of the new side-chain
    is the main challenge. It also relates to side-chain conformation prediction in the field of
    structural prediction.
        Deletion and insertion involve backbone changes.

    Avaible strageties:
    Substitution:
        Direct replacement of the side-chain:
        - tleap_min (https://pubs.acs.org/doi/full/10.1021/acs.jcim.1c01424)
            The most simple way to get a mutant structure. It 1. place the new side-chain using a
            constant conformation (relative to backbone) and 2. relax the crude mutant structure using
            MM minimization.

            Consider limited change of other side chains in MM minimization
            Not consider backbone change

            * This method particularly has problem when mutating a small residue to a larger one. In this
            case, collision may appears in the mutated structure and the MM minimization is responsible
            for resolving it. But in extreme cases, there are unresolvable collision such as the carbon
            chain is trapped in a phenyl ring. And currently we don't have a method to detect such trapping.
            The method is only used as a place holder for 1st version EnzyHTP. We have encounter any problem
            brought by the accuracy of the mutation when using this method in workflows but users should be
            cautious with it and consider it a potential source of absured results.
        
        Side-chain rotamer library:
        (most used in the field)
        - SCWRL4 (http://dunbrack.fccc.edu/lab/scwrl)
            Not consider other side-chain change
            Not consider backbone change
        - PyMol (https://github.com/schrodinger/pymol-open-source)
            Not consider other side-chain change
            Not consider backbone change
        - Phyre2
            Consider other side-chain change
            Not consider backbone change
            * seems having a derived pipeline Missense3D addressing the challenge (https://www.sciencedirect.com/science/article/pii/S0022283619302037?via%3Dihub#s0050)
            * related discussion in its website (http://www.sbg.bio.ic.ac.uk/phyre2/html/help.cgi?id=help/faq)

        Machine learning methods:
        - Packpred (http://cospi.iiserpune.ac.in/packpred/, https://www.frontiersin.org/articles/10.3389/fmolb.2021.646288/full, https://github.com/kuanpern/PackPred)
          * find a summary of the missence mutation in the intro of the paper
            Unknown

        MCMC search globally in side-chains:
        - Modeller
            Fully consider other side-chain change
            Not consider backbone change
        - SWISSMODEL
            Fully consider other side-chain change
            Not consider backbone change

    Insertion/Deletion:
        - Phyre4
            see http://www.sbg.bio.ic.ac.uk/phyre2/html/help.cgi?id=help/faq
            works mainly <5 AA change
    """
    # deal with repeating mutation
    if check_repeat_mutation(mutant):
        _LOGGER.warning(
            f"Detected repeating mutation in mutant: {mutant}. Only use the last one.")
        mutant = remove_repeat_mutation(mutant, keep="last")
    # apply the mutation
    mutator = MUTATE_STRU_ENGINE[engine]
    return mutator(stru, mutant, in_place, **kwargs)

def mutate_stru_with_tleap(
        stru: Structure,
        mutant: List[Mutation],
        in_place: bool,
        # tleap_specifics_below
        ) -> Structure:
    """mutate the {stru} to its {mutant} structure using tleap
    from AmberMD package."""

    # # Prepare a label for the filename
    # tot_Flag_name=''
    # for Flag in self.MutaFlags:
    #     Flag_name=self._build_MutaName(Flag)
    #     tot_Flag_name=tot_Flag_name+'_'+Flag_name

    # # Operate the PDB
    # out_PDB_path1=self.cache_path+'/'+self.name+tot_Flag_name+'_tmp.pdb'
    # out_PDB_path2=self.path_name+tot_Flag_name+'.pdb'

    # self._get_file_path()
    # with open(self.path,'r') as f:
    #     with open(out_PDB_path1,'w') as of:
    #         chain_count = 1
    #         for line in f:
    #             pdb_l = PDB_line(line)
                                    
    #             TER_flag = 0
    #             if pdb_l.line_type == 'TER':
    #                 TER_flag = 1
    #             # add chain count in next loop for next line
    #             if TER_flag:
    #                 chain_count += 1
    #             match=0
    #             # only match in the dataline and keep all non data lines
    #             if pdb_l.line_type == 'ATOM':
    #                 for Flag in self.MutaFlags:
    #                     if 'WT' in Flag:
    #                         continue
    #                     # Test for every Flag for every lines
    #                     t_chain_id=Flag[1]
    #                     t_resi_id =Flag[2]

    #                     if chr(64+chain_count) == t_chain_id:
    #                         if pdb_l.resi_id == int(t_resi_id):
                                
    #                             # do not write old line if match a MutaFlag
    #                             match=1
    #                             # Keep OldAtoms of targeted old residue
    #                             resi_2 = Flag[3]
    #                             OldAtoms=['N','H','CA','HA','CB','C','O']
    #                             #fix for mutations of Gly & Pro
    #                             if resi_2 == 'G':
    #                                 OldAtoms=['N','H','CA','C','O']
    #                             if resi_2 == 'P':
    #                                 OldAtoms=['N','CA','HA','CB','C','O']

    #                             for i in OldAtoms:
    #                                 if i == pdb_l.atom_name:
    #                                     new_line=line[:17]+Resi_map[resi_2]+line[20:]                                        
    #                                     of.write(new_line)
    #                                     break                                
    #                             #Dont run for other Flags after first Flag matches.
    #                             break

    #             if not match:               
    #                 of.write(line)


    # # Run tLeap 
    # #make input
    # leapin_path = self.cache_path+'/leap_P2PwL.in'
    # leap_input=open(leapin_path,'w')
    # leap_input.write('source leaprc.protein.ff14SB\n')
    # leap_input.write('a = loadpdb '+out_PDB_path1+'\n')
    # leap_input.write('savepdb a '+out_PDB_path2+'\n')
    # leap_input.write('quit\n')
    # leap_input.close()
    # #run
    # os.system('tleap -s -f '+leapin_path+' > '+self.cache_path+'/leap_P2PwL.out')
    # if Config.debug <= 1:
    #     os.system('rm leap.log')

    # #Update the file
    # self.path = out_PDB_path2
    # self._update_name()


MUTATE_STRU_ENGINE = {
    "tleap" : mutate_stru_with_tleap
}