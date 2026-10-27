"""Generic graph inspection only; no admission behavior."""
import argparse
import json
from dataclasses import asdict
from rdf_subset import load_graph

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('input_directory')
    parser.add_argument('--predicate',help='optional exact predicate IRI filter')
    parser.add_argument('--count',action='store_true')
    args=parser.parse_args()
    graph=load_graph(args.input_directory)
    selected=[triple for triple in graph if args.predicate is None or triple[1].value==args.predicate]
    if args.count:print(json.dumps({'tripleCount':len(selected)}));return
    for triple in sorted(selected,key=lambda triple:repr(triple)):
        print(json.dumps([asdict(term) for term in triple],ensure_ascii=False))

if __name__ == '__main__':
    main()
