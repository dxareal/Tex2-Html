import os
import re
import shutil

"""
Skript zum wandeln eines LaTeX-Skripts in ein CP (Course Package) für OLAT.

1. Aufteilen des Skripts in Oberkapitel, Kapitel, Sektionen und Untersektionen.

2. Struktur erstellen (???)
    Oberkapitel --> Ordner
    Kapitel --> Ordner (wird zu ZIP als CP)
    Sektion, Untersektion --> html
"""

input_path = "input"
output_path = "output"

class Tex2HTML():

    def __init__(self):
        self.filestructure = {}  # dictionary to store the categories and subcategories
        self.chapter_counter = 0
        self.img_section_counter = 1

    def run(self):
        """
        BASE
        """

        os.system("rm -r output")
        self.getFileStructure()
        print(self.filestructure)
        self.tex2html()
        self.generateManifest()
        self.setupImages()

    def getFileStructure(self):
        """
    Scannt das Hauptskript nach input- & part-Tags und speichert diese in einem Dictionary
    """

        pattern_part = r"\\part{([^{}]*)}"  # regular expression pattern to match "\part{...}"
        pattern_input = r"\\input{([^{}]*)}"  # regular expression pattern to match "\input{...}"

        with open(f"{input_path}/script.tex", "r", encoding="ISO-8859-1") as file:
            file_contents = file.readlines()
            scanning = False
            category = None
            for line in file_contents:
                if scanning:
                    if line.startswith("%"):  # ignore comments
                        continue
                    match_input = re.search(pattern_input, line)
                    if match_input:
                        input_file = match_input.group(1)
                        if category in self.filestructure:
                            self.filestructure[category].append(input_file)
                        else:
                            self.filestructure[category] = [input_file]
                    else:
                        match_part = re.search(pattern_part, line)
                        if match_part:
                            category = match_part.group(1)
                            self.filestructure[category] = []
                elif line.startswith("\\begin{document}"):
                    scanning = True

    def tex2html(self):
        """
    1. Erstellt Ordner für die jeweiligen Oberkapitel und Kapitel
    2. Teilt die Tex Dateien jeweils auf und speichert sie in der Zwischenablage (temp)
    """

        chapter_pattern = r'\\chapter\s*\{([^{}]*)\}'  # regular expression pattern to match "\chapter{...}"
        section_pattern = r'\\section\s*\{([^{}]*)\}'  # regular expression pattern to match "\section{...}"
        subsection_pattern = r'\\subsection\s*\{([^{}]*)\}'  # regular expression pattern to match "\subsection{...}"

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        course_counter = 1
        for course, topics in self.filestructure.items():
            if course is None:
                continue

            course = self.formatFilename(course)
            os.makedirs(f"{output_path}/{course_counter}_{course}")

            if topics is None:
                continue

            for topic in topics:
                filename = f"{input_path}/{topic}.tex"
                with open(filename, 'r', encoding='ISO-8859-1') as f:
                    file_content = f.readlines()

                    section_counter = 0
                    subsection_counter = 1
                    htmlbody = ""
                    title = ""
                    filepath = ""
                    semantic_struct_flag = False

                    for line in file_content:
                      last_filepath = filepath
                      last_title = title
                      if line.startswith("%"):  # ignore comments
                            continue
                      
                      if re.search(chapter_pattern, line):  # Kapitel gefunden --> Ordner erstellen
                          chapter_name = re.search(chapter_pattern, line).group(1)
                          chapter_name = self.formatFilename(chapter_name)
                          self.chapter_counter += 1
                          self.img_section_counter = 1
                          chapter_folder_path = os.path.join(f"{output_path}/{course_counter}_{course}/{self.chapter_counter}_{chapter_name}")
                          os.makedirs(chapter_folder_path)
                          with open(f"{chapter_folder_path}/style.css",'w', encoding='utf-8') as f:
                            f.write(self.getCSS())
                          
                          section_counter = 0
                      
                      elif re.search(section_pattern, line): # Section gefunden --> Html erstellen
                          section_name = re.search(section_pattern,line).group(1)
                          section_name = self.formatFilename(section_name)
                          section_counter += 1
                          filepath = f"{output_path}/{course_counter}_{course}/{self.chapter_counter}_{chapter_name}/{self.chapter_counter}_{section_counter}_0_{section_name}"
                          if last_filepath == '':
                              last_filepath = filepath
                              last_title = section_name
                          title = f"{section_counter}_{section_name}"
                          subsection_counter = 1
                      
                      elif re.search(subsection_pattern, line): # Subsection gefunden --> Html erstellen
                          subsection_name = re.search(subsection_pattern,line).group(1)
                          subsection_name = self.formatFilename(subsection_name)
                          filepath = f"{output_path}/{course_counter}_{course}/{self.chapter_counter}_{chapter_name}/{self.chapter_counter}_{section_counter}_{subsection_counter}_{subsection_name}"
                          title = f"{section_counter}_{subsection_counter}_{section_name}"
                          subsection_counter += 1
                      
                      if last_filepath != filepath:
                          self.writeHtml(filepath=last_filepath, title=last_title, htmlbody=htmlbody)
                          htmlbody = ""

                      # handle shaboxes START
                      if "\DEF{" in line:
                        line = "\n+++SEMANTIC-STRUCT-START+++ \{mathdef\}\n" + line
                        semantic_struct_flag = True
                      if "\SATZ{" in line:
                        line = "\n+++SEMANTIC-STRUCT-START+++ \{theorem\}\n" + line
                        semantic_struct_flag = True
                      if "\BEW{" in line:
                        line = "\n+++SEMANTIC-STRUCT-START+++ \{proof\}\n" + line
                        semantic_struct_flag = True

                      if semantic_struct_flag and line == "}\n":
                          line = line + "\n+++SEMANTIC-STRUCT-END+++\n\n" 
                          semantic_struct_flag = False
                      # handle shaboxes END

                      if "\SK" in line:
                          start_index = line.find('{') + 1
                          end_index = line.find('}')
                          img_alt = line[start_index:end_index]
                          img_alt = img_alt.replace('$', '')
                          line = line + "\n+++SKIZZE+++ \{" + img_alt + "\}\ \nn"

                      if re.search(r"\\ref\{.*?\}", line):
                          start_index = line.find('{') + 1
                          end_index = line.find('}')
                          ref = line[start_index:end_index]
                          line = re.sub(r"\\ref\{.*?\}", f"Kapitel: {ref}", line)

                      # htmlbody is first written into a tex file
                      htmlbody += line.replace('eqnarray*','align*').replace('&=&', '&=')

                    self.writeHtml(filepath=last_filepath, title=last_title, htmlbody=htmlbody)
                    htmlbody = ""
            course_counter += 1  # Ende des Oberkapitels

    def writeHtml(self, filepath, title, htmlbody):
        with open(f"{filepath}.tex", 'w', encoding='utf-8') as f:
          f.writelines("""
\\newcommand{\\DEF}[1]{
  \\begin{div}
    \\noindent\\textbf{Definition\\thedefinition: #1}
  \\end{div}
}
\\newcommand{\\SATZ}[1]{
\\begin{div}
\\noindent\\textbf{Satz:\\\\}
{#1}
\\end{div}
}
\\newcommand{\\BEW}[1]{
\\begin{div}
\\noindent\\textbf{Beweis:\\\\}
{#1}
\\end{div}
}
\\newcommand{\SK}[1]{
\\begin{div}
\\noindent\\textbf{#1\\\\}
\\end{div}
}
          """)
          f.write(f"{htmlbody}")

        # Latex -> Html
        os.system(f'pandoc -f latex -t html -o {filepath}.html {filepath}.tex --section-divs --mathjax')

        # Open the file for reading
        with open(f"{filepath}.html", "r") as input_file:
            # Read all the lines from the input file
            body = input_file.readlines()
        # Open the file for writing
        with open(f"{filepath}.html", "w", encoding='utf-8') as output_file:
            # Write only the lines that don't contain the "<p> <br />" pattern

            output_file.write(self.getBaseHtmlHead(title))

            for l in body:
                tmp = self.formatHtml(l)
                if tmp != "\n":
                    output_file.write(tmp)

            output_file.write(self.getBaseHtmlFoot())

            # remove .tex files
            os.system(f'rm {filepath}.tex') #TODO: COMMENT-IN in PRODUCTION

    def formatHtml(self, line):
        line = re.sub(r'id="beispiel(-\d+)?"', r'class="beispiel"', line)
        line = re.sub(r'id="hinweis(-\d+)?"', r'class="hinweis"', line)
        line = re.sub(r'id="definition(-\d+)?"', r'class="definition"', line)
        line = line.replace('max-width: 36em;', '').replace('padding-top: 50px;', '').replace('padding-bottom: 50px;', '')
        line = line.replace('\\[', '</br>$').replace('\\]', '$</br>')
        line = line.replace('\\)', '</br>$').replace('\\(', '$</br>') # Problem: Geklammerte Wörter.. zb 10_1_0 Anfang
        line = line.replace('&amp; \\approx &amp;', '&amp; \\approx').replace('&amp;\\approx &amp;', '&amp; \\approx').replace('&amp; =&amp', '&amp=').replace('&amp;  = &amp;', '&amp='); #TODO: use REGEX
        line = line.replace('\\R', '\\mathbb{R}').replace('\\Q', '\\mathbb{Q}').replace('\\C', '\\mathbb{C}').replace('\\I', '\\mathbb{I}').replace('\\I', '\\mathbb{N}').replace('\\Z', '\\mathbb{Z}').replace('\\M', '\\mathbb{M}')
        line = line.replace('<h5>Hinweis</h5>', '<h2>Hinweis:</h2>').replace('<h5>Beispiel</h5>', '<h2>Beispiel:</h2>').replace('<h5>Definition</h5>', '<h2>Definition</h2>')
        
        if "<p>\xa0<br />\n" in line or "<p>\u00A0<br />\n" in line:
            line = ""
        if "+++SEMANTIC-STRUCT-START+++" in line:
            start_index = line.find('{') + 1
            end_index = line.find('}')
            semantic_struct = line[start_index:end_index]
            line = f"<div class='{semantic_struct}'>"
        if "+++SEMANTIC-STRUCT-END+++" in line:
            line = "</div>"
        if "+++SKIZZE+++" in line:
            start_index = line.find('{') + 1
            end_index = line.find('}')
            img_alt = line[start_index:end_index]
            line = f"<img class='img_skizze' alt='{img_alt}' src='img/{self.chapter_counter}_{self.img_section_counter}.png'>"
            self.img_section_counter += 1
        return line
    
    def formatFilename(self, filename):
        filename = filename.replace("ü", "ue").replace("ä", "ae").replace("ö", "oe")
        filename = filename.replace("Ü", "Ue").replace("Ä", "Ae").replace("Ö", "Oe")
        filename = filename.replace("$", "").replace("/", "").replace(" ", "_").replace("\\", "").replace("\'", "")
        return filename

    def getBaseHtmlHead(self, title):
        return """
<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="utf8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <link href="style.css" rel="stylesheet" type="text/css" />
  <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/MathJax.js?config=TeX-MML-AM_CHTML"></script>
  <script>
    MathJax.Hub.Config({
      tex2jax: {
        inlineMath: [['$', '$']],
        displayMath: [['$$', '$$']],
        processEscapes: true,
        processEnvironments: true,
        processRefs: true,
        processTags: true,
        skipTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
      },
      TeX: {
        extensions: ['AMSmath.js', 'AMSsymbols.js'],
        Macros: {
        }
      }
    });
  </script>
  <title> """ + title + """</title>
</head>

<body>\n"""

    def getBaseHtmlFoot(self):
        return """
</body>

</html>
        """

    def getCSS(self):
        return """

        /* Style for body */
body {
  font-family: Arial, sans-serif;
  font-size: 18px;
  line-height: 1.5;
  margin: 0;
  padding: 20px;
  background-color: #f0f0f0;
}

/* Style for heading */
h1 {
  font-size: 32px;
  font-weight: bold;
  text-align: center;
  margin: 10px 0px 10px 0;
}

/* Style for sub-heading */
h2 {
  font-size: 24px;
  font-weight: bold;
  margin: 10px 0px 10px 0;
}

/* Style for section heading */
h3 {
  font-size: 20px;
  font-weight: bold;
  margin: 10px 0px 10px 0;
}

/* Style for text */
p {
  margin: 0 0 10px 0;
}

/* Style for math text */
.math.inline {
  font-style: italic;
  font-size: 18px;
}

/* Style for Boxes */
.mathdef, .theorem, .proof {
  background-color: #f8f9fa;
  padding: 10px;
  margin-bottom: 20px;
  box-shadow: 0px 3px 8px rgba(0, 0, 0, 0.2);
  border-radius: 5px;
}

.mathdef {
  border: 3px solid #2ecc71;
}

.theorem {
  border: 3px solid #34495e;
}

.proof {
  border: 3px solid #e74c3c;
}
        """

    def getManifest(self, items, resources): #TODO: extract title from script
      return """<?xml version="1.0" encoding="utf8" standalone="no" ?>

<!--
     Course: Angewandte Mathematik
     Author: Daniel de Sousa Areal
  Last edit: 25.03.2023
-->

<manifest identifier="hstrier" 
          version="1"
          xmlns="http://www.imsglobal.org/xsd/ims_cp_rootv1p1">
          <metadata>
    <schema>IMS Content</schema>
    <schemaversion>1.1</schemaversion>
  </metadata>
	<organizations default="hochschule_trier">
		<organization identifier="hs_trier">
        <title>Angewandte Mathematik</title>
        """ + items + """
   </organization>
	</organizations>
    <resources>
        """ + resources + """
    </resources>
</manifest>
        """
    
    def getManifestItem(self, counter, title):
        return """
          <item identifier='item_""" + str(counter) + """' identifierref='resource_""" + str(counter) + """'>
				<title>""" + title +"""</title>
			</item>
        """

    def getManifestResource(self, counter, filepath):
        return """
    <resource identifier='resource_""" + str(counter) + """' type="webcontent" href='""" + filepath + """'>
      <file href='""" + filepath + """'/>
		</resource>
        """

    def generateManifest(self):
      course_counter = 1
      for course, topics in self.filestructure.items():
        if course is None:
            continue

        # Get all files in the folder
        chapters = os.listdir(f"{output_path}/{course_counter}_{course}")
        for chapter in chapters:
          files = os.listdir(f"{output_path}/{course_counter}_{course}/{chapter}")
          counter = 1
          items = ""
          resources = ""
          # Filter the files to only include HTML files
          html_files = [f for f in files if f.endswith(".html")]
          html_files.sort()
          for html_file in html_files:
            items += self.getManifestItem(counter=counter, title=(html_file[6:-5].replace('_', ' ')))
            resources += self.getManifestResource(counter=counter, filepath=html_file)
            
            counter += 1
            pass
          with open(f"{output_path}/{course_counter}_{course}/{chapter}/imsmanifest.xml",'w', encoding='utf-8') as f:
            f.write(self.getManifest(items=items, resources=resources))

        course_counter +=1

    def setupImages(self):
      course_counter = 1
      for course, topics in self.filestructure.items():
        if course is None:
            continue

        # Get all files in the folder
        chapters = os.listdir(f"{output_path}/{course_counter}_{course}")
        chapters.sort()
        for chapter_counter, chapter in enumerate(chapters, start=1):
          os.makedirs(f"{output_path}/{course_counter}_{course}/{chapter}/img")
          img_files = os.listdir('img')
          for img_file in img_files:
              if re.match(fr"^{chapter_counter}_.+$", img_file):
                  shutil.copy(f"img/{img_file}", f"{output_path}/{course_counter}_{course}/{chapter}/img")
        course_counter += 1

tex = Tex2HTML()
tex.run()