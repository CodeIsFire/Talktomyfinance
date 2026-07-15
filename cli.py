from __future__ import annotations

from agents.orchestrator import answer_query


def main() -> None:
    print("Finance assistant ready. Type 'quit' to exit.")
    while True:
        try:
            query = input("\nAsk a finance question: ").strip()
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

        if not query:
            continue
        if query.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break

        answer = answer_query(query)
        print(answer)


if __name__ == "__main__":
    main()
