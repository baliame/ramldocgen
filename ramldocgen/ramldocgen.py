import click
from .generator import Generator

@click.group()
def cli():
    pass

@cli.command()
@click.argument('infile')
@click.argument('outfile')
def generate(infile, outfile):
    g = Generator(infile)
    with open(outfile, 'w') as target:
        target.write(g.generate())
