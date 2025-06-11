#!/bin/bash
# Installing the dependencies

sudo apt-get install gcc g++ python python-dev qt4-dev-tools mercurial bzr cmake libc6-dev libc6-dev-i386 g++-multilib gdb valgrind gsl-bin libgsl0-dev libgsl0ldbl flex bison libfl-dev tcpdump sqlite sqlite3 libsqlite3-dev  libxml2 libxml2-dev  libgtk2.0-0 libgtk2.0-dev vtun lxc uncrustify doxygen graphviz imagemagick texlive-full python-sphinx dia python-pygraphviz python-kiwi python-pygoocanvas libgoocanvas-dev libboost-signals-dev libboost-filesystem-dev openmpi-bin openmpi-common openmpi-doc libopenmpi-dev mercurial bzr  texi2html python-pygccxml

#Get the ns3 installation packages

#Building the ns3 software

cd ns-allinone-3.25
./build.py --enable-examples --enable-tests




