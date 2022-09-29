"""This class summarized data structure level operation from Structure/Chain/Residue/Atom, which
are designed to contain data in the doublelinked manner, that is, a parent object holds a list
of children objects while each children object also holds a reference of the parent object. (e.g:
Chain().residues[0].chain is the first Chain object)

Common operations from such summarization are:
set/get_parent (set_ghost_children for leafs)
set/get_children (set_ghost_parent for the root, these are designed so that the summarized class
                  know what to expect.)
__deepcopy__
__getitem__
__delitem__
__len__

Author: QZ Shao, <shaoqz@icloud.com>
Date: 2022-09-14
"""

import copy
from typing import Any, Dict, List, Union


class DoubleLinkedNode():
    """
    class for parent objects of the doubly linked tree
    """
    #region === Attr ===
    # parent use
    def set_children(self, children: List):
        """
        set children and add self as parent of children
        """
        self._children = children
        for child in self._children:
            child.parent = self

    def set_ghost_children(self):
        """
        method for the node with no children to set
        The idea is DoubleLinkNode defines what to set when no children
        """
        self._children = None

    def get_children(self) -> List:
        return self._children

    # api out of class use
    @property
    def children(self) -> List:
        return self.get_children()
    @children.setter
    def children(self, val):
        self.set_children(val)

    # child use
    def set_parent(self, parent):
        """
        only set parent to self
        * do not add self to parent"s children
        """
        self._parent = parent

    def set_ghost_parent(self):
        """
        method for the node with no parent to set
        The idea is DoubleLinkNode defines what to set when no parent
        """
        self._parent = None

    def get_parent(self):
        return self._parent

    # api out of class use
    @property
    def parent(self) -> List:
        return self.get_parent()
    @parent.setter
    def parent(self, val):
        self.set_parent(val)
    #endregion

    #region === edit ===
    def delete_from_parent(self) -> None:
        """
        delete self from parent's children list
        delete base on object's id()
        Returns:
            None. changes are made to the .children list in self.parent
        """
        delete_base_on_id(self.parent.children, id(self))

    # def __deepcopy__(self, memo: Union[Dict[int, Any], None]):
    #     """
    #     support deepcopy of the object
    #     shallow copy wont cause any problem but deepcopy do as explained on:
    #     https://docs.python.org/3.10/library/copy.html?highlight=deepcopy
    #     Deepcopy of the Node returns a new Node with empty parent and full children copies
    #     This behavior is mimicing copy part of the structure given any structure parts identifier
    #     (e.g.: copy chain A will give all residues, atoms in chain A but dont need chain B, C, etc.)
    #     """
    #     result = copy.copy(self)
    #     result.set_ghost_parent()
    #     #TODO
    #     # it seems built-in deepcopy handle this pretty well

    def deepcopy_without_parent(self):
        """
        support another version of deepcopy that donot copy any parent and siblings TODO maybe make this default
        """
        parent_holder = self.parent
        self.parent = None
        result = copy.deepcopy(self)
        self.parent = parent_holder
        return result
    #endregion

    # === special ===
    def __getitem__(self, key: int):
        return self._children[key]

    def __delitem__(self, key: int):
        del self._children[key]

    def __len__(self) -> int:
        return len(self._children)

# TODO go to other core
def delete_base_on_id(target_list: list, target_id: int):
    """
    delete an element from a list base on its id() value
    """
    for i in range(len(target_list)-1,-1,-1):
        if id(target_list[i]) == target_id:
            del target_list[i]
