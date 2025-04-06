#!/bin/bash

echo "Combining markdown files..."

# Create a combined markdown file from revised files
cat acknowledgements.md > combined_thesis.md

cat buffer.md >> combined_thesis.md

cat preface.md >> combined_thesis.md

cat buffer.md >> combined_thesis.md

cat introduction.md >> combined_thesis.md

cat buffer.md >> combined_thesis.md

cat literature_review.md >> combined_thesis.md

cat buffer.md >> combined_thesis.md

cat chapter_1.md >> combined_thesis.md

cat buffer.md >> combined_thesis.md

cat chapter_2.md >> combined_thesis.md

cat buffer.md >> combined_thesis.md

cat conclusion.md >> combined_thesis.md

cat buffer.md >> combined_thesis.md

cat bibliography.md >> combined_thesis.md

cat buffer.md >> combined_thesis.md

cat methodology_attack_data.md >> combined_thesis.md

cat buffer.md >> combined_thesis.md

cat results_attack_data.md >> combined_thesis.md


echo "Updating links..."
python deploy/update_links.py combined_thesis.md

echo "Updating footnotes..."
python renumber_footnotes.py combined_thesis.md

echo "Converting to PDF..."
pandoc combined_thesis.md \
    --from markdown \
    --pdf-engine=pdflatex \
    --template=deploy/template.tex \
    --toc \
    --number-sections \
    -V title="American Exceptionalism in War: Precision Bombing and Resisting the Temptation of Total War" \
    -V author="Nicholas A. Chimicles" \
    -V date="\today" \
    -V geometry:margin=1in \
    --listings \
    --highlight-style=tango \
    -o thesis.pdf

echo "Thesis PDF successfully generated."