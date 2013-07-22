While describing the differences between bpython and ipython with Scott,
I asserted that you couldn't keep normal scrollback with cool bpython
autocompletion, because curses. This is a proof of concept of why
he was right when he disagreed.

I'd like to create a bpython frontend that does this, or use it as
a ipython frontend, but right now just reimplementing features to
get a sense for how they're implemented in bpython.

Installation
------------

It's ready for people to start to use it a teensy bit!

* `git clone https://github.com/thomasballinger/scottwasright.git`
* `cd scottwasright`
* (these are optional suggested virtualenv step)
  * `virtualenv venv`
  * `source venv/bin/activate`
* `pip install -e . -r requirements.txt`


Things to do:

Terminal Wrapper Library
------------------------

* add bpython-style tab completion
    * inc. import completion
* fix window size changing (happens now, but screws up easily)
* fix rewind/undo behavior when scolls above top of screen - either disallow or
  break history
* integrate rest of functionality from bpython.repl
* display library screen caching (rewrite only changing parts of terminal)
