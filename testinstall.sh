#!/usr/bin/env bash
cd /tmp
rm -rf scottwasright_test_install
mkdir scottwasright_test_install
cd scottwasright_test_install
git clone scottwasright
cd scottwasright
virtualenv venv
source venv/bin/activate
