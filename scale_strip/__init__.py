"""Focusing scale strip generator for the Bronica S2 helicoid.

The package separates one abstract model from two renderers. ``build_model``
turns a unit and focal lengths into a ``StripModel`` in millimeters; the PDF and
DXF renderers consume that model. The command line and the website share both.
"""
