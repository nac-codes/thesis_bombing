#!/bin/bash

echo "Combining markdown files..."

# Create a combined markdown file from revised files
cat revised/introduction.md > combined_thesis.md

cat revised/literature_review.md >> combined_thesis.md

cat revised/chapter_1.md >> combined_thesis.md

cat revised/chapter_2.md >> combined_thesis.md

cat revised/conclusion.md >> combined_thesis.md



echo "Updating links..."
python deploy/update_links.py combined_thesis.md

echo "Converting to PDF..."
pandoc combined_thesis.md \
    --from markdown \
    --pdf-engine=pdflatex \
    --template=deploy/template.tex \
    --toc \
    --number-sections \
    -V title="American Exceptionalism in War: Precision Bombing and the Defiance of Omnistate Theory" \
    -V author="Nicholas A. Chimicles" \
    -V date="\today" \
    -V geometry:margin=1in \
    --listings \
    --highlight-style=tango \
    -o thesis.pdf

echo "Thesis PDF successfully generated."