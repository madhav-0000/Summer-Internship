import pypandoc
import os

print("Downloading pandoc binaries...")
pypandoc.download_pandoc()

print("Converting Project_Report.md to Project_Report.docx...")
pypandoc.convert_file('Project_Report.md', 'docx', outputfile='Project_Report.docx')

print("Conversion complete! Check Project_Report.docx")
