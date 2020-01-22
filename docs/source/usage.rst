Using abserde
=============

Before using abserde, make sure it is installed (see :ref:`installing` if you haven't yet).

You can pass :code:`--debug` if you want to check that abserde will compile the stub you
provided. The output wheel can be found in :code:`dist/`.

.. code-block::

    $ abserde --debug my_input.pyi

Once you are happy with the results, you can run without :code:`--debug` to build a fully optimized
release wheel.

.. code-block::

    $ abserde my_input.pyi


Abserde creates a Rust crate, which you can change the author name and email for via the
:code:`--name` and :code:`--email` flags.

.. code-block::

    $ abserde --name "King Arthur" --email king.arthur@lancelot.email my_input.pyi
