from forge.infrastructure.code_indexer.tree_sitter_parser import TreeSitterParser


def test():
    parser = TreeSitterParser()
    with open("src/forge/application/indexing/full_index_usecase.py") as f:
        content = f.read()

    entries = parser.parse_file("src/forge/application/indexing/full_index_usecase.py", content)
    for e in entries:
        print(f"[{e.entry_type.name}] {e.name}: {len(e.content)} chars")
        if e.name == "FullIndexUseCase":
            print(f"--- FullIndexUseCase chunk ---\n{e.content}\n-----------------------------")


if __name__ == "__main__":
    test()
