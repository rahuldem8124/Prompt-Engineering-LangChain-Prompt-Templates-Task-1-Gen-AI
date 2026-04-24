import os
from markdown_pdf import MarkdownPdf, Section

def convert_to_pdf(md_filename, pdf_filename):
    if not os.path.exists(md_filename):
        print(f"Markdown file {md_filename} not found.")
        return
        
    print(f"Converting {md_filename} to {pdf_filename}...")
    try:
        with open(md_filename, 'r', encoding='utf-8') as f:
            content = f.read()

        pdf = MarkdownPdf(toc_level=2)
        pdf.add_section(Section(content))
        pdf.meta["title"] = pdf_filename.replace('.pdf', '').upper()
        pdf.save(pdf_filename)
        print(f"Successfully converted {md_filename} to {pdf_filename}.")
    except Exception as e:
        print(f"Failed to convert {md_filename}: {e}")

if __name__ == "__main__":
    files_to_convert = [
        ("hld.md", "HLD_Document.pdf"),
        ("lld.md", "LLD_Document.pdf"),
        ("tech_doc.md", "Technical_Documentation.pdf")
    ]
    
    for md_file, pdf_file in files_to_convert:
        convert_to_pdf(md_file, pdf_file)
