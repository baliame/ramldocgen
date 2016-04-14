# HTML documentation generator from RAML

A python implementation of generating a concise and easy to use documentation page from a RAML description of an API. This tool is heavily inspired by the node.js equivalent, https://github.com/raml2html/raml2html.

## Installation

The tool has been developed and tested with Python 3.5. It is not guaranteed to function with Python 2.7.

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
