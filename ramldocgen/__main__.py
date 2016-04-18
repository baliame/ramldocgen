import sys
from .ramldocgen import cli

def main():
    sys.argv[0] = "ramldocgen"
    cli.main()

if __name__ == "__main__":
    main()