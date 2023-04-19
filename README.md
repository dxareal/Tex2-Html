# Tex2-Html

This script converts a LaTeX script into several CP (Course Package) modules so that they can be integrated into OLAT vcrp.
Mathematical formulas are supported and formated with the help of MathJax.
  

## Description

### Basic
The program automatically sections the script into its chapters, sections and subsections.
Afterwards it formats the sectioned LaTeX files and converts it to HTML using Pandoc.
Then it generates a style.css and manifest.xml file in every Course Package.
In the end, the respective folders are zipped to fit the CP specifications.
They are outputted in the specified folder on the top of the script.

Default values are:
(Top Level folders, same height as the src folder)
- input folder (containing the main script and it's dependencies): /input
- output folder (containing the zipped CP, ready for upload): /output
- tmp folder (containing the temporary results): /tmp

### Sketches
If images for the sketches inside the script are provided, they shall be numbered with the section number and sketch number, like: *1_2.png*
This refers to the second Sketch in the first section.
To debug any problems, the  Browser 'developer tools' may help ton identify the resource name needed.

Make sure, to use the format png, otherwise this has to be changed in code.

If the Debug flag is set to true, it will wont delete the .tex files in the folders and it also wont delete the tmp folder, where the interim results are stored. 
  

## Getting Started


### Dependencies
This Script has been developed and tested on Linux.

* pandoc
* shutil
  

### Installing

The repository is private, but can be accessible via permissions.
```bash
git clone git@github.com:IBerryX/Tex2-Html.git
```

Pandoc is the tool used to convert the LaTeX script into HTML files.
To install pandoc run:
```sh
sudo apt install pandoc
```


### Executing program

Before executing the program, make sure to check the input and output path.
The input path should contain the main scripts and all the dependencies.

* to run the file use the following command

```sh
python3 src/main.py
```

## Help
If any problems are encountered, make sure to contact the author: daniel99areal@gmail.com

## To-Do

- [ ] extract title from LaTeX Script (for now the title has to be manually changed, since it's hardcoded)
- [ ] support various image types / let the user specify which type to take via CLI flag
- [ ] CLI support for taking arguments like output and input path, aswell as the image folder
- [ ] Fix Problems when converting to HTML, like some Math Symbols not being recognized
- [ ] The end of a Chapter contains some part of the next Chapter about to begin (this is only a copy)
- [ ] GUI support maybe with more options
