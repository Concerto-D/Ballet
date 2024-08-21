#!/bin/bash

# Initialize counters
python_lines=0
java_lines=0

# Recursively find all .py files and count lines
for file in $(find . -name '*.py'); do
    lines=$(wc -l < "$file")
    python_lines=$((python_lines + lines))
done

# Recursively find all .java files and count lines
for file in $(find . -name '*.java'); do
    lines=$(wc -l < "$file")
    java_lines=$((java_lines + lines))
done

total=$((python_lines+java_lines))

# Output the results
echo "Total lines of Python code: $python_lines"
echo "Total lines of Java code: $java_lines"
echo "TOTAL: $total"