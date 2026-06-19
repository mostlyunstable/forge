# ADR-0004: Tree-sitter for Code Parsing

## Problem
Forge must extract structured metadata (classes, functions, interfaces, enums) from source code. Regular expressions are fragile and language-specific.

## Options
1. **Tree-sitter**: Incremental parsing, 40+ languages, error-tolerant
2. **AST modules** (ast for Python): Language-specific, no cross-language support
3. **Regex extraction**: Simple but fragile, misses nested structures
4. **LSP integration**: Accurate but requires running language servers

## Decision
Tree-sitter. It provides fast, incremental parsing with error tolerance (can parse incomplete code). Supports Python, TypeScript, JavaScript out of the box with the same API.

## Tradeoffs
- **Pro**: Single parser for all supported languages
- **Pro**: Error-tolerant (works on partial/invalid code)
- **Pro**: Incremental (only re-parses changed sections)
- **Con**: External C dependency
- **Con**: Grammar installation required per language

## Status
Accepted

## Date
2026-06-18
