# Porter

Opinionated Ivy protocol translator

Porter lifts Ivy protocols into a minimal AST intended for extraction to various
language backends. Porter performs minimal syntax transformation and so the AST
is reasonably Ivy-idiomatic; for a more opinionated translation mechanism,
consider [Irving](https://github.com/dijkstracula/irving).

## Setup

Porter uses Poetry for dependency management. Install it, then activate the virtual environment
in order to install its dependencies.

```
$ curl -sSL https://install.python-poetry.org | python3 -
$ poetry shell
(yesand-py3.11) $ poetry install
Updating dependencies
[...]
Installing the current project: porter (0.1.0)
(yesand-py3.11) $
```

Next, Install the python3 fork of Ivy. The `ms-ivy` package is not explicitly a dependency because we may wish to
either install a stock release of Ivy or use a version checked out from source.
Install it into your venv; if you need guidance doing
so, [follow this guide](https://www.cs.utexas.edu/~ntaylor/blog/ivy-venv-python3/).
(This may change now that Ivy has been officially ported to Python3.)

```
(porter-py3.11) $ python3 -q
>>> import ivy
>>> import ivy.z3
>>> ivy.z3.get_version()
(4, 7, 1, 0)
>>> ^D
```