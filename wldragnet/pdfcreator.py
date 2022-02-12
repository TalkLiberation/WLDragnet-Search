import codecs
import os
import re
import sys
from datetime import date
from io import BytesIO

from flask import render_template_string

# Workaround to load packages that for some reason are not added to sys.path
libpath = '../venv/lib/python3.9/site-packages'
if libpath not in sys.path:
    sys.path.append(libpath)
import pdfkit
import PyPDF2

pdfkit_config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')

# commandline options set for the execution of wkhtmltopdf
options = {
    'page-size': 'A4',
    'margin-top': '9mm',
    'margin-bottom': '9mm',
    'orientation': 'Portrait',
    'encoding': 'UTF-8',
    'print-media-type': None,
    'enable-local-file-access': None,
}

# Pattern for css url rules
pattern = re.compile(r"(url\(\'([^'#?]+)(\??#[^']+)?\'\))")
css_files = [
    'wldragnet/templates/report/assets/css/style.css',
    'wldragnet/templates/report/assets/css/print.css',
    'wldragnet/templates/report/assets/css/font.css'
]

base_path = os.getcwd()


def rewrite_css(file_path):
    """
    CSS rules with url(\' ..\') in them require absolute paths for the wkhtmltopdf library to find them.
    This function scans given css files and replaces those relative urls with absolute paths,
    then returns the css file as a string

    :param file_path: path to a css file relative to the app root directory
    :return: the fixed css as a string
    """
    """"""

    file_path_folder = os.path.join(base_path, os.path.split(file_path)[0])

    def generate_url_rule(match):
        """
        Function to generate a css url statement from a regex match
        :param match: the match caught by a regex
        :return: the css url statement as a string
        """
        result = 'url(\''
        result += os.path.join(file_path_folder, match.group(2))
        if match.group(3) is not None:
            result += match.group(3)
        result += '\')'
        return result

    with codecs.open(file_path, encoding="UTF-8") as file_handle:
        return pattern.sub(generate_url_rule, file_handle.read())


# Generate CSS block
css_data = []
for file in css_files:
    fixed_css = rewrite_css(file)
    css_data.append(fixed_css)
css_data = "\n".join(css_data)

# Load the report template as a string
with codecs.open('wldragnet/templates/report/report.html', encoding="UTF-8") as f:
    template = f.read()

# Inject CSS block
template = template.replace('</head>', '<style>' + css_data + '</style></head>')


def generate_report(query, results, out):
    """
    This function generates a pdf report for a queried userhandle and writes it to the out stream

    :param query: the query that has been searched for
    :param results: the results returned for the query
    :param out: the out stream to write the generated pdf to
    """
    pdf_writer = PyPDF2.PdfFileWriter()

    front_cover_file = open('wldragnet/templates/report/pdf-cover/front-cover-and-intro.pdf', 'rb')
    front_cover_reader = PyPDF2.PdfFileReader(front_cover_file)

    # We have to write each page sepparately to the pdf writer
    for page_num in range(front_cover_reader.numPages):
        page = front_cover_reader.getPage(page_num)
        pdf_writer.addPage(page)

    timestamp = date.today().strftime('%d %b %Y')
    report = pdfkit.from_string(
        render_template_string(template, query=query, results=results, timestamp=timestamp),
        False,
        options=options,
        configuration=pdfkit_config,
    )

    report_stream = BytesIO(report)
    # PyPDF2 requires a stream
    report_reader = PyPDF2.PdfFileReader(report_stream)

    for page_num in range(report_reader.numPages):
        page = report_reader.getPage(page_num)
        pdf_writer.addPage(page)

    back_cover_file = open('wldragnet/templates/report/pdf-cover/back-cover.pdf', 'rb')
    back_cover_reader = PyPDF2.PdfFileReader(back_cover_file)

    for page_num in range(back_cover_reader.numPages):
        page = back_cover_reader.getPage(page_num)
        pdf_writer.addPage(page)

    pdf_writer.write(out)

    back_cover_file.close()
    report_stream.close()
    front_cover_file.close()
