echo "Combining markdown files..."

# Create a combined markdown file
cat preface.md > combined_thesis.md
cat "\n\n" >> combined_thesis.md
cat introduction.md >> combined_thesis.md
echo "\n\n" >> combined_thesis.md
cat lit_review.md >> combined_thesis.md
echo "\n\n" >> combined_thesis.md
cat chapter_1.md >> combined_thesis.md
echo "\n\n" >> combined_thesis.md
# Add the appendices
# cat methodology_attack_data.md >> combined_thesis.md
# echo "\n\n" >> combined_thesis.md
# cat results_attack_data.md >> combined_thesis.md
# echo "\n\n" >> combined_thesis.md
cat bibliography.md >> combined_thesis.md

echo "Updating links..."
python deploy/update_links.py combined_thesis.md

echo "Converting to PDF..."
pandoc combined_thesis.md \
    --from markdown \
    --pdf-engine=pdflatex \
    --template=deploy/template.tex \
    --toc \
    --number-sections \
    -V title="Strategic Bombing in World War II: A Data-Driven Analysis" \
    -V author="Nicholas A. Chimicles" \
    -V date="\today" \
    -V geometry:margin=1in \
    --listings \
    --highlight-style=tango \
    -o thesis.pdf