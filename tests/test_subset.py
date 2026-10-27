"""Generic parser/reader behavior only; no admission algorithm or truth tables."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from rdf_subset import load_graph,parse_text,XSD,RDF

class ReaderTests(unittest.TestCase):
    def test_punctuation_and_union(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'a.ttl').write_text('@prefix x: <urn:x:> . x:a x:p x:b, x:c ; x:q 2 . # comment\n',encoding='utf-8')
            (root/'b.ttl').write_text('<urn:x:a> <urn:x:p> <urn:x:b> .',encoding='utf-8')
            self.assertEqual(len(load_graph(root)),3)
    def test_empty(self):
        with tempfile.TemporaryDirectory() as folder:self.assertEqual(load_graph(folder),set())
    def test_type_keyword_and_language(self):
        triples=parse_text('@prefix : <urn:x:> . :one a :Kind ; :label "你好"@zh-CN ; .')
        self.assertEqual(len(triples),2)
        self.assertTrue(any(p.value==RDF+'type' and o.value=='urn:x:Kind' for s,p,o in triples))
        self.assertTrue(any(o.language=='zh-cn' for s,p,o in triples))
    def test_typed_values(self):
        triples=parse_text('@prefix xsd: <http://www.w3.org/2001/XMLSchema#> . <urn:a> <urn:p> "+002"^^xsd:integer, "1"^^xsd:boolean, false .')
        self.assertEqual({(o.datatype,o.value) for s,p,o in triples},{(XSD+'integer','+002'),(XSD+'boolean','1'),(XSD+'boolean','false')})
    def test_unicode_escape(self):
        triples=parse_text('<urn:a\\u0031> <urn:p> "a\\n\\\"b\\U0001F642" .')
        s,p,o=next(iter(triples));self.assertEqual(s.value,'urn:a1');self.assertEqual(o.value,'a\n"b🙂')
    def test_excluded_syntax(self):
        for text in ['[] <urn:p> <urn:o> .','@base <urn:x:> .','<relative> <urn:p> true .','<urn:a> <urn:p> 1.5 .']:
            with self.subTest(text=text),self.assertRaises(ValueError):parse_text(text)
    def test_cli_count(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder)/'a.ttl').write_text('<urn:a> <urn:p> <urn:b> .',encoding='utf-8')
            process=subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'reference_reader.py'),folder,'--count'],capture_output=True,text=True,check=True)
            self.assertEqual(json.loads(process.stdout),{'tripleCount':1})

if __name__=='__main__':unittest.main()
