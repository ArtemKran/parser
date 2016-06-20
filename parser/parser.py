#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import tools


class _Reader(object):
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.completed = False

    def __iter__(self):
        return self

    def __next__(self):
        try:
            to_return = self.text[self.pos]
        except IndexError:
            self.completed = True
            raise StopIteration

        self.pos += 1
        return to_return

    def seek_back(self, num):
        self.pos += num


class Parser(object):
    standart = {
      'quotes': ['"', "'"],
      'spaces': [' ', '\t', '\n'],
      'tag': {
        'allowed_symbols': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_',
        'allowed_first_symbols': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
        'unpaired': ['input', 'br', 'hr', 'meta', 'link', 'image', 'img', 'col'],
        'ignore_content': ['style', 'script']
      },
      'attribute': {
        'allowed_symbols': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_:',
      },
    }
    doctype = {
      'html_or_xml': '',
      'lang': '',
      'type': ''
    }
    _current_parent = None
    roots = tools.BondedList(parent=None)
    _header_text = ''

    def __init__(self, file):
        # text = file.read() if type(file) != str else file
        self.i = _Reader(file)

    def error(self, text='Something wrong here'):
        lines = self.i.text[:self.i.pos].splitlines()
        pos = len(lines[-1])
        line_num = len(lines)
        line = self.i.text.splitlines()[line_num-1]
        self.onerror(line_num, line, pos, text)

    def onerror(self, num, line, position, comment):
        print('{} (on line {}):'.format(comment, num))
        print(line)
        print(' '*position + '^')

    def parse(self):
        for char in self.i:
            if char == '<':
                char = next(self.i)
                if char in self.standart['tag']['allowed_first_symbols']:
                    self.i.seek_back(-1)
                    self.read_tag()
                elif char == '?':
                    self.read_header('xml')
                elif char == '/':
                    self.close_tag()
                elif char == '!':
                    if next(self.i) + next(self.i) == '--':
                        self.read_comment()
                    else:
                        self.i.seek_back(-2)
                        self.read_header('html')
                else:
                    self.error('Invalid character in the tag name')
            else:
                self.i.seek_back(-1)
                self.read_text()
        if self._current_parent is not None:
            self.error('Unexpected end')

    # list of different doctypes is in the end of the page
    def read_header(self, lang):
        self.doctype['html_or_xml'] = lang

        if lang == 'html':
            doctype = ''
            for char in self.i:
                if char != '>':
                    doctype += char
                else:
                    break
            for space in self.standart['spaces']:
                doctype.replace(space, ' ')
            self._header_text = '<!' + doctype + '>'
            doctype = [x.lower() for x in doctype.split(' ') if x != '']
            if len(doctype) < 2 or doctype[0] != 'doctype' or doctype[1] != 'html':
                self.error('Invalid doctype declaration')
            if len(doctype) == 2:
                self.doctype['lang'] = 'html 5.0'
            else:
                if not '//' in doctype[5]:
                    self.doctype['lang'] = doctype[4] + ' ' + doctype[5]
                    self.doctype['type'] = doctype[6][:-5]
                elif doctype[5] == 'basic':
                    self.doctype['lang'] = 'xhtml 1.0'
                    self.doctype['type'] = 'basic'
                else:
                    self.doctype['lang'] = doctype[4] + ' ' + doctype[5][:-5]
                    self.doctype['type'] = 'strict'
        else:
            self.standart['tag']['unpaired'] = []
            for char in self.i:
                if char == '?' and next(self.i) == '>':
                    break

    def read_tag(self):
        has_attrs = True
        paired = True
        name = next(self.i)

        for char in self.i:
            if not char in self.standart['tag']['allowed_symbols']:
                if char in self.standart['spaces']:
                    self.i.seek_back(-1)
                    break
                if char == '/':
                    if next(self.i) != '>':
                        self.error('Invalid character in the tag')
                    has_attrs = False
                    paired = False
                    break
                if char == '>':
                    has_attrs = False
                    break
                else:
                    self.error('Invalid character in the tag name')
            name += char
        tag = tools.Element(name)
        if has_attrs:
            self.read_attrs(tag)
        if tag.paired:
            tag.paired = paired
        self.append_node(tag)
        if not name in self.standart['tag']['unpaired'] and tag.paired:
            self._current_parent = tag
        if name in self.standart['tag']['ignore_content']:
            self.ignore_content(tag)

    def read_attrs(self, tag):
        for char in self.i:
            if char in self.standart['attribute']['allowed_symbols']:
                self.i.seek_back(-1)
                self.read_attr(tag)
            elif char == '>':
                break
            elif char == '/' and next(self.i) == '>':
                tag.paired = False
                break
            elif not char in self.standart['spaces']:
                self.error('Invalid character in the attribute name')

    def read_attr(self, tag):
        name = self.read_attr_name()
        value = ''
        for char in self.i:
            if char == '=':
                value = self.read_attr_value()
                break
            elif char in self.standart['attribute']['allowed_symbols']:
                self.i.seek_back(-1)
                break
            elif char == '>':
                self.i.seek_back(-1)
                break
            elif char == '/' and next(self.i) == '>':
                self.i.seek_back(-2)
                break
            elif not char in self.standart['spaces']:
                self.error('Invalid character in the attribute')
        tag.attributes[name] = value

    def read_attr_name(self):
        name = ''
        for char in self.i:
            if char in self.standart['spaces']:
                if name:
                    break
            elif char in self.standart['attribute']['allowed_symbols']:
                name += char
            elif char == '>' or char == '=':
                self.i.seek_back(-1)
                break
            elif char == '/' and next(self.i) == '>':
                self.seek_back(-2)
            else:
                self.error('Invalid character in the attribute name')
        return name

    def read_attr_value(self):
        value = ''
        quote = ''
        for char in self.i:
            if quote == char:
                break
            if char in self.standart['quotes']:
                if not (value and quote):
                    quote = char
                    continue
            elif char in self.standart['spaces']:
                if not quote and value:
                    self.i.seek_back(-1)
                    break
                elif not (value and quote):
                    continue

            elif not quote:
                if char == '>':
                    self.i.seek_back(-1)
                    break
                elif char == '/' and next(self.i) == '>':
                    self.i.seek_back(-2)
                    break
            value += char
        return value

    def ignore_content(self, tag):
        length_of_end = len(tag.name) + 3
        val = ''
        for char in self.i:
            val += char
            if char == '>':
                if val[-length_of_end:] == '</' + tag.name + '>':
                    val = val[:-length_of_end]
                    self.i.seek_back(-length_of_end)
                    break

        content = tools.Text(val)
        tag.childNodes.add(content)

    def close_tag(self):
        name = ''
        for char in self.i:
            if char == '>':
                break
            else:
                name += char
        if self._current_parent is None:
            self.error('Error with nested tags')
        if name != self._current_parent.name:
            self.error('Error with nested tags')
        self._current_parent = self._current_parent.parent

    def read_comment(self):
        text = ''
        for char in self.i:
            if char == '-':
                if next(self.i) + next(self.i) == '->':
                    break
                else:
                    self.i.seek_back(-2)
            text += char
        node = tools.Comment(text)
        self.append_node(node)

    def read_text(self):
        text = ''
        for char in self.i:
            if char == '<':
                self.i.seek_back(-1)
                break
            if type(char) == int:
                if type(text) == str:
                    text += str(char)
                else:
                    text += bytes(char)
            else:
                text += char
        node = tools.Text(text)
        self.append_node(node)

    def append_node(self, node):
        if self._current_parent is not None:
            self._current_parent.childNodes.add(node)
            node.parent = self._current_parent
        else:
            self.roots.add(node)

    def foreach(self, func):
        return self.roots.foreach(func)

    def get_elements_by_tag_name(self, name):
            return self.roots.get_elements_by_tag_name(name)

    def get_elements_by_attr_name(self, name, val):
            return self.roots.get_elements_by_attr_name(name, val)


class NotStrictParser(Parser):
    def error(self, text='Something wrong here'):
        if text != 'Unexpected end':
            Parser.error(self, text)

    def close_tag(self):
        name = ''
        for char in self.i:
            if char == '>':
                break
            name += char
        if self._current_parent is None:
            return
        if self._current_parent.name == name:
            self.current_parent = self._current_parent.parent
            return
        if self._current_parent.parent is not None and self._current_parent.parent.name == name:
            self._current_parent = self._current_parent.parent.parent

