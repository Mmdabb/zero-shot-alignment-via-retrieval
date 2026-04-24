"""
Interactive terminal test for Zero-Shot Alignment via Retrieval.

Run from the project root:

    python interactive_alignment_test.py

Behavior:
- Ask for user query.
- Ask for optional base response.
- If base response is empty, the system auto-generates it.
- Prints before/after alignment and retrieval details.
"""

from alignment import ZeroShotAlignmentSystem


def print_result(result: dict) -> None:
    print("\n" + "=" * 80)
    print("ALIGNMENT RESULT")
    print("=" * 80)

    print(f"\nUser Query:\n{result['original_prompt']}")

    print("\nSystem Info:")
    print(f"  Retrieval Model:      {result.get('retrieval_model')}")
    print(f"  Base Response Source: {result.get('base_response_source')}")
    print(f"  Base Provider:        {result.get('base_provider')} / {result.get('base_model')}")
    print(f"  Alignment Provider:   {result.get('alignment_provider')} / {result.get('alignment_model')}")
    print(f"  Retrieved Style:      {result.get('best_style')}")

    print("\nTop-k Style Scores:")
    for style_name, score in result.get("top_styles", []):
        print(f"  - {style_name:<10} {score:.4f}")

    print("\n--- BEFORE ALIGNMENT: Base Response ---")
    print(result.get("base_response", ""))

    print("\n--- AFTER ALIGNMENT: Final Styled Response ---")
    print(result.get("styled_response", ""))

    print("\n--- Retrieved Style Prompt ---")
    print(result.get("style_prompt_augmentation", ""))

    print("\nProvider Attempts:")
    for attempt in result.get("provider_attempts", []):
        status = "succeeded" if attempt.get("success") else "failed"
        print(f"  - {attempt.get('task')} | {attempt.get('provider')}: {status}")

    print(f"\nLog File:\n{result.get('log_file')}")

    print("=" * 80 + "\n")


def main() -> None:
    system = ZeroShotAlignmentSystem()

    print("\nInteractive Zero-Shot Alignment Test")
    print("Type 'exit' or 'quit' as the query to stop.")
    print("Leave base response empty to auto-generate it.\n")

    while True:
        query = input("User query: ").strip()

        if query.lower() in {"exit", "quit"}:
            print("Exiting.")
            break

        if not query:
            print("Please enter a non-empty query.\n")
            continue

        base_response = input("Optional base response override [press Enter to auto-generate]: ").strip()

        if base_response:
            result = system.align_response(prompt=query, response=base_response)
        else:
            result = system.align_response(prompt=query)

        print_result(result)


if __name__ == "__main__":
    main()
