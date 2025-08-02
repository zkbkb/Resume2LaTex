#!/usr/bin/env python3
"""
resume2latex - Convert JSON resume to LaTeX format
"""

import json
import sys
import re
import argparse
import os
import platform
import subprocess
import tempfile
import shutil
from pathlib import Path

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def escape_latex(text):
    """Escape LaTeX special characters in text"""
    if not text:
        return ""
    
    # Note: order matters for backslash
    text = text.replace('\\', '\\\\')  # Escape backslashes first
    text = text.replace('&', '\\&')
    text = text.replace('%', '\\%')
    text = text.replace('$', '\\$')
    text = text.replace('#', '\\#')
    text = text.replace('_', '\\_')
    text = text.replace('{', '\\{')
    text = text.replace('}', '\\}')
    text = text.replace('~', '\\textasciitilde{}')
    text = text.replace('^', '\\textasciicircum{}')
    
    return text

def get_single_char_input():
    """Get a line of input from the user and return it as a stripped, lowercase string."""
    try:
        return input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        return "n"  # Default to no if input is not available

def validate_file_path(file_path):
    """Validate file path for security"""
    if not file_path or not isinstance(file_path, str):
        return False
    
    # Check for path traversal attempts
    if '..' in file_path:
        return False
    
    # Allow absolute paths only if they're in the current directory or subdirectories
    if os.path.isabs(file_path):
        # Get current working directory
        current_dir = os.getcwd()
        # Check if the file path is within the current directory
        try:
            # Resolve the absolute path
            abs_path = os.path.abspath(file_path)
            # Check if it's within current directory
            if not abs_path.startswith(current_dir):
                return False
        except (OSError, ValueError):
            return False
    
    # Check for potentially dangerous characters
    dangerous_chars = [';', '|', '&', '`', '$', '(', ')', '{', '}', '[', ']', '"', "'"]
    if any(char in file_path for char in dangerous_chars):
        return False
    
    return True

def safe_subprocess_run(cmd, **kwargs):
    """Safely run subprocess with validation"""
    if not isinstance(cmd, list) or not cmd:
        raise ValueError("Command must be a non-empty list")
    
    # Validate each command argument
    for arg in cmd:
        if not isinstance(arg, str) or not arg.strip():
            raise ValueError("Command arguments must be non-empty strings")
    
    # Only allow specific safe commands
    safe_commands = {
        'brew', 'apt-get', 'yum', 'which', 'pdflatex', 'latexmk',
        'python3', 'pip', 'curl', 'wget'
    }
    
    # Check the base name of the command against the safe list
    if os.path.basename(cmd[0]) not in safe_commands:
        raise ValueError(f"Command '{cmd[0]}' is not in the allowed list")
    
    return subprocess.run(cmd, **kwargs)

def generate_output_filename(resume_data):
    """Generate output filename based on name"""
    # Get name from resume data, clean it for filename
    name = resume_data['personal_info']['name']
    # Replace spaces with hyphens and other special characters with underscores
    clean_name = name.replace(' ', '-')
    clean_name = re.sub(r'[^a-zA-Z0-9\-]', '_', clean_name).strip('_')

    # Generate filename: YOUR-NAME_resume.tex
    filename = f"{clean_name}_resume.tex"

    return filename

# =============================================================================
# FILE OPERATIONS
# =============================================================================

def load_resume_data(json_file):
    """Load resume data from JSON file"""
    if not validate_file_path(json_file):
        print(f"Error: Invalid file path: {json_file}")
        sys.exit(1)
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_file} not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {json_file}: {e}")
        sys.exit(1)

# =============================================================================
# LATEX GENERATION
# =============================================================================

def generate_latex_header():
    """Generate LaTeX document header"""
    return r"""\documentclass[letterpaper,11pt]{article}

%---------- PACKAGES ----------
\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{textcomp}  % Alternative to marvosym for symbols
\usepackage[usenames,dvipsnames]{color}
\usepackage{times}    % main text in Times New Roman
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\usepackage{hyphenat}

%---------- PAGE SETUP ----------
\pagestyle{fancy}
\fancyhf{} % clear all header and footer fields
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins
\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

%---------- SECTION FORMATTING ----------
\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

% Ensure that generate pdf is machine readable/ATS parsable
\pdfgentounicode=1

%---------- CUSTOM COMMANDS ----------

% Basic item command
\newcommand{\resumeItem}[1]{
  \item \small{ #1 }
}

% Subheading with 4 parameters: company, location, position, date
\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      {\small #3} & {\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

% Sub-subheading with 2 parameters: title, date
\newcommand{\resumeSubSubheading}[2]{
    \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      {\small #1} & {\small #2} \\
    \end{tabular*}\vspace{-7pt}
}

% Education heading with 4 parameters: university, location, degree, date
\newcommand{\resumeEducationHeading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      {\small #3} & {\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

% Project heading with 2 parameters: project name, date
\newcommand{\resumeProjectHeading}[2]{
    \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-7pt}
}

% Organization heading with 4 parameters: company, date, position, location
\newcommand{\resumeOrganizationHeading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & \textit{\small #2} \\
      \textit{\small#3}
    \end{tabular*}\vspace{-7pt}
}

% Sub-item with extra spacing
\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}

% List environment commands
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}[leftmargin=*, itemsep=2pt, label=\textbullet]}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

%-------------------------------------------
%%%%%%  RESUME STARTS HERE  %%%%%%%%%%%%%%%%%%%%%%%%%%%

\begin{document}

%---------- HEADING ----------
"""

def generate_heading(personal_info):
    """Generate the heading section"""
    name = escape_latex(personal_info['name'])
    phone = escape_latex(personal_info['phone'])
    email = escape_latex(personal_info['email'])
    location = escape_latex(personal_info['location'])
    website = escape_latex(personal_info['website'])

    return f"""%---------- HEADING ----------
\\begin{{center}}
    \\textbf{{\\Huge \\scshape {name}}} \\\\ \\vspace{{3pt}}
    \\small
    {phone} $|$ {email} $|$ {location} $|$ {website}
\\end{{center}}

"""

def generate_education(education):
    """Generate the education section"""
    institution = escape_latex(education['institution'])
    location = escape_latex(education['location'])
    degree = escape_latex(education['degree'])
    period = escape_latex(education['period'])
    core_modules = escape_latex(', '.join(education['details']['core_modules']))
    grade = escape_latex(education['details']['grade'])

    latex = f"""%---------- EDUCATION -----------
\\section{{EDUCATION}}
  \\vspace{{3pt}}
  \\resumeSubHeadingListStart

    \\resumeEducationHeading
      {{{institution}}}{{{location}}}
      {{{degree}}}{{{period}}}

        \\resumeItemListStart
            \\resumeItem{{Core Modules: {core_modules}}}
            \\resumeItem{{Grade: {grade}}}
        \\resumeItemListEnd

  \\resumeSubHeadingListEnd

"""
    return latex

def generate_professional_experience(experiences):
    """Generate the professional experience section"""
    latex = """%---------- PROFESSIONAL EXPERIENCE -----------
\\section{PROFESSIONAL EXPERIENCE}
  \\vspace{3pt}
  \\resumeSubHeadingListStart

"""

    for exp in experiences:
        company = escape_latex(exp['company'])
        location = escape_latex(exp['location'])
        position = escape_latex(exp['position'])
        period = escape_latex(exp['period'])

        latex += f"""    \\resumeSubheading
      {{{company}}}{{{location}}}
      {{{position}}}{{{period}}}"""

        if exp['description']:
            latex += "\n        \\resumeItemListStart\n"
            for description in exp['description']:
                description_escaped = escape_latex(description)
                latex += f"            \\resumeItem{{{description_escaped}}}\n"
            latex += "        \\resumeItemListEnd\n"
        else:
            latex += "\n"

    latex += "  \\resumeSubHeadingListEnd\n\n"
    return latex

def generate_project_experience(projects):
    """Generate the project experience section"""
    latex = """%---------- PROJECT EXPERIENCE -----------
\\section{PROJECT EXPERIENCE}
    \\vspace{3pt}
    \\resumeSubHeadingListStart

"""

    for project in projects:
        name = escape_latex(project['name'])
        period = escape_latex(project['period'])

        latex += f"""      \\resumeProjectHeading
        {{\\textbf{{{name}}}}}{{{period}}}"""

        if 'description' in project:
            latex += "\n          \\resumeItemListStart\n"
            for description in project['description']:
                description_escaped = escape_latex(description)
                latex += f"            \\resumeItem{{{description_escaped}}}\n"
            latex += "          \\resumeItemListEnd\n"
        else:
            latex += "\n"

    latex += "    \\resumeSubHeadingListEnd\n\n"
    return latex

def generate_additional_information(additional_info):
    """Generate the additional information section"""
    languages = additional_info['languages']
    skills = additional_info['skills']

    languages_str = ", ".join([f"{lang['language']} ({lang['proficiency']})" for lang in languages])
    skills_str = ", ".join(skills)

    # Escape special characters
    languages_str = escape_latex(languages_str)
    skills_str = escape_latex(skills_str)

    return f"""%---------- ADDITIONAL INFORMATION -----------
\\section{{ADDITIONAL INFORMATION}}
  \\vspace{{2pt}}
  \\resumeSubHeadingListStart
    \\small{{\\item{{
        \\textbf{{Languages:}} {languages_str} \\\\ \\vspace{{3pt}}

        \\textbf{{Skills:}} {skills_str} \\\\ \\vspace{{3pt}}
    }}}}
  \\resumeSubHeadingListEnd

"""

def generate_latex_footer():
    """Generate LaTeX document footer"""
    return """%-------------------------------------------
\\end{document}
"""

def generate_resume_latex(resume_data):
    """Generate complete LaTeX resume from JSON data"""
    latex_content = ""

    # Header
    latex_content += generate_latex_header()

    # Heading
    latex_content += generate_heading(resume_data['personal_info'])

    # Education
    latex_content += generate_education(resume_data['education'])

    # Professional Experience
    latex_content += generate_professional_experience(resume_data['professional_experience'])

    # Project Experience
    latex_content += generate_project_experience(resume_data['project_experience'])

    # Additional Information
    latex_content += generate_additional_information(resume_data['additional_information'])

    # Footer
    latex_content += generate_latex_footer()

    return latex_content

# =============================================================================
# VALIDATION
# =============================================================================

def validate_latex_syntax(filename):
    """Validate LaTeX syntax in the generated file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"Validating {filename}...")
        print("=" * 50)

        issues = []

        # Check for unescaped special characters in content (not comments)
        # Remove LaTeX comments first
        content_no_comments = re.sub(r'%.*$', '', content, flags=re.MULTILINE)
        unescaped_percent = re.findall(r'(?<!\\)%', content_no_comments)
        if unescaped_percent:
            issues.append(f"Found {len(unescaped_percent)} unescaped percent signs (%) in content")

        # Check for unescaped ampersands only in content after \begin{document}
        doc_start = content.find('\\begin{document}')
        if doc_start != -1:
            content_after_doc = content[doc_start:]
            unescaped_ampersand = re.findall(r'(?<!\\)&(?!\w)', content_after_doc)
            if unescaped_ampersand:
                issues.append(f"Found {len(unescaped_ampersand)} unescaped ampersands (&) in content")

        # Check for balanced braces
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            issues.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")

        # Check for required elements
        required = [
            '\\documentclass',
            '\\begin{document}',
            '\\end{document}'
        ]

        missing = []
        for req in required:
            if req not in content:
                missing.append(req)

        if missing:
            issues.append(f"Missing required elements: {missing}")

        # Report results
        if not issues:
            print("No syntax issues found!")
            print("LaTeX file appears to be valid")
            return True
        else:
            print("Found the following issues:")
            for issue in issues:
                print(f"  - {issue}")
            return False

    except Exception as e:
        print(f"Error reading file: {e}")
        return False

# =============================================================================
# TEMPLATE GENERATION
# =============================================================================

def generate_readme_content():
    """Generate README.md content"""
    return """# Resume2LaTeX - Generate Formatted Resume in LaTeX

A python script that generates a formatted resume from structured JSON data to a formatted resume page in LaTeX format, with optional PDF compilation.

## Files

- `resume2latex.py` - Main Python script for resume generation and validation
- `resume_template.json` - Template JSON file for creating your resume data

## Usage

### 1. Create a new template JSON file to fill in

```bash
python3 resume2latex.py -t
# or
python3 resume2latex.py --template
```

This will generate a `resume_template.json` file with example data that you can edit.

### 2. Generate resume from your JSON file

```bash
python3 resume2latex.py resume.json
```

### 3. Compile LaTeX file to PDF

```bash
python3 resume2latex.py resume.tex -p
```

### 4. Generate and compile JSON to PDF

```bash
python3 resume2latex.py resume.json -p
```

### 5. More options

```bash
# Show help
python3 resume2latex.py -h

# Validate the generated LaTeX file
python3 resume2latex.py resume.json -v

# Only check existing LaTeX file without generating new one
python3 resume2latex.py file.tex -c

# Specify custom output filename
python3 resume2latex.py resume.json -o my_resume.tex
```

## Auto-generated Filename

The script automatically generates output filenames based on the name in your JSON data:

- Input: `"John Doe"` → Output: `John-Doe_resume.tex`
- Input: `"Mary Jane Smith"` → Output: `Mary-Jane-Smith_resume.tex`

Spaces in names are automatically converted to hyphens for the filename.

## JSON Data Structure

The JSON file should contain the following structure:

```json
{
    "personal_info": {
        "name": "Your Full Name (e.g., John Doe)",
        "phone": "+44 7123 456789",
        "email": "your.email@example.com",
        "location": "City, Country",
        "website": "your-website.com"
    },
    "education": {
        "institution": "University Name (e.g., University College London)",
        "location": "City, Country",
        "degree": "Your Degree",
        "period": "Start Date -- End Date",
        "details": {
            "core_modules": [
                "Module 1",
                "Module 2",
                "Module 3",
                "Module 4",
                "Course Module 5 (or just leave blank)"
            ],
            "grade": "Your Grade"
        }
    },
    "professional_experience": [
        {
            "company": "Company Name",
            "location": "City, Country",
            "position": "Job Title",
            "period": "Start Date -- End Date",
            "description": [
                "Description 1",
                "Description 2",
                "Description 3"
            ]
        }
    ],
    "project_experience": [
        {
            "name": "Project Name",
            "period": "Start Date -- End Date",
            "description": [
                "Description 1",
                "Description 2",
                "Description 3"
            ]
        }
    ],
    "additional_information": {
        "languages": [
            {
                "language": "Language Name",
                "proficiency": "Proficiency Level"
            }
        ],
        "skills": [
            "Skill 1",
            "Skill 2",
            "Skill 3"
        ]
    }
}
```

## Template Usage

1. Run `python3 resume2latex.py -t` to generate the template
2. Edit `resume_template.json` with your information
3. Run `python3 resume2latex.py resume_template.json` to generate your resume in LaTeX format
4. Use `python3 resume2latex.py resume_template.json -p` to generate both LaTeX and PDF files
5. The generated LaTeX file can also be compiled manually with any LaTeX compiler

## PDF Compilation

The script includes built-in PDF compilation functionality:

- **Built-in pdflatex Compiler**: Uses pdflatex for LaTeX to PDF compilation
- **Automatic LaTeX Detection**: Automatically finds installed pdflatex in common locations
- **Automatic Installation**: Offers to install LaTeX distribution if pdflatex is not found
- **Clean Output**: Automatically removes temporary LaTeX files, keeping only the PDF
- **Error Handling**: Provides detailed error messages for compilation issues
- **Cross-platform Support**: Works on macOS, Linux, and Windows

### LaTeX Installation

If pdflatex is not found, the script will automatically offer to install a LaTeX distribution:

- **macOS**: Automatically installs basictex via Homebrew
- **Ubuntu/Debian**: Automatically installs texlive-full via apt-get
- **Windows**: Provides manual installation instructions for MiKTeX

The script will detect your operating system and package manager, then install the appropriate LaTeX distribution that includes pdflatex.

## Features

- **Auto-filename Generation**: Creates filenames based on your name
- **LaTeX Validation**: Built-in validation to check for syntax errors
- **PDF Compilation**: Built-in pdflatex compiler with automatic LaTeX detection and installation
- **Template Generation**: Creates ready-to-use JSON templates with examples

## Error Handling

If you run the script without arguments, it will display:
```
ERROR: Either a Input file (JSON or LaTeX) or a specified command flag is required.
Usage: python3 resume2latex.py <input_file> [options]

Need help? (y/n)
```

Responding with 'y' will show detailed help information.

## Notes

```mermaid
flowchart TB
    %% Actors
    User(["User / Developer"]):::actor

    %% Script Modules Subgraph
    subgraph "Resume2LaTeX Script"
        direction TB
        CLIParser["CLI Parser"]:::internal
        TemplateGen["Template Generator"]:::internal
        JSONParser["JSON Parser / Validator"]:::internal
        Formatter["LaTeX Formatter"]:::internal
        FilenameGen["Filename Generator"]:::internal
        Validator["LaTeX Syntax Validator"]:::internal
        PDFCompiler["PDF Compiler"]:::internal
        LaTeXInstaller["LaTeX Installer"]:::internal
    end

    %% File System Data Stores
    subgraph "File System"
        direction TB
        TemplateFile[("resume_template.json")]:::datastore
        InputExample[("sample.json")]:::datastore
        OutputExample[("sample.tex")]:::datastore
        README[("README.md")]:::datastore
        LICENSE[("LICENSE")]:::datastore
    end

    %% External Dependency
    ExternalCompiler(["LaTeX Compiler"]):::external

    %% Flows
    User --> CLIParser
    CLIParser -->|"--template"| TemplateGen
    TemplateGen --> TemplateFile
    TemplateGen -->|"console output"| User

    CLIParser -->|".json input"| JSONParser
    JSONParser --> Formatter
    Formatter --> FilenameGen
    FilenameGen --> OutputExample
    FilenameGen -->|"console output"| User
    FilenameGen --> Validator
    Validator --> ExternalCompiler
    ExternalCompiler --> Validator
    Validator -->|"validation status"| User

    CLIParser -->|"--check .tex"| Validator
    CLIParser -->|"--pdf .tex"| PDFCompiler
    CLIParser -->|"--pdf .json"| Formatter
    Formatter --> PDFCompiler
    PDFCompiler --> LaTeXInstaller
    LaTeXInstaller --> PDFCompiler
    PDFCompiler --> ExternalCompiler

    %% Example files as optional input/output
    User --> InputExample
    User --> OutputExample

    %% Styles
    classDef actor fill:#f9f,stroke:#333,stroke-width:2px,shape:ellipse
    classDef internal fill:#bbf,stroke:#333,stroke-width:1px
    classDef datastore fill:#bfb,stroke:#333,stroke-width:1px,shape:cylinder
    classDef external fill:#ffb,stroke:#333,stroke-width:1px,shape:hexagon
```

- The script automatically escapes LaTeX special characters (`{`, `}`, `&`, `%`)
- All output messages are in plain text (no emojis)
- The generated LaTeX file follows a clean, professional format
- Template includes detailed examples to guide users
"""

def create_template():
    """Create a new resume template file"""
    template_content = {
        "personal_info": {
            "name": "John Doe",
            "phone": "+44 7123 456789",
            "email": "your.email@example.com",
            "location": "City, Country",
            "website": "your-website.com"
        },
        "education": {
            "institution": "University Name (e.g., University College London)",
            "location": "City, Country",
            "degree": "Degree Type (e.g., B.S. Computer Science)",
            "period": "Start Date -- End Date (e.g., Sept. 2020 -- June 2024)",
            "details": {
                "core_modules": [
                    "Course Module 1 (e.g., Data Structures and Algorithms)",
                    "Course Module 2 (e.g., Database Systems)",
                    "Course Module 3 (e.g., Software Engineering)",
                    "Course Module 4 (e.g., Machine Learning)",
                    "Course Module 5 (or just leave blank)"
                ],
                "grade": "Expected Grade (e.g., First Class, 3.8 GPA)"
            }
        },
        "professional_experience": [
            {
                "company": "Company Name 1 (e.g., Google Inc.)",
                "location": "City, Country (e.g., Mountain View, CA, USA)",
                "position": "Job Title (e.g., Software Engineer)",
                "period": "Start Date -- End Date (e.g., Jan. 2024 -- Present)",
                "description": [
                    "Description 1: Describe a specific accomplishment with quantifiable results (e.g., Increased efficiency by 25%)",
                    "Description 2: Another accomplishment with measurable impact",
                    "Description 3: Third accomplishment highlighting your skills and contributions"
                ]
            },
            {
                "company": "Company Name 2 (e.g., Microsoft Corporation)",
                "location": "City, Country (e.g., Redmond, WA, USA)",
                "position": "Previous Job Title (e.g., Junior Developer)",
                "period": "Start Date -- End Date (e.g., June 2023 -- Dec. 2023)",
                "description": [
                    "Description 1: Specific accomplishment with metrics",
                    "Description 2: Another significant contribution",
                    "Description 3: Third achievement demonstrating your value"
                ]
            },
            {
                "company": "Company Name 3 (e.g., Startup Inc.)",
                "location": "City, Country (e.g., San Francisco, CA, USA)",
                "position": "Internship/Entry Level Position (e.g., Software Engineering Intern)",
                "period": "Start Date -- End Date (e.g., May 2022 -- Aug. 2022)",
                "description": [
                    "Description 1: Internship accomplishment",
                    "Description 2: Learning outcome or project contribution",
                    "Description 3: Skill development or team contribution"
                ]
            }
        ],
        "project_experience": [
            {
                "name": "Project Name 1 (e.g., E-commerce Platform)",
                "period": "Start Date -- End Date (e.g., Mar. 2024 -- Mar. 2024)",
                "description": [
                    "Description 1: Describe a key feature or functionality you implemented",
                    "Description 2: Another important feature or technical achievement",
                    "Description 3: Third feature highlighting your skills"
                ]
            },
            {
                "name": "Project Name 2 (e.g., Machine Learning Model)",
                "period": "Start Date -- End Date (e.g., Jan. 2024 -- Mar. 2024)",
                "description": [
                    "Description 1: Describe what you accomplished in this project",
                    "Description 2: Another significant outcome or learning",
                    "Description 3: Third achievement showing your project management or skills"
                ]
            },
            {
                "name": "Competition/Challenge Name (e.g., Hackathon Winner)",
                "period": "Start Date -- End Date (e.g., Feb. 2024 -- Feb. 2024)",
                "description": [
                    "Description 1: What you accomplished in the competition",
                    "Description 2: Another outcome or recognition",
                    "Description 3: Third achievement demonstrating your competitive skills"
                ]
            }
        ],
        "additional_information": {
            "languages": [
                {
                    "language": "English",
                    "proficiency": "Native/Fluent/Intermediate/Basic"
                },
                {
                    "language": "Second Language (e.g., Spanish)",
                    "proficiency": "Native/Fluent/Intermediate/Basic"
                },
                {
                    "language": "Third Language (e.g., French)",
                    "proficiency": "Native/Fluent/Intermediate/Basic"
                },
                {
                    "language": "Fourth Language (e.g., Mandarin)",
                    "proficiency": "Native/Fluent/Intermediate/Basic"
                }
            ],
            "skills": [
                "Programming Language 1 (e.g., Python)",
                "Programming Language 2 (e.g., JavaScript)",
                "Database Technology (e.g., PostgreSQL)",
                "Framework 1 (e.g., React)",
                "Framework 2 (e.g., Django)",
                "Tool 1 (e.g., Git)",
                "Tool 2 (e.g., Docker)",
                "Platform 1 (e.g., AWS)",
                "Platform 2 (e.g., Google Cloud)"
            ]
        }
    }

    return template_content

# =============================================================================
# PDF COMPILATION
# =============================================================================

def find_pdflatex():
    """Find pdflatex executable"""
    # Check if pdflatex is in PATH
    if shutil.which("pdflatex"):
        return "pdflatex"

    # If not found in PATH, check common LaTeX installation paths
    common_paths = [
        "/usr/local/texlive/2024basic/bin/universal-darwin/pdflatex",
        "/usr/local/texlive/2023/bin/universal-darwin/pdflatex",
        "/usr/local/texlive/2022/bin/universal-darwin/pdflatex",
        "/Library/TeX/texbin/pdflatex",
        "/usr/local/bin/pdflatex",
        "/opt/homebrew/bin/pdflatex"
    ]

    for path in common_paths:
        if os.path.exists(path):
            return path

    return None

def install_latex():
    """Install LaTeX distribution based on platform"""
    system = platform.system()

    if system == "Darwin":  # macOS
        print("To install LaTeX on macOS, please run the following command:")
        print("  brew install --cask basictex")
        print("After installation, please ensure the TeX binaries are in your PATH and run this script again.")
        return False

    elif system == "Linux":
        print("To install LaTeX on your system, please run one of the following commands:")
        print()
        print("For Debian/Ubuntu-based systems:")
        print("  sudo apt-get update && sudo apt-get install -y texlive-full")
        print()
        print("For RHEL/CentOS-based systems:")
        print("  sudo yum install -y texlive")
        print()
        print("After installation, please run this script again.")
        return False

    elif system == "Windows":
        print("Please install MiKTeX manually:")
        print("  1. Download from https://miktex.org/")
        print("  2. Run the installer")
        print("  3. Restart your terminal")
        return False

    else:
        print(f"Unsupported operating system: {system}")
        return False

def compile_latex_to_pdf(latex_file):
    """Compile LaTeX file to PDF using pdflatex"""
    # Validate input file path
    if not validate_file_path(latex_file):
        print(f"Error: Invalid file path: {latex_file}")
        return False
    
    if not os.path.exists(latex_file):
        print(f"Error: File not found: {latex_file}")
        return False
    
    try:
        # Find pdflatex executable
        pdflatex_path = find_pdflatex()
        if not pdflatex_path:
            print("Error: pdflatex not found in PATH.")
            print("Would you like to install a LaTeX distribution now? (y/n)")

            try:
                user_input = get_single_char_input()
                if user_input in ['y', 'yes']:
                    if install_latex():
                        print("Please restart your terminal and try again.")
                    return False
                else:
                    print("PDF compilation cancelled.")
                    return False
            except (KeyboardInterrupt, EOFError):
                print("\nOperation cancelled.")
                return False
            except Exception as e:
                print(f"Error reading input: {e}")
                print("PDF compilation cancelled.")
                return False

        # Get the directory and filename
        latex_path = Path(latex_file)
        latex_dir = latex_path.parent
        latex_name = latex_path.stem

        # Validate filename for security
        if not re.match(r'^[a-zA-Z0-9_-]+$', latex_name):
            print(f"Error: Invalid filename characters in: {latex_name}")
            return False

        # Create a temporary directory for compilation
        temp_dir = None
        
        try:
            temp_dir = tempfile.mkdtemp()
            
            # Copy the LaTeX file to the temporary directory
            temp_latex_file = os.path.join(temp_dir, f"{latex_name}.tex")
            shutil.copy2(latex_file, temp_latex_file)

            # Run pdflatex with proper error handling
            print(f"Compiling {latex_file} to PDF...")

            result = safe_subprocess_run(
                [pdflatex_path, "-interaction=nonstopmode", f"{latex_name}.tex"],
                capture_output=True,
                text=True,
                check=False,  # Don't raise exception, handle manually
                cwd=temp_dir
            )

            # Check if compilation was successful
            if result.returncode != 0:
                print(f"LaTeX compilation failed with return code: {result.returncode}")
                if result.stdout:
                    print("LaTeX output:")
                    print(result.stdout)
                if result.stderr:
                    print("LaTeX errors:")
                    print(result.stderr)
                return False

            # Copy the generated PDF back to the original directory
            pdf_file = f"{latex_name}.pdf"
            if os.path.exists(os.path.join(temp_dir, pdf_file)):
                output_pdf = os.path.join(latex_dir, pdf_file)
                shutil.copy2(os.path.join(temp_dir, pdf_file), output_pdf)
                print(f"PDF generated successfully: {output_pdf}")
                return True
            else:
                print("PDF file was not generated")
                return False

        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except OSError:
                    pass  # Ignore cleanup errors

    except subprocess.CalledProcessError as e:
        print(f"Error compiling PDF: {e}")
        if e.stderr:
            print(f"LaTeX compilation errors:")
            print(e.stderr)
        return False
    except Exception as e:
        print(f"Error during PDF compilation: {e}")
        return False

# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='resume2latex - Convert JSON to LaTeX',
        epilog="""Examples:
  python3 resume2latex.py -t                    # Create template
  python3 resume2latex.py resume.json           # Generate LaTeX
  python3 resume2latex.py resume.json -p        # Generate LaTeX and PDF
  python3 resume2latex.py resume.tex -p         # Compile LaTeX to PDF
  python3 resume2latex.py resume.json -v        # Validate LaTeX
  python3 resume2latex.py file.tex -c           # Check existing LaTeX file

Need help? (y/n)"""
    )
    parser.add_argument('input_file', nargs='?', help='Input JSON file path or LaTeX file path (optional when using --template)')
    parser.add_argument('-o', '--output',
                       help='Output LaTeX file path (default: YOUR-NAME_resume.tex)')
    parser.add_argument('-v', '--validate', action='store_true',
                       help='Validate the generated LaTeX file')
    parser.add_argument('-c', '--check', action='store_true',
                       help='Only check existing LaTeX file without generating new one')
    parser.add_argument('-t', '--template', action='store_true',
                       help='Create a new resume template JSON file')
    parser.add_argument('-p', '--pdf', action='store_true',
                       help='Compile LaTeX file to PDF')

    args = parser.parse_args()

    # If template mode, create a new template file
    if args.template:
        template_content = create_template()
        template_file = "resume_template.json"

        try:
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_content, f, indent=2, ensure_ascii=False)
            print(f"Template created successfully: {template_file}")
            print("You can now edit this file with your information and run:")
            print(f"   python3 resume2latex.py {template_file}")
            print("The template includes detailed examples in parentheses to help you fill it out properly.")
            sys.exit(0)
        except Exception as e:
            print(f"Error creating template: {e}")
            sys.exit(1)

    # If check mode, validate existing file
    if args.check:
        if not args.input_file:
            print("Error: Input file required for check mode")
            sys.exit(1)
        
        if not validate_file_path(args.input_file):
            print(f"Error: Invalid file path: {args.input_file}")
            sys.exit(1)
            
        if validate_latex_syntax(args.input_file):
            sys.exit(0)
        else:
            sys.exit(1)

    # Check if input_file is provided when not in template mode
    if not args.input_file and not args.template and not args.check:
        print()
        print("Collect README.md?(y/n)")

        try:
            user_input = get_single_char_input()
            if user_input in ['y', 'yes']:
                try:
                    readme_content = generate_readme_content()
                    with open('README.md', 'w', encoding='utf-8') as f:
                        f.write(readme_content)
                    print("README.md generated successfully!")
                    sys.exit(0)
                except Exception as e:
                    print(f"Error generating README.md: {e}")
                    sys.exit(1)
            else:
                # Call error handling logic
                print()
                print("ERROR: Either a Input file (JSON or LaTeX) or a specified command flag is required.")
                print()
                print("Usage: python3 resume2latex.py <input_file> [options]")
                print()
                print("Need help? (y/n)")

                try:
                    help_input = get_single_char_input()
                    if help_input in ['y', 'yes']:
                        print()
                        print("—" * 50)
                        print()
                        print("# resume2latex.py is a Python script that converts resume info from JSON data to a formatted resume page in LaTeX.")
                        print("# 1. Create a new template JSON file to fill in, using:")
                        print()
                        print("python3 resume2latex.py -t")
                        print()
                        print("# 2. Generate resume from your JSON file")
                        print()
                        print("python3 resume2latex.py resume.json")
                        print()
                        print("# 3. Compile LaTeX file to PDF")
                        print()
                        print("python3 resume2latex.py resume.tex -p")
                        print()
                        print("# More options:")
                        print("  -h, --help        Show this help message and exit")
                        print("  -v, --validate    Validate the generated LaTeX file")
                        print("  -c, --check       Only check existing LaTeX file without generating new one")
                        print("  -t, --template    Create a new resume template JSON file")
                        print("  -p, --pdf         Compile LaTeX file to PDF")
                        print("  -o, --output [OUTPUT_NAME]")
                        print("                    Output LaTeX file path (default: YOUR-NAME_resume.tex)")
                        print()
                        print("Good luck with everything!")
                        sys.exit(0)
                    if help_input in ['n', 'no']:
                        print("—" * 50 + "\n")
                        print("Good luck with everything!")
                        print()
                        sys.exit(1)
                except KeyboardInterrupt:
                    print("\nOperation cancelled.")
                    sys.exit(1)
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            sys.exit(1)

    # Validate input file path
    if args.input_file and not validate_file_path(args.input_file):
        print(f"Error: Invalid file path: {args.input_file}")
        sys.exit(1)

    # Check if input file is a LaTeX file (ends with .tex)
    if args.input_file and args.input_file.endswith('.tex'):
        # Direct LaTeX to PDF compilation
        if args.pdf:
            if compile_latex_to_pdf(args.input_file):
                print("PDF compilation completed successfully!")
                sys.exit(0)
            else:
                print("PDF compilation failed.")
                sys.exit(1)
        else:
            print("For LaTeX files, use -p flag to compile to PDF")
            sys.exit(1)

    # Load resume data from JSON
    if args.input_file:
        resume_data = load_resume_data(args.input_file)
    else:
        print("Error: No input file specified")
        sys.exit(1)

    # Generate LaTeX content
    latex_content = generate_resume_latex(resume_data)

    # Determine output filename
    if args.output:
        output_file = args.output
        # Validate output file path
        if not validate_file_path(output_file):
            print(f"Error: Invalid output file path: {output_file}")
            sys.exit(1)
    else:
        output_file = generate_output_filename(resume_data)

    # Write to file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        print(f"Resume generated successfully: {output_file}")

        # Validate if requested
        if args.validate:
            print("\n" + "=" * 50)
            if validate_latex_syntax(output_file):
                print("Resume generation and validation completed successfully!")
            else:
                print("Resume generated but validation found issues.")
                sys.exit(1)

        # Compile to PDF if requested
        if args.pdf:
            print("\n" + "=" * 50)
            if compile_latex_to_pdf(output_file):
                print("PDF compilation completed successfully!")
            else:
                print("PDF compilation failed.")
                sys.exit(1)

    except Exception as e:
        print(f"Error writing to {output_file}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
