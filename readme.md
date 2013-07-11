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

* Context manager for putting stdin in raw mode
* Library for symbolically processing input into keys
* get_event function that blocks, returning window change events, keypresses
* screen output library that renders a rectangle of characters to the screen
* fix window size changing (happens now, but screws up easily)


Paint Layer
-----------

* window resizing (probably not resizing prior output though)
* nice api for painting characters different places
