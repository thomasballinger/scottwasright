While describing the differences between bpython and ipython with Scott,
I asserted that you couldn't keep normal scrollback with cool bpython
autocompletion, because curses. This is a proof of concept of why
he was right when he disagreed.

I'd like to create a bpython frontend that does this, or use it as
a ipython frontend, but right now just reimplementing features to
get a sense for how they're implemented in bpython.

Things to do:

* colored everything
* tab completion of all kinds
* useful infobox
* control c working (maybe need to use cbreak mode instead of raw?) Or a thread
    to check back to see if cdoe.interpreter should be interrupted?
* history readline commands
* window resizing (probably not resizing prior output though)
