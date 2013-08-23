While describing the differences between bpython and ipython with @graue (Scott),
I asserted that you couldn't keep normal scrollback with cool bpython
autocompletion, because curses. This is a proof of concept for why
he was right when he disagreed.

This repo is inactive, the code is being used for a bpython frontend.
For now, see
[my bpython
fork](https://bitbucket.org/thomasballinger/bpython/commits/branch/add-scroll-frontend),
but it'll hopefully soon be merged, and executable with an installation of
bpython with the command `bpython-scroll`.

Installation
------------

It's ready for people to start to use it a teensy bit!

* `git clone https://github.com/thomasballinger/scottwasright.git`
* `cd scottwasright`
* (these are suggested but optional virtualenv steps)
  * `virtualenv venv`
  * `source venv/bin/activate`
* `pip install -e . -r requirements.txt`

Things to do:
-------------

* integrate rest of functionality from bpython.repl.Repl
* feature complete with bpython.cli
