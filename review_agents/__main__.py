import sys

if __name__ == "__main__":
    if sys.version_info < (3, 10):
        print(
            f"Python 3.10 or newer is required (found {sys.version.split()[0]}). "
            "Run with an installed newer interpreter, for example: python3.12 -m review_agents",
            file=sys.stderr,
        )
        raise SystemExit(2)

    from .cli import main

    raise SystemExit(main())
