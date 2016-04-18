# HTML documentation generator from RAML

A python implementation of generating a concise and easy to use documentation page from a RAML description of an API. This tool is heavily inspired by the node.js equivalent, https://github.com/raml2html/raml2html.

## Installation

The tool has been developed with Python 3.5 and has been tested with Python 3.3 and Python 3.4. Python 2.7 will not be supported due to major differences in how unicode strings are handled across the two major versions.

Use pip to install the tool.

```
pip3 install ramldocgen
```

## Usage

To use, simply invoke the executable created by the installation.

```
ramldocgen generate SOURCE DESTINATION
```

For example:

```
ramldocgen generate api.raml api.html
```
