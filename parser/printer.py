#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import parser


class Printer(object):
    def __init__(self, parser=parser.Parser):
        self.parser = parser
    
    def print_node(self, node, compress=True, print_it=True, deep=True, pretty=False, tab='    ', _n=0):
        space = '\n' + tab * _n if pretty else ''
        
        to_return = ''
        if node.nodeType == 3:
            if compress:
                if node.content.strip():
                    to_return += space + node.content
            else:
                to_return += space + node.content
        
        if node.nodeType == 8:
            if not compress:
                to_return += space + '<!--' + node.content + '-->'
        
        if node.nodeType == 1:
            to_return += space + '<' + node.name
            for attr in node.attributes.keys():
                to_return += ' {}="{}"'.format(attr, node.attributes[attr])
            
            if node.name in self.parser.standart['tag']['unpaired'] or not node.paired:
                to_return += ' /'
            to_return += '>'
            if node.childNodes:
                if not deep: to_return += '...'
                else:
                    for elt in node.childNodes:
                        to_return += self.print_node(
                            elt,
                            compress=compress,
                            print_it=False,
                            deep=True,
                            pretty=pretty,
                            tab=tab,
                            _n=_n + 1
                        )
            
            if not node.name in self.parser.standart['tag']['unpaired'] and node.paired:
                to_return += space + '</' + node.name + '>'
        
        if print_it:
            print(to_return)
        else:
            return to_return

    def mprint(self, print_it=True):
        to_return = self.parser._header_text
        for elt in self.parser.roots:
            to_return += self.print_node(elt, print_it=False)
        if print_it:
            print(to_return)
        else:
            return to_return
        
# this method ought to print document without changes, but it incorrect yet 
#    def sprint(self, print_it=True):
#        to_return = self.parser._header_text
#        for elt in self.parser.roots:
#            to_return += self.print_node(elt, compress=False, print_it=False)
#        if print_it: print(to_return)
#        else: return to_return

    def pprint(self, print_it=True, tab='    ', _n = 0):
        to_return = self.parser._header_text
        for elt in self.parser.roots:
            to_return += self.print_node(elt, print_it=False, pretty=True, tab=tab)
        if print_it:
            print(to_return)
        else:
            return to_return
