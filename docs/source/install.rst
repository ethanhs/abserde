.. _installing:

Installing abserde
==================

To install abserde, first install the latest nightly Rust via `rustup`_ and poetry via :code:`pip`. Then clone
the repository and install it!

.. code-block::

    $ curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
      ... rust installs. Make sure to install the latest nightly for your platform! ...
    $ curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
      ... poetry installs ...
    $ git clone https://github.com/ethanhs/abserde.git && cd abserde
      ... cloning etc ...
    $ python -m pip install .
      ... install abserde ...
    $ abserde --help
      ... help output here...


.. _`rustup`: https://rustup.rs/
