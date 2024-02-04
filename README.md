# Porter

Lightweight Ivy protocol translator

Porter lifts Ivy protocols into a minimal AST intended for extraction to
various language backends. Porter performs minimal syntax transformation and so
the AST is reasonably Ivy-idiomatic; for a more opinionated translation
mechanism, consider [Irving](https://github.com/dijkstracula/irving).

## Setup

If you have not cloned with `--recurse-submodules`, be sure to run `git
submodule init` and `git submodule update` as the test suite requires
additional repositories.

### Python and Poetry

Porter requires python 3.11. Begin by installing it if you are using an older
version.

```
$ sudo apt-get install python3.11 # Ubuntu
$ brew install python3.11 #MacOS
```

Porter uses Poetry for dependency management. Install it, create your virtual
environment, and install Poetry dependencies into it.

```
$ curl -sSL https://install.python-poetry.org | python3 -
$ echo 'export PATH="/home/ntaylor/.local/bin:$PATH"' >> ~/.zshrc
$ source ~/.zshrc
$ which poetry         
/home/ntaylor/.local/bin/poetry
$ 
```

```
$ poetry env use python3.11
Creating virtualenv porter-WiUz2hvV-py3.11 in /home/ntaylor/.cache/pypoetry/virtualenvs
$ poetry install
Updating dependencies
[...]
Installing the current project: porter (0.1.0)
$
```

### IVy

Next, Install the python3 fork of Ivy.

The `ms-ivy` package is not explicitly a dependency because we may wish to
either install a stock release of Ivy or use a version checked out from source.

If you enjoy living on the edge and wish to do the latter: Building Ivy is a
two-step process: after cloning the repo with submodules, build its fork of Z3.
Then, ensuring that you have activated the poetry virtual environment, install
ivy (I do so in _develop_ mode, so as to have easy editing access to its source
code).

```
$ poetry shell
(porter-py3.11) $ pushd ~/code
(porter-py3.11) $ git clone https://github.com/kenmcmil/ivy.git --recurse-submodules
Cloning into 'ivy'...
...
Submodule 'submodules/z3' checked out
...
(porter-py3.11) $ python build_submodules.py
(porter-py3.11) $ python setup.py develop 
...
Finished installing dependencies for ms-ivy==1.8.25
(porter-py3.11) $
```

You may find that the submodule building script may not fully complete, but so
long as z3 builds you're good. Confirm that ivy and ivy's Z3 modules are
available to your virtualenv's Python.

```
(porter-py3.11) $ python3 -q
>>> import ivy
>>> import ivy.z3
>>> ivy.z3.get_version()
(4, 7, 1, 0)
>>> ^D
```

## Running

```
$ poetry run
```

## Development

High-level source architecture:

* `ast/`        : Well-typed IVy abstract syntax tree.
* `extraction/` : Ivy -> Java source conversion.
* `ivy/`        : Shim to Ken's IVy.  (All `ivy` imports should try to live in here.)
* `pp/`         : Wadler-style pretty-printer combinators.

Porter uses pytest for unit tests and pyright for typechecking.

```commandline
poetry run pytest
poetry run pyright
```

If any dependent submodules are updated, you will need to update your local
copy as well:

```commandline
git submodule update --remote --recursive
```


