While describing the differences between bpython and ipython with @graue (Scott),
I asserted that you couldn't keep normal scrollback with cool bpython
autocompletion, because curses. This is a proof of concept for why
he was right when he disagreed.

This repo is inactive, the code is being used for the bpython frontend [bpython-curtsies](https://bitbucket.org/bobf/bpython)
or install bpython and type `bpython-curtsies`.

Installation
------------

It's ready for people to start to use it a teensy bit!

* `git clone https://github.com/thomasballinger/scottwasright.git`
* `cd scottwasright`
* (these are suggested but optional virtualenv steps)
  * `virtualenv venv`
  * `source venv/bin/activate`
* `pip install -e . -r requirements.txt`

BUT the version of fmtstr this code needs doesn't exist anymore, so if one really wanted to run the code they'd need to check out a version of https://github.com/thomasballinger/curtsies old enough that it was still called fmtstr.
