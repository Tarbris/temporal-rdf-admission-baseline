# Independent finite RDF reader baseline

This author-created, AI-assisted baseline uses only the Python standard library. It loads the set union of supported Turtle-compatible triples from all `.ttl` files in a directory and supports exact predicate filtering or counting. It is not a full Turtle 1.1 parser or a SPARQL engine. It performs no identity entailment, class entailment, temporal selection, authorization decision, or business aggregation.

## Explicit accepted syntax

- UTF-8 text. Whitespace and `#` line comments separate tokens.
- Absolute `<IRI>` terms; Unicode is permitted, and `\uHHHH` / `\UHHHHHHHH` Unicode scalar escapes are supported. Relative IRIs, `@base`, and BASE are excluded.
- `@prefix prefix: <absolute-IRI> .` declarations local to one file. The prefix is empty or matches `[A-Za-z_][A-Za-z0-9_-]*`. A nonempty local name matches `[A-Za-z0-9_][A-Za-z0-9_-]*`; an empty local name is also supported. No other prefixed-name escaping or punctuation is accepted.
- Named IRI subjects/predicates. Predicate `a` abbreviates the RDF type IRI. Triples end with `.`, predicate lists use `;`, object lists use `,`; an optional final `;` is accepted.
- Objects can be IRIs, bare signed decimal integers, `true`/`false`, or short double-quoted strings. String escapes are `\t`, `\b`, `\n`, `\r`, `\f`, `\"`, `\'`, `\\`, `\uHHHH`, and `\UHHHHHHHH`. Raw newlines inside strings are excluded.
- Strings may have `^^datatype-IRI` or a language tag matching `@[A-Za-z]+(-[A-Za-z0-9]+)*`. Integer and boolean datatypes validate their lexical form; integers permit signs and leading zeros, booleans permit `true`, `false`, `1`, `0`. Language tags are case-normalized.
- Blank nodes, collections, property lists, long/single-quoted strings, decimal/exponent numeric shortcuts, named graphs, RDF-star, imports, and every unlisted syntax form are outside this subset. No network operations occur.

RDF terms retain kind, decoded lexical value, datatype, and language. Graph union removes duplicate identical RDF terms, without treating distinct lexical forms as identical RDF terms. Business numeric interpretation belongs to the task contract. The public tests concern this generic subset only; there is no task-specific oracle or completed business implementation.

## Run

CPython 3.11+; no packages to install. From this directory:

```sh
python3 reference_reader.py ../workloads/sample --count
python3 reference_reader.py ../workloads/sample --predicate http://www.w3.org/1999/02/22-rdf-syntax-ns#type
python3 -m unittest discover -s tests -v
```

Without `--count`, each stdout JSON line is a triple of term records. `--count` returns `{"tripleCount":N}`. With `--predicate`, only exact predicate matches are selected. The future admission processor has a separate JSONL request/response interface specified by proposal.json. Nothing here implements that target.

This baseline was created for this task; it is not represented as a pre-existing third-party project. AI assistance is disclosed and independent human authorship is not asserted. License: MIT.
