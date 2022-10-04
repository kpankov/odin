"""Random logo generator

Links:
- https://patorjk.com/software/taag/#p=display&f=Graffiti&t=onsemi

"""

# Std
from random import choice

logos = {}


def print_onsemi_logo(logger, random: bool = True):
    """Prints random or "original" logo

    Parameters
    ----------
    logger : Logger
        Logger object
    random : bool
        Turns on randomizer if True
    """
    if random:
        logger.bypass(choice(list(logos.values())))
    else:
        logger.bypass(logos["Speed"])


logos["Calvin_S"] = "\
┌─┐┌┬┐┬┌┐┌ ┌─┐┬ ┬\n\
│ │ ││││││ ├─┘└┬┘\n\
└─┘─┴┘┴┘└┘o┴   ┴ "

logos["Mini"] = "\
  _   _| o ._    .\n\
 (_) (_| | | | o |_) \/\n\
                 |   /"

logos["Speed"] = "\
      _____________\n\
____________  /__(_)______   _____________  __\n\
_  __ \  __  /__  /__  __ \  ___  __ \_  / / /\n\
/ /_/ / /_/ / _  / _  / / /____  /_/ /  /_/ /\n\
\____/\__,_/  /_/  /_/ /_/_(_)  .___/_\__, /\n\
                             /_/     /____/\n"
