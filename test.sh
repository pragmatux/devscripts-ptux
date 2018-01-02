#!/bin/sh
# Run all unit tests

(cd src && python -m unittest discover)
(cd src-ptuxrepo && python -m unittest discover)
