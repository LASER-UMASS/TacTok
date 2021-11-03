#!/usr/bin/env bash

sed -i "s/TT_DIR=.*/TT_DIR=$1/" swarm/*.sh
