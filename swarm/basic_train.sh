#!/usr/bin/env bash

TT_DIR=$HOME/TacTok

cd $TT_DIR/TacTok
python main.py --no_validation $@
