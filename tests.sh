#!/bin/bash

code_style=flake8

echo "Checking code style..."
$code_style announce/
$code_style remote/
$code_style game/
$code_style score/
$code_style util/
$code_style *.py

echo "Running Tests..."
python $(which nosetests) --with-coverage tests/*

echo "Final coverage report:"

coverage_report_options='-i --omit=tests/*,venv/*,venv2/*'
coverage html $coverage_report_options
coverage report $coverage_report_options
