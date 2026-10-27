"""Explicit Turtle-compatible subset. No entailment, temporal or business logic.

Not a full Turtle 1.1 implementation: see README for accepted input syntax.
"""
from dataclasses import dataclass
from pathlib import Path
import re

XSD='http://www.w3.org/2001/XMLSchema#'
RDF='http://www.w3.org/1999/02/22-rdf-syntax-ns#'
PNAME=re.compile(r'(?:[A-Za-z_][A-Za-z0-9_-]*)?:[A-Za-z0-9_][A-Za-z0-9_-]*')
PREFIX=re.compile(r'(?:[A-Za-z_][A-Za-z0-9_-]*)?:')
INTEGER=re.compile(r'[+-]?[0-9]+')
LANG=re.compile(r'@[A-Za-z]+(?:-[A-Za-z0-9]+)*')
SCHEME=re.compile(r'^[A-Za-z][A-Za-z0-9+.-]*:')

@dataclass(frozen=True)
class Term:
    kind: str
    value: str
    datatype: str=''
    language: str=''

def unescape(text):
    out=[];i=0
    escapes={'t':'\t','b':'\b','n':'\n','r':'\r','f':'\f','"':'"',"'":"'",'\\':'\\'}
    while i<len(text):
        if text[i]!='\\':out.append(text[i]);i+=1;continue
        i+=1
        if i>=len(text):raise ValueError('incomplete escape')
        if text[i] in ('u','U'):
            width=4 if text[i]=='u' else 8;token=text[i+1:i+1+width]
            if len(token)!=width or not re.fullmatch('[0-9a-fA-F]+',token):raise ValueError('invalid Unicode escape')
            code=int(token,16)
            if code>0x10ffff or 0xd800<=code<=0xdfff:raise ValueError('invalid Unicode scalar')
            out.append(chr(code));i+=width+1
        else:
            if text[i] not in escapes:raise ValueError('unsupported escape')
            out.append(escapes[text[i]]);i+=1
    return ''.join(out)

def tokenize(text):
    tokens=[];i=0
    while i<len(text):
        ch=text[i]
        if ch.isspace():i+=1;continue
        if ch=='#':
            end=text.find('\n',i);i=len(text) if end<0 else end+1;continue
        if ch in ';,.':tokens.append((ch,ch));i+=1;continue
        if text.startswith('^^',i):tokens.append(('^^','^^'));i+=2;continue
        if text.startswith('@prefix',i) and (i+7==len(text) or text[i+7].isspace()):
            tokens.append(('PREFIX','@prefix'));i+=7;continue
        if ch=='<':
            end=text.find('>',i+1)
            if end<0:raise ValueError('unterminated IRI')
            raw=text[i+1:end]
            if re.search(r'[\x00-\x20<>"{}|^`]',raw):raise ValueError('invalid IRI character')
            if re.search(r'\\(?!u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8})',raw):raise ValueError('unsupported IRI escape')
            iri=unescape(raw)
            if not SCHEME.match(iri):raise ValueError('absolute IRI required')
            tokens.append(('IRI',iri));i=end+1;continue
        if ch=='"':
            end=i+1
            while end<len(text):
                if text[end]=='\\':end+=2;continue
                if text[end]=='"':break
                if text[end] in '\r\n':raise ValueError('multiline strings outside subset')
                end+=1
            if end>=len(text):raise ValueError('unterminated string')
            tokens.append(('STRING',unescape(text[i+1:end])));i=end+1;continue
        found=False
        for kind,pattern in [('PNAME',PNAME),('PREFIX_NAME',PREFIX),('INTEGER',INTEGER),('LANG',LANG)]:
            match=pattern.match(text,i)
            if match:
                tokens.append((kind,match.group()));i=match.end();found=True;break
        if found:continue
        for word in ('true','false','a'):
            if text.startswith(word,i) and (i+len(word)==len(text) or text[i+len(word)].isspace() or text[i+len(word)] in ';,.#'):
                tokens.append(('A' if word=='a' else 'BOOLEAN',word));i+=len(word);found=True;break
        if not found:raise ValueError('unsupported syntax at character '+str(i))
    return tokens

class Parser:
    def __init__(self,text):self.tokens=tokenize(text);self.pos=0;self.prefixes={}
    def peek(self,kind):return self.pos<len(self.tokens) and self.tokens[self.pos][0]==kind
    def take(self,kind=None):
        if self.pos>=len(self.tokens):raise ValueError('unexpected end of input')
        token=self.tokens[self.pos]
        if kind is not None and token[0]!=kind:raise ValueError('expected '+kind+', got '+token[0])
        self.pos+=1;return token[1]
    def iri(self):
        if self.peek('IRI'):return Term('iri',self.take())
        if self.peek('PNAME') or self.peek('PREFIX_NAME'):
            prefix,local=self.take().split(':',1)
            if prefix not in self.prefixes:raise ValueError('undefined prefix: '+prefix)
            return Term('iri',self.prefixes[prefix]+local)
        raise ValueError('IRI or supported prefixed name required')
    def object(self):
        if self.peek('STRING'):
            value=self.take();datatype=XSD+'string';language=''
            if self.peek('^^'):self.take();datatype=self.iri().value
            elif self.peek('LANG'):language=self.take()[1:].lower();datatype=RDF+'langString'
            if datatype==XSD+'integer' and not INTEGER.fullmatch(value):raise ValueError('invalid integer lexical form')
            if datatype==XSD+'boolean' and value not in ('true','false','1','0'):raise ValueError('invalid boolean lexical form')
            return Term('literal',value,datatype,language)
        if self.peek('INTEGER'):return Term('literal',self.take(),XSD+'integer')
        if self.peek('BOOLEAN'):return Term('literal',self.take(),XSD+'boolean')
        return self.iri()
    def parse(self):
        result=set()
        while self.pos<len(self.tokens):
            if self.peek('PREFIX'):
                self.take();name=self.take('PREFIX_NAME')[:-1];self.prefixes[name]=self.take('IRI');self.take('.');continue
            subject=self.iri()
            while True:
                if self.peek('A'):self.take();predicate=Term('iri',RDF+'type')
                else:predicate=self.iri()
                while True:
                    result.add((subject,predicate,self.object()))
                    if not self.peek(','):break
                    self.take(',')
                if not self.peek(';'):break
                self.take(';')
                if self.peek('.'):break
            self.take('.')
        return result

def parse_text(text):return Parser(text).parse()

def load_graph(folder):
    result=set()
    for path in sorted(Path(folder).glob('*.ttl')):
        result.update(parse_text(path.read_text(encoding='utf-8')))
    return result
