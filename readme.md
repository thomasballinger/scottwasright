While describing the differences between bpython and ipython with Scott,
I asserted that you couldn't keep normal scrollback with cool bpython
autocompletion, because curses. This is a proof of concept of why
he was right when he disagreed.

Hopefully this can be a bpython frontend in the short term

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

* add bpython-style tab completion
    * integrate import completion
    * fix filename completion
* fix window size changing (happens now, but screws up easily)
* fix rewind/undo behavior when scolls above top of screen - either disallow or
  break history
* integrate rest of functionality from bpython.repl.Repl
* feature complete with bpython.cli
* display library screen caching (rewrite only changing parts of terminal)
