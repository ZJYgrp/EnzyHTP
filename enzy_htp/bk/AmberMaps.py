#__doc__ = """
#This module include mapping required by the workflow.
#------------------------------------------------------------
#(MAP) Resi_map
#Map residue key with the 3 letter name.
#{resi_key:resi_name_3,...}
#------------------------------------------------------------
#(MAP) Resi_map2
#Map 3 letter name with residue key.
#{resi_name_3:resi_key,...}
#------------------------------------------------------------
#(List) Resi_list
#Map residue key with index number
#[resi_key,...]
#------------------------------------------------------------
#(???) Atom_topology
#
#
#------------------------------------------------------------
#"""
#
#
#TIP3P_map = [
#    "O",
#    "H",
#    "OW",
#    "HW",
#    "HOH",
#    "WAT",
#    "F",
#    "Cl",
#    "CL",
#    "Br",
#    "BR",
#    "I",
#    "Li",
#    "LI",
#    "Na",
#    "NA",
#    "K",
#    "Rb",
#    "RB",
#    "Cs",
#    "CS",
#    "Mg",
#    "MG",
#    "Tl",
#    "TL",
#    "Cu",
#    "CU",
#    "Ag",
#    "AG",
#    "Be",
#    "BE",
#    "Ni",
#    "NI",
#    "Pt",
#    "PT",
#    "Zn",
#    "ZN",
#    "Co",
#    "CO",
#    "Pd",
#    "PD",
#    "Cr",
#    "CR",
#    "Fe",
#    "FE",
#    "V",
#    "Mn",
#    "MN",
#    "Hg",
#    "HG",
#    "Cd",
#    "CD",
#    "Yb",
#    "YB",
#    "Ca",
#    "CA",
#    "Sn",
#    "SN",
#    "Pb",
#    "PB",
#    "Eu",
#    "EU",
#    "Sr",
#    "SR",
#    "Sm",
#    "SM",
#    "Ba",
#    "BA",
#    "Ra",
#    "RA",
#    "Al",
#    "AL",
#    "In",
#    "IN",
#    "Y",
#    "La",
#    "LA",
#    "Ce",
#    "CE",
#    "Pr",
#    "PR",
#    "Nd",
#    "ND",
#    "Gd",
#    "GD",
#    "Tb",
#    "TB",
#    "Dy",
#    "DY",
#    "Er",
#    "ER",
#    "Tm",
#    "TM",
#    "Lu",
#    "LU",
#    "Hf",
#    "HF",
#    "Zr",
#    "ZR",
#    "U",
#    "Pu",
#    "PU",
#    "Th",
#    "TH",
#]
#
## a map all metal (resi_name:atom_name)
#Metal_map = {
#    "LI": "Li",
#    "NA": "Na",
#    "Na+": "Na",
#    "K": "K",
#    "K+": "K",
#    "RB": "Rb",
#    "CS": "Cs",
#    "MG": "Mg",
#    "TL": "Tl",
#    "CU": "Cu",
#    "AG": "Ag",
#    "BE": "Be",
#    "NI": "Ni",
#    "PT": "Pt",
#    "ZN": "Zn",
#    "CO": "Co",
#    "PD": "Pd",
#    "CR": "Cr",
#    "FE": "Fe",
#    "V": "V",
#    "MN": "Mn",
#    "HG": "Hg",
#    "CD": "Cd",
#    "YB": "Yb",
#    "CA": "Ca",
#    "SN": "Sn",
#    "PB": "Pb",
#    "EU": "Eu",
#    "SR": "Sr",
#    "SM": "Sm",
#    "BA": "Ba",
#    "RA": "Ra",
#    "AL": "Al",
#    "IN": "In",
#    "Y": "Y",
#    "LA": "La",
#    "CE": "Ce",
#    "PR": "Pr",
#    "ND": "Nd",
#    "GD": "Gd",
#    "TB": "Tb",
#    "DY": "Dy",
#    "ER": "Er",
#    "TM": "Tm",
#    "LU": "Lu",
#    "HF": "Hf",
#    "ZR": "Zr",
#    "U": "U",
#    "PU": "Pu",
#    "TH": "Th",
#}
#
## Potential coordination center: add upon discover. (resi_name:atom_name)
#MetalCenter_map = {}
#
## A map for element conversio, independent of the grammer.
## Amber: base on a Amber18 LEaP ff14SB output
#Resi_Ele_map = {
#    "Amber": {
#        "C": "C",
#        "CA": "C",
#        "CB": "C",
#        "CD": "C",
#        "CD1": "C",
#        "CD2": "C",
#        "CE": "C",
#        "CE1": "C",
#        "CE2": "C",
#        "CE3": "C",
#        "CG": "C",
#        "CG1": "C",
#        "CG2": "C",
#        "CH2": "C",
#        "CZ": "C",
#        "CZ2": "C",
#        "CZ3": "C",
#        "H": "H",
#        "H1": "H",
#        "H2": "H",
#        "H3": "H",
#        "HA": "H",
#        "HA2": "H",
#        "HA3": "H",
#        "HB": "H",
#        "HB1": "H",
#        "HB2": "H",
#        "HB3": "H",
#        "HD1": "H",
#        "HD11": "H",
#        "HD12": "H",
#        "HD13": "H",
#        "HD2": "H",
#        "HD21": "H",
#        "HD22": "H",
#        "HD23": "H",
#        "HD3": "H",
#        "HE": "H",
#        "HE1": "H",
#        "HE2": "H",
#        "HE21": "H",
#        "HE22": "H",
#        "HE3": "H",
#        "HG": "H",
#        "HG1": "H",
#        "HG11": "H",
#        "HG12": "H",
#        "HG13": "H",
#        "HG2": "H",
#        "HG21": "H",
#        "HG22": "H",
#        "HG23": "H",
#        "HG3": "H",
#        "HH": "H",
#        "HH11": "H",
#        "HH12": "H",
#        "HH2": "H",
#        "HH21": "H",
#        "HH22": "H",
#        "HZ": "H",
#        "HZ1": "H",
#        "HZ2": "H",
#        "HZ3": "H",
#        "N": "N",
#        "ND1": "N",
#        "ND2": "N",
#        "NE": "N",
#        "NE1": "N",
#        "NE2": "N",
#        "NH1": "N",
#        "NH2": "N",
#        "NZ": "N",
#        "O": "O",
#        "OD1": "O",
#        "OD2": "O",
#        "OE1": "O",
#        "OE2": "O",
#        "OG": "O",
#        "OG1": "O",
#        "OH": "O",
#        "OXT": "O",
#        "SD": "S",
#        "SG": "S",
#        "LI": "Li",
#        "NA": "Na",
#        "K": "K",
#        "RB": "Rb",
#        "CS": "Cs",
#        "MG": "Mg",
#        "TL": "Tl",
#        "CU": "Cu",
#        "AG": "Ag",
#        "BE": "Be",
#        "NI": "Ni",
#        "PT": "Pt",
#        "ZN": "Zn",
#        "CO": "Co",
#        "PD": "Pd",
#        "CR": "Cr",
#        "FE": "Fe",
#        "V": "V",
#        "MN": "Mn",
#        "YB": "Yb",
#        "SN": "Sn",
#        "PB": "Pb",
#        "EU": "Eu",
#        "SR": "Sr",
#        "SM": "Sm",
#        "BA": "Ba",
#        "RA": "Ra",
#        "AL": "Al",
#        "IN": "In",
#        "Y": "Y",
#        "LA": "La",
#        "PR": "Pr",
#        "ND": "Nd",
#        "GD": "Gd",
#        "TB": "Tb",
#        "DY": "Dy",
#        "ER": "Er",
#        "TM": "Tm",
#        "LU": "Lu",
#        "HF": "Hf",
#        "ZR": "Zr",
#        "U": "U",
#        "PU": "Pu",
#        "TH": "Th",
#    }
#}
#
## relative mass of elements. Append as need.
#Ele_mass_map = {
#    "H": 1.008,
#    "He": 4.003,
#    "Li": 6.941,
#    "Be": 9.012,
#    "B": 10.811,
#    "C": 12.011,
#    "N": 14.007,
#    "O": 15.999,
#    "F": 18.998,
#    "Ne": 20.17,
#    "Na": 22.99,
#    "Mg": 24.305,
#    "Al": 26.982,
#    "Si": 28.085,
#    "P": 30.974,
#    "S": 32.06,
#    "Cl": 35.453,
#    "Ar": 39.94,
#    "K": 39.098,
#    "Ca": 40.08,
#}
#
## Potential coordination donor: add upon discover. (atom name - base on the atom type definition in the force field)
## ========= Side chain Heteroatoms (O,N,S) ==============
## Amber: base on a Amber18 LEaP ff14SB output
#
#Donor_atom_list = {
#    "Amber": [
#        "NH2",
#        "NE",
#        "NH1",
#        "ND1",
#        "NE2",
#        "NZ",
#        "OD1",
#        "OD2",
#        "OE1",
#        "OE2",
#        "OG",
#        "OG1",
#        "ND2",
#        "OD1",
#        "OE1",
#        "NE2",
#        "SG",
#        "SD",
#        "OH",
#        "NE1",
#    ]
#}
#
## A list for residues with ambiguous protonation state that have potential deprotonation
#AmbProton_list = [
#    "ASH",
#    "ASP",
#    "CYS",
#    "CYM",
#    "GLH",
#    "GLU",
#    "HIP",
#    "HIE",
#    "HID",
#    "LYS",
#    "LYN",
#    "TYR",
#    "TYM",
#    "ARG",
#    "AR0",
#]
#
## a map of residue name of deprotonation {resi_name : (depro_resi_name, depro_proton_name), ...}
## atom name base on a Amber18 LEaP ff14SB output
#DeProton_map = {
#    "ASH": ("ASP", "HD2"),
#    "CYS": ("CYM", "HG"),
#    "GLH": ("GLU", "HE2"),
#    "HIP": (("HIE", "HD1"), ("HID", "HE2")),
#    "HID": None,  # depending on the T_atom, no default method
#    "HIE": None,
#    "LYS": ("LYN", "HZ1"),
#    "TYR": ("TYM", "HH"),
#    "ARG": ("AR0", "HH22"),
#}
#
#NoProton_list = ["ASP", "GLU", "MET"]
#
## Radius and distance
## ===============================================
## reference:  (element : radius)
#Ionic_radius_map =
## reference:  doi:10.1021/jp8111556 (element : radius)
#VDW_radius_map =
## mimic the way GaussView/PyMol add H using PDB atom names (append in the future as needed)
## ===============================================
#
## from amino12.lib about residue and connectivity
## ===============================================
#
#resi_atom_list = {
#    "ALA": ["N", "H", "CA", "HA", "CB", "HB1", "HB2", "HB3", "C", "O"],
#    "ARG": [
#        "N",
#        "H",
#        "CA",
#        "HA",
#        "CB",
#        "HB2",
#        "HB3",
#        "CG",
#        "HG2",
#        "HG3",
#        "CD",
#        "HD2",
#        "HD3",
#        "NE",
#        "HE",
#        "CZ",
#        "NH1",
#        "HH11",
#        "HH12",
#        "NH2",
#        "HH21",
#        "HH22",
#        "C",
#        "O",
#    ],
#    "ASH": [
#        "N",
#        "H",
#        "CA",
#        "HA",
#        "CB",
#        "HB2",
#        "HB3",
#        "CG",
#        "OD1",
#        "OD2",
#        "HD2",
#        "C",
#        "O",
#    ],
#    "ASN": [
#        "N",
#        "H",
#        "CA",
#        "HA",
#        "CB",
#        "HB2",
#        "HB3",
#        "CG",
#        "OD1",
#        "ND2",
#        "HD21",
#        "HD22",
#        "C",
#        "O",
#    ],
#    "ASP": ["N", "H", "CA", "HA", "CB", "HB2", "HB3", "CG", "OD1", "OD2", "C", "O"],
#    "CYM": ["N", "H", "CA", "HA", "CB", "HB3", "HB2", "SG", "C", "O"],
#    "CYS": ["N", "H", "CA", "HA", "CB", "HB2", "HB3", "SG", "HG", "C", "O"],
#    "CYX": ["N", "H", "CA", "HA", "CB", "HB2", "HB3", "SG", "C", "O"],
#    "GLH": [
#        "N",
#        "H",
#        "CA",
#        "HA",
#        "CB",
#        "HB2",
#        "HB3",
#        "CG",
#        "HG2",
#        "HG3",
#        "CD",
#        "OE1",
#        "OE2",
#        "HE2",
#        "C",
#        "O",
#    ],
#    "GLN": [
#        "N",
#        "H",
#        "CA",
#        "HA",
#        "CB",
#        "HB2",
#        "HB3",
#        "CG",
#        "HG2",
#        "HG3",
#        "CD",
#        "OE1",
#        "NE2",
#        "HE21",
#        "HE22",
#        "C",
#        "O",
#    ],
#    "GLU": [
#        "N",
#        "H",
#        "CA",
#        "HA",
#        "CB",
#        "HB2",
#        "HB3",
#        "CG",
#        "HG2",
#        "HG3",
#        "CD",
#        "OE1",
#        "OE2",
#        "C",
#        "O",
#    ],
#    "GLY": ["N", "H", "CA", "HA2", "HA3", "C", "O"],
#    "HID": [
#        "N",
#        "H",
#        "CA",
#        "HA",
#        "CB",
#        "HB2",
#        "HB3",
#        "CG",
#        "ND1",
#        "HD1",
#        "CE1",
#        "HE1",
#        "NE2",
#        "CD2",
#        "HD2",
#        "C",
#        "O",
#    ],
#    "HIE": [
#        "N",
#        "H",
#        "CA",
#        "HA",
#        "CB",
#        "HB2",
#        "HB3",
#        "CG",
#        "ND1",
#        "CE1",
#        "HE1",
#        "NE2",
#        "HE2",
#        "CD2",
#        "HD2",
#        "C",
#        "O",
#    ],
#    "HIP": [
#        "N",
#        "H",
#        "CA",
#        "HA",
#        "CB",
#        "HB2",
#        "HB3",
#        "CG",
#        "ND1",
#        "HD1",
#        "CE1",
#        "HE1",
#        "NE2",
#        "HE2",
#        "CD2",
#        "HD2",
#        "C",
#        "O",
#    ],
#    "HYP": [
#        "N",
#        "CD",
#        "HD22",
#        "HD23",
#        "CG",
#        "HG",
#        "OD1",
#        "HD1",
#        "CB",
#        "HB2",
#        "HB3",
#        "CA",
#        "HA",
#        "C",
#        "O",
#    ],
#    "ILE": [
#        "N",
#        "H",
#        "CA",
#        "HA",
#        "CB",
#        "HB",
#        "CG2",
#        "HG21",
#        "HG22",
#        "HG23",
#        "CG1",
#        "HG12",
#        "HG13",
#        "CD1",
#        "HD11",
#        "HD12",
#        "HD13",
#        "C",
#        "O",
#    ],
#    "LEU": [
#        "N",
#        "H",
#        "CA",
#        "HA",
#        "CB",
#        "HB2",
#        "HB3",
#        "CG",
#        "HG",
#        "CD1",
#        "HD11",
#        "HD12",
#        "HD13",
#        "CD2",
#        "HD21",
#        "HD22",
#        "HD23",
#        "C",
#        "O",
#    ],
#    "LYN": [
#        "N",
#        "H",
#        "CA",
#        "HA",
#        "CB",
#        "HB2",
#        "HB3",
#        "CG",
#        "HG2",
#        "HG3",
#        "CD",
#        "HD2",
#        "HD3",
#        "CE",
#        "HE2",
#        "HE3",
#        "NZ",
#        "HZ2",
#        "HZ3",
#        "C",
#        "O",
#    ],
#    "LYS": [
#        "N",
#        "H",
#        "CA",
#        "HA",
#        "CB",
#        "HB2",
#        "HB3",
#        "CG",
#        "HG2",
#        "HG3",
#        "CD",
#        "HD2",
#        "HD3",
#        "CE",
#        "HE2",
#        "HE3",
#        "NZ",
#        "HZ1",
#        "HZ2",
#        "HZ3",
#        "C",
#        "O",
#    ],
#    "MET": [
#        "N",
#        "H",
#        "CA",
#        "HA",
#        "CB",
#        "HB2",
#        "HB3",
#        "CG",
#        "HG2",
#        "HG3",
#        "SD",
#        "CE",
#        "HE1",
#        "HE2",
#        "HE3",
#        "C",
#        "O",
#    ],
#    "PHE": [
#        "N",
#        "H",
#        "CA",
#        "HA",
#        "CB",
#        "HB2",
#        "HB3",
#        "CG",
#        "CD1",
#        "HD1",
#        "CE1",
#        "HE1",
#        "CZ",
#        "HZ",
#        "CE2",
#        "HE2",
#        "CD2",
#        "HD2",
#        "C",
#        "O",
#    ],
#    "PRO": [
#        "N",
#        "CD",
#        "HD2",
#        "HD3",
#        "CG",
#        "HG2",
#        "HG3",
#        "CB",
#        "HB2",
#        "HB3",
#        "CA",
#        "HA",
#        "C",
#        "O",
#    ],
#    "SER": ["N", "H", "CA", "HA", "CB", "HB2", "HB3", "OG", "HG", "C", "O"],
#    "THR": [
#        "N",
#        "H",
#        "CA",
#        "HA",
#        "CB",
#        "HB",
#        "CG2",
#        "HG21",
#        "HG22",
#        "HG23",
#        "OG1",
#        "HG1",
#        "C",
#        "O",
#    ],
#    "TRP": [
#        "N",
#        "H",
#        "CA",
#        "HA",
#        "CB",
#        "HB2",
#        "HB3",
#        "CG",
#        "CD1",
#        "HD1",
#        "NE1",
#        "HE1",
#        "CE2",
#        "CZ2",
#        "HZ2",
#        "CH2",
#        "HH2",
#        "CZ3",
#        "HZ3",
#        "CE3",
#        "HE3",
#        "CD2",
#        "C",
#        "O",
#    ],
#    "TYR": [
#        "N",
#        "H",
#        "CA",
#        "HA",
#        "CB",
#        "HB2",
#        "HB3",
#        "CG",
#        "CD1",
#        "HD1",
#        "CE1",
#        "HE1",
#        "CZ",
#        "OH",
#        "HH",
#        "CE2",
#        "HE2",
#        "CD2",
#        "HD2",
#        "C",
#        "O",
#    ],
#    "VAL": [
#        "N",
#        "H",
#        "CA",
#        "HA",
#        "CB",
#        "HB",
#        "CG1",
#        "HG11",
#        "HG12",
#        "HG13",
#        "CG2",
#        "HG21",
#        "HG22",
#        "HG23",
#        "C",
#        "O",
#    ],
#}
#
## C terminal
##resi_ct_cnt_map # N terminal
##resi_nt_cnt_map =# ===============================================
#
## ONIOM label G16 (Need to provide missing parms for non-pre-existed metal)
#G16_label_map = {
#    "ILE": {
#        "C": "C",
#        "CG2": "CT",
#        "HG22": "HC",
#        "H": "H",
#        "CA": "CT",
#        "O": "O",
#        "N": "N",
#        "CG1": "CT",
#        "HG21": "HC",
#        "HG12": "HC",
#        "HG13": "HC",
#        "HD13": "HC",
#        "CD1": "CT",
#        "CB": "CT",
#        "HB": "HC",
#        "HD12": "HC",
#        "HG23": "HC",
#        "HA": "H1",
#        "HD11": "HC",
#    },
#    "GLN": {
#        "HG2": "HC",
#        "C": "C",
#        "H": "H",
#        "CA": "CT",
#        "CG": "CT",
#        "HG3": "HC",
#        "O": "O",
#        "N": "N",
#        "CD": "C",
#        "CB": "CT",
#        "HE22": "H",
#        "HE21": "H",
#        "HA": "H1",
#        "NE2": "N",
#        "OE1": "O",
#        "HB3": "HC",
#        "HB2": "HC",
#    },
#    "GLU": {
#        "HG2": "HC",
#        "C": "C",
#        "H": "H",
#        "CA": "CT",
#        "CG": "CT",
#        "HG3": "HC",
#        "O": "O",
#        "N": "N",
#        "CD": "C",
#        "CB": "CT",
#        "HA": "H1",
#        "OE2": "O2",
#        "OE1": "O2",
#        "HB3": "HC",
#        "HB2": "HC",
#    },
#    "GLY": {
#        "N": "N",
#        "H": "H",
#        "CA": "CT",
#        "HA2": "HC",
#        "HA3": "HC",
#        "C": "C",
#        "O": "O",
#    },
#    "CYS": {
#        "C": "C",
#        "H": "H",
#        "CA": "CT",
#        "O": "O",
#        "N": "N",
#        "CB": "CT",
#        "HA": "H1",
#        "SG": "SH",
#        "HG": "HS",
#        "HB3": "H1",
#        "HB2": "H1",
#    },
#    "ASP": {
#        "C": "C",
#        "H": "H",
#        "CA": "CT",
#        "CG": "C",
#        "OD1": "O2",
#        "N": "N",
#        "O": "O",
#        "CB": "CT",
#        "HA": "H1",
#        "OD2": "O2",
#        "HB3": "HC",
#        "HB2": "HC",
#    },
#    "SER": {
#        "C": "C",
#        "OG": "OH",
#        "H": "H",
#        "CA": "CT",
#        "O": "O",
#        "N": "N",
#        "CB": "CT",
#        "HA": "H1",
#        "HG": "HO",
#        "HB3": "H1",
#        "HB2": "H1",
#    },
#    "LYS": {
#        "HA": "H1",
#        "HE2": "HP",
#        "HE3": "HP",
#        "HG2": "HC",
#        "HG3": "HC",
#        "NZ": "N3",
#        "HZ1": "H",
#        "HZ3": "H",
#        "CB": "CT",
#        "C": "C",
#        "H": "H",
#        "CA": "CT",
#        "HZ2": "H",
#        "CG": "CT",
#        "CE": "CT",
#        "N": "N",
#        "O": "O",
#        "CD": "CT",
#        "HD3": "HC",
#        "HD2": "HC",
#        "HB3": "HC",
#        "HB2": "HC",
#    },
#    "PRO": {
#        "C": "C",
#        "HA": "H1",
#        "HD3": "H1",
#        "HD2": "H1",
#        "HG2": "HC",
#        "CA": "CT",
#        "CG": "CT",
#        "HG3": "HC",
#        "O": "O",
#        "CD": "CT",
#        "CB": "CT",
#        "N": "N",
#        "HB3": "HC",
#        "HB2": "HC",
#    },
#    "HID": {
#        "CD2": "CV",
#        "HE1": "H5",
#        "HD1": "H",
#        "H": "H",
#        "CA": "CT",
#        "CG": "CC",
#        "C": "C",
#        "O": "O",
#        "N": "N",
#        "HD2": "H4",
#        "CE1": "CR",
#        "CB": "CT",
#        "ND1": "NA",
#        "HA": "H1",
#        "NE2": "NB",
#        "HB3": "HC",
#        "HB2": "HC",
#    },
#    "HIE": {
#        "CD2": "CW",
#        "HE1": "H5",
#        "HE2": "H",
#        "H": "H",
#        "CA": "CT",
#        "CG": "CC",
#        "C": "C",
#        "O": "O",
#        "N": "N",
#        "HD2": "H4",
#        "CE1": "CR",
#        "CB": "CT",
#        "ND1": "NB",
#        "HA": "H1",
#        "NE2": "NA",
#        "HB3": "HC",
#        "HB2": "HC",
#    },
#    "ASN": {
#        "C": "C",
#        "ND2": "N",
#        "HD22": "H",
#        "HD21": "H",
#        "H": "H",
#        "CA": "CT",
#        "CG": "C",
#        "OD1": "O",
#        "N": "N",
#        "O": "O",
#        "CB": "CT",
#        "HA": "H1",
#        "HB3": "HC",
#        "HB2": "HC",
#    },
#    "HIP": {
#        "CD2": "CW",
#        "HE2": "H",
#        "HE1": "H5",
#        "HD1": "H",
#        "H": "H",
#        "CA": "CT",
#        "CG": "CC",
#        "C": "C",
#        "O": "O",
#        "N": "N",
#        "HD2": "H4",
#        "CE1": "CR",
#        "CB": "CT",
#        "ND1": "NA",
#        "HA": "H1",
#        "NE2": "NA",
#        "HB3": "HC",
#        "HB2": "HC",
#    },
#    "VAL": {
#        "C": "C",
#        "CG2": "CT",
#        "HG11": "HC",
#        "H": "H",
#        "CA": "CT",
#        "HG21": "HC",
#        "O": "O",
#        "N": "N",
#        "CG1": "CT",
#        "HG12": "HC",
#        "HG13": "HC",
#        "CB": "CT",
#        "HB": "HC",
#        "HG23": "HC",
#        "HA": "H1",
#        "HG22": "HC",
#    },
#    "THR": {
#        "C": "C",
#        "CG2": "CT",
#        "HG22": "HC",
#        "H": "H",
#        "CA": "CT",
#        "OG1": "OH",
#        "O": "O",
#        "N": "N",
#        "HG21": "HC",
#        "HG1": "HO",
#        "CB": "CT",
#        "HB": "H1",
#        "HG23": "HC",
#        "HA": "H1",
#    },
#    "TRP": {
#        "HH2": "HA",
#        "CZ2": "CA",
#        "CZ3": "CA",
#        "CD1": "CW",
#        "CD2": "CB",
#        "HA": "H1",
#        "HE1": "H",
#        "HE3": "HA",
#        "CH2": "CA",
#        "HZ3": "HA",
#        "HZ2": "HA",
#        "CB": "CT",
#        "C": "C",
#        "H": "H",
#        "CA": "CT",
#        "CG": "C*",
#        "O": "O",
#        "N": "N",
#        "CE3": "CA",
#        "CE2": "CN",
#        "HD1": "H4",
#        "HB2": "HC",
#        "HB3": "HC",
#        "NE1": "NA",
#    },
#    "WAT": {"H2": "HW", "H1": "HW", "O": "OW"},
#    "PHE": {
#        "HZ": "HA",
#        "CD2": "CA",
#        "HE2": "HA",
#        "HE1": "HA",
#        "HD1": "HA",
#        "H": "H",
#        "CA": "CT",
#        "CG": "CA",
#        "C": "C",
#        "O": "O",
#        "N": "N",
#        "CZ": "CA",
#        "CE2": "CA",
#        "HD2": "HA",
#        "CD1": "CA",
#        "CE1": "CA",
#        "CB": "CT",
#        "HA": "H1",
#        "HB3": "HC",
#        "HB2": "HC",
#    },
#    "ALA": {
#        "C": "C",
#        "H": "H",
#        "CA": "CT",
#        "O": "O",
#        "N": "N",
#        "CB": "CT",
#        "HA": "H1",
#        "HB1": "HC",
#        "HB3": "HC",
#        "HB2": "HC",
#    },
#    "MET": {
#        "HG2": "H1",
#        "C": "C",
#        "HE1": "H1",
#        "HE2": "H1",
#        "HE3": "H1",
#        "H": "H",
#        "CA": "CT",
#        "CG": "CT",
#        "HG3": "H1",
#        "CE": "CT",
#        "N": "N",
#        "SD": "S",
#        "O": "O",
#        "CB": "CT",
#        "HA": "H1",
#        "HB3": "HC",
#        "HB2": "HC",
#    },
#    "LEU": {
#        "C": "C",
#        "HD22": "HC",
#        "HD23": "HC",
#        "HD21": "HC",
#        "H": "H",
#        "CA": "CT",
#        "CG": "CT",
#        "O": "O",
#        "N": "N",
#        "CD1": "CT",
#        "CD2": "CT",
#        "CB": "CT",
#        "HD13": "HC",
#        "HD12": "HC",
#        "HD11": "HC",
#        "HA": "H1",
#        "HG": "HC",
#        "HB3": "HC",
#        "HB2": "HC",
#    },
#    "ARG": {
#        "NE": "N2",
#        "HA": "H1",
#        "HE": "H",
#        "HG2": "HC",
#        "HG3": "HC",
#        "HH22": "H",
#        "HH21": "H",
#        "CB": "CT",
#        "C": "C",
#        "H": "H",
#        "CA": "CX",
#        "CG": "CT",
#        "O": "O",
#        "N": "N3",
#        "CZ": "CA",
#        "NH1": "N2",
#        "NH2": "N2",
#        "CD": "CT",
#        "HD3": "H1",
#        "HD2": "H1",
#        "HH12": "H",
#        "HH11": "H",
#        "HB3": "HC",
#        "HB2": "HC",
#    },
#    "TYR": {
#        "CD2": "CA",
#        "HE2": "HA",
#        "HE1": "HA",
#        "HD1": "HA",
#        "OH": "OH",
#        "H": "H",
#        "CA": "CT",
#        "CG": "CA",
#        "C": "C",
#        "O": "O",
#        "N": "N",
#        "CZ": "C",
#        "HH": "HO",
#        "HD2": "HA",
#        "CD1": "CA",
#        "CE1": "CA",
#        "CB": "CT",
#        "CE2": "CA",
#        "HA": "H1",
#        "HB3": "HC",
#        "HB2": "HC",
#    },
#    "Na+": {"Na+": "IP"},
#    "Cl-": {"Cl-": "IM"},
#    "CS": {"Cs+": "Cs"},
#    "IB": {"IB": "IB"},
#    "K+": {"K+": "K"},
#    "Li+": {"Li+": "Li"},
#    "MG": {"MG": "MG"},
#    "Rb+": {"Rb+": "Rb"},
#}
#
#tip3p_metal_map = {
#    "AL": {"AL": ["Al3+", "1.369", "0.01128487"]},
#    "Ag": {"Ag": ["Ag2+", "1.336", "0.00770969"]},
#    "BA": {"BA": ["Ba2+", "2.019", "0.40664608"]},
#    "BR": {"BR": ["Br-", "2.608", "0.0586554"]},
#    "Be": {"Be": ["Be2+", "0.956", "0.00000395"]},
#    "CA": {"CA": ["Ca2+", "1.649", "0.10592870"]},
#    "CD": {"CD": ["Cd2+", "1.412", "0.01773416"]},
#    "CE": {"CE": ["Ce3+", "1.782", "0.19865859"]},
#    "CL": {"CL": ["Cl-", "2.513", "0.0355910"]},
#    "CO": {"CO": ["Co2+", "1.299", "0.00483892"]},
#    "CR": {"CR": ["Cr3+", "1.415", "0.01827024"]},
#    "CS": {"CS": ["Cs+", "1.976", "0.4065394"]},
#    "CU": {"CU": ["Cu2+", "1.218", "0.00148497"]},
#    "Ce": {"Ce": ["Ce4+", "1.766", "0.18612361"]},
#    "Cl-": {"Cl-": ["Cl-", "2.513", "0.0355910"]},
#    "Cr": {"Cr": ["Cr2+", "1.346", "0.00868178"]},
#    "Dy": {"Dy": ["Dy3+", "1.637", "0.09900804"]},
#    "EU": {"EU": ["Eu2+", "1.802", "0.21475916"]},
#    "EU3": {"EU3": ["Eu3+", "1.716", "0.14920231"]},
#    "Er": {"Er": ["Er3+", "1.635", "0.09788018"]},
#    "F": {"F": ["F-", "2.303", "0.0033640"]},
#    "FE": {"FE": ["Fe3+", "1.443", "0.02387506"]},
#    "FE2": {"FE2": ["Fe2+", "1.353", "0.00941798"]},
#    "GD3": {"GD": ["Gd3+", "1.658", "0.11129023"]},
#    "HG": {"HG": ["Hg2+", "1.407", "0.01686710"]},
#    "Hf": {"Hf": ["Hf4+", "1.600", "0.07934493"]},
#    "IN": {"IN": ["In3+", "1.491", "0.03625449"]},
#    "IOD": {"I": ["I-", "2.860", "0.0536816"]},
#    "K+": {"K+": ["K+", "1.705", "0.1936829"]},
#    "K": {"K": ["K+", "1.705", "0.1936829"]},
#    "LA": {"LA": ["La3+", "1.758", "0.17997960"]},
#    "LI": {"LI": ["Li+", "1.025", "0.0279896"]},
#    "LU": {"LU": ["Lu3+", "1.625", "0.09235154"]},
#    "MG": {"MG": ["Mg2+", "1.360", "0.01020237"]},
#    "MN": {"MN": ["Mn2+", "1.407", "0.01686710"]},
#    "NA": {"NA": ["Na+", "1.369", "0.0874393"]},
#    "NI": {"NI": ["Ni2+", "1.255", "0.00262320"]},
#    "Na+": {"Na+": ["Na+", "1.369", "0.0874393"]},
#    "Nd": {"Nd": ["Nd3+", "1.724", "0.15486311"]},
#    "PB": {"PB": ["Pb2+", "1.745", "0.17018074"]},
#    "PD": {"PD": ["Pd2+", "1.303", "0.00509941"]},
#    "PR": {"PR": ["Pr3+", "1.780", "0.19707431"]},
#    "PT": {"PT": ["Pt2+", "1.266", "0.00307642"]},
#    "Pu": {"Pu": ["Pu4+", "1.752", "0.17542802"]},
#    "RB": {"RB": ["Rb+", "1.813", "0.3278219"]},
#    "Ra": {"Ra": ["Ra2+", "2.019", "0.40664608"]},
#    "SM": {"SM": ["Sm3+", "1.711", "0.14571499"]},
#    "SR": {"SR": ["Sr2+", "1.810", "0.22132374"]},
#    "Sm": {"Sm": ["Sm2+", "1.819", "0.22878796"]},
#    "Sn": {"Sn": ["Sn2+", "1.666", "0.11617738"]},
#    "TB": {"TB": ["Tb3+", "1.671", "0.11928915"]},
#    "Th": {"Th": ["Th4+", "1.770", "0.18922704"]},
#    "Tl": {"Tl": ["Tl3+", "1.571", "0.06573030"]},
#    "Tm": {"Tm": ["Tm3+", "1.647", "0.10475707"]},
#    "U4+": {"U": ["U4+", "1.792", "0.20665151"]},
#    "V2+": {"V2+": ["V2+", "1.364", "0.01067299"]},
#    "Y": {"Y": ["Y3+", "1.630", "0.09509276"]},
#    "YB2": {"YB2": ["Yb2+", "1.642", "0.10185975"]},
#    "ZN": {"ZN": ["Zn2+", "1.271", "0.00330286"]},
#    "Zr": {"Zr": ["Zr4+", "1.609", "0.08389240"]},
#}
#
## Mutation rule related
## ===============================================
## Residue catageries (subgroups)
## MMPB(GB)SA related
## Radii mapping with igb methods
#radii_map = {
#    "1": "mbondi",
#    "2": "mbondi2",
#    "5": "mbondi2",
#    "7": "bondi",
#    "8": "mbondi3",
#}
#
## {connecting_atom : H type} Base on http://www.uoxray.uoregon.edu/local/manuals/biosym/discovery/General/Forcefields/AMBER.html
## ff96_H_map = {'N2':'H', 'N':'H', 'CT':'HC', 'CA':'HA', 'OH':'HO', 'SH':'HS', 'OW':'HW', 'CR':'H5', 'CV':'H4', 'CR':'H5'}
## a list of meaningless co-crystaled "ligands". Do not read in Structure.fromPDB.
#rd_non_ligand_list = ["CL", "EDO", "GOL"]
#rd_solvent_list = ["HOH", "WAT"]
