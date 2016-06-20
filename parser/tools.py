#!/usr/bin/env python
# -*- coding: utf-8 -*-


class NodeList(object):
    def __init__(self, *args):
        self.elements = []
        self.add(*args)
    
    def add(self, *args):
        for arg in args:
            self.elements.append(arg)
    
    def remove(self, *args):
        for arg in args:
            if arg in self:
                self.elements.remove(arg)
    
    def add_to(self, pos, arg):
        old_list = self.elements
        new_list = []
        for i in range(len(old_list)+1):
            if i < pos:
                new_list.append(old_list[i])
            elif i == pos:
                new_list.append(arg)
            else:
                new_list.append(old_list[i-1])
        self.elements = new_list
        
    def foreach(self, func, deep=False):
        to_return = NodeList()
        for node in self:
            if func(node):
                to_return.add(node)
            if node.nodeType == 1 and deep:
                to_return.add(*node.foreach(func, True))
        return to_return
    
    def by_name(self, name, deep=False):
        return self.foreach(lambda x: x.nodeType == 1 and x.name == name, deep)
        
    def with_attr(self, name, deep=False):
        return self.foreach(lambda x: x.nodeType == 1 and name in x.attributes, deep)
        
    def by_attr(self, name, value, deep=False):
        return self.foreach(lambda x: x.nodeType == 1 and name in x.attributes and x.attributes[name] == value, deep)
        
    def __getitem__(self, index):
        return self.elements[index]
    
    def __bool__(self):
        return bool(self.elements)
    
    def __len__(self):
        return len(self.elements)

    
class BondedList(NodeList):
    def __init__(self, parent):
        NodeList.__init__(self)
        self.common_parent = parent
    
    def add(self, *args):
        for arg in args:
            if self:
                self[-1].next_sibling = arg
                arg.previous_sibling = self[-1]
            arg.parent = self.common_parent
            NodeList.add(self, arg)
    
    def remove(self, *args):
        for arg in args:
            if arg in self:
                i = self.elements.index(arg)
                
                if self[i].previous_sibling is not None:
                    self[i].previous_sibling.next_sibling = self[i].next_sibling
                    
                if self[i].next_sibling is not None:
                    self[i].next_sibling.previous_sibling = self[i].previous_sibling
                
                NodeList.remove(self, arg)
    
    def add_to(self, pos, arg):
        arg.parent = self.common_parent
        if pos == 0:
            self[0].previous_sibling = arg
            arg.nextSibling = self[0]
            
        elif pos < len(self):
            self[pos].previous_sibling = arg
            arg.nextSibling = self[pos]
            self[pos-1].next_sibling = arg
            arg.previousSibling = self[pos-1]
            
        elif pos == len(self):
            self[pos-1].next_sibling = arg
            arg.previousSibling = self[pos-1]
        
        NodeList.add_to(self, pos, arg)

            
class Node(object):
    parent = None
    nextSibling = None
    previousSibling = None
        
    def remove(self):
        if self.nextSibling:
            self.nextSibling.previousSibling = self.previousSibling
        if self.previousSibling:
            self.previousSibling.nextSibling = self.nextSibling
        if self.parent:
            self.parent.childNodes.remove(self)
    
    def insert_before(self, node):
        if self.parent is not None:
            index = self.parent.childNodes.elements.index(self)
            self.parent.childNodes.add_to(index, node)
    
    def insert_after(self, node):
        if self.parent is not None:
            index = self.parent.childNodes.elements.index(self)
            self.parent.childNodes.add_to(index+1, node)

            
class TextNode(Node):
    def __init__(self, content=''):
        self.content = content 
        
      
class Comment(TextNode):
    nodeType = 8
    nodeName = 'comment'
    
    def __init__(self, content=''):
        TextNode.__init__(self, content)


class Text(TextNode):
    nodeType = 3
    nodeName = 'text'
    
    def __init__(self, content=''):
        TextNode.__init__(self, content)


class Element(Node):
    nodeType = 1
    nodeName = 'element'
    paired = True
    
    def __init__(self, name=''):
        self.name = name
        self.attributes = {}
        self.childNodes = BondedList(parent=self)
        
    def squeeze(self):
        if self.parent is not None:
            parent = self.parent
            pos = parent.childNodes.elements.index(self)
            children = self.childNodes
            self.remove()
            for node in children:
                parent.childNodes.add_to(pos, node)
                pos += 1
        
    def foreach(self, func, deep=True):
        return self.childNodes.foreach(func, deep)

    def by_name(self, name, deep=True):
        return self.childNodes.by_name(name, deep)
        
    def with_attr(self, name, deep=True):
        return self.childNodes.with_attr(name, deep)

    def by_attr(self, name, value, deep=True):
        return self.childNodes.by_attr(name, value, deep)
