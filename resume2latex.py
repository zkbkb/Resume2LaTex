#!/usr/bin/env python3
"""
resume2latex - Convert JSON resume to LaTeX format
"""

import json
import sys
import re
import argparse
from datetime import datetime
import os
import platform

def load_resume_data(json_file):
    """Load resume data from JSON file"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_file} not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {json_file}: {e}")
        sys.exit(1)

def generate_latex_header():
    """Generate LaTeX document header"""
    return r"""\documentclass[letterpaper,11pt]{article}

%---------- PACKAGES ----------
\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
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

"""

def generate_heading(personal_info):
    """Generate the heading section"""
    name = personal_info['name'].replace('{', '\\{').replace('}', '\\}').replace('&', '\\&')
    phone = personal_info['phone'].replace('{', '\\{').replace('}', '\\}').replace('&', '\\&')
    email = personal_info['email'].replace('{', '\\{').replace('}', '\\}').replace('&', '\\&')
    location = personal_info['location'].replace('{', '\\{').replace('}', '\\}').replace('&', '\\&')
    website = personal_info['website'].replace('{', '\\{').replace('}', '\\}').replace('&', '\\&')
    
    return f"""%---------- HEADING ----------
\\begin{{center}}
    \\textbf{{\\Huge \\scshape {name}}} \\\\ \\vspace{{3pt}}
    \\small
    {phone} $|$ {email} $|$ {location} $|$ {website}
\\end{{center}}

"""

def generate_education(education):
    """Generate the education section"""
    institution = education['institution'].replace('{', '\\{').replace('}', '\\}').replace('&', '\\&')
    location = education['location'].replace('{', '\\{').replace('}', '\\}').replace('&', '\\&')
    degree = education['degree'].replace('{', '\\{').replace('}', '\\}').replace('&', '\\&')
    period = education['period'].replace('{', '\\{').replace('}', '\\}').replace('&', '\\&')
    core_modules = ', '.join(education['details']['core_modules']).replace('{', '\\{').replace('}', '\\}').replace('&', '\\&')
    grade = education['details']['grade'].replace('{', '\\{').replace('}', '\\}').replace('&', '\\&')
    
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
        company = exp['company'].replace('{', '\\{').replace('}', '\\}').replace('&', '\\&')
        location = exp['location'].replace('{', '\\{').replace('}', '\\}').replace('&', '\\&')
        position = exp['position'].replace('{', '\\{').replace('}', '\\}').replace('&', '\\&')
        period = exp['period'].replace('{', '\\{').replace('}', '\\}').replace('&', '\\&')
        
        latex += f"""    \\resumeSubheading
      {{{company}}}{{{location}}}
      {{{position}}}{{{period}}}"""
        
        if exp['description']:
            latex += "\n        \\resumeItemListStart\n"
            for description in exp['description']:
                description_escaped = description.replace('{', '\\{').replace('}', '\\}').replace('&', '\\&').replace('%', '\\%')
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
        name = project['name'].replace('{', '\\{').replace('}', '\\}').replace('&', '\\&')
        period = project['period'].replace('{', '\\{').replace('}', '\\}').replace('&', '\\&')
        
        latex += f"""      \\resumeProjectHeading
        {{\\textbf{{{name}}}}}{{{period}}}"""
        
        if 'description' in project:
            latex += "\n          \\resumeItemListStart\n"
            for description in project['description']:
                description_escaped = description.replace('{', '\\{').replace('}', '\\}').replace('&', '\\&').replace('%', '\\%')
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
    languages_str = languages_str.replace('{', '\\{').replace('}', '\\}').replace('&', '\\&')
    skills_str = skills_str.replace('{', '\\{').replace('}', '\\}').replace('&', '\\&')
    
    return f"""%---------- ADDITIONAL INFORMATION -----------
\\section{{ADDITIONAL INFORMATION}}
  \\vspace{{2pt}}
  \\resumeSubHeadingListStart
    \\small{{\\item{{
        \\textbf{{Languages:}} {languages_str} \\\\ \\vspace{{3pt}}
        
        \\textbf{{Technical Skills:}} {skills_str} \\\\ \\vspace{{3pt}}
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
                    "Description 3: Third feature highlighting your technical skills"
                ]
            },
            {
                "name": "Project Name 2 (e.g., Machine Learning Model)",
                "period": "Start Date -- End Date (e.g., Jan. 2024 -- Mar. 2024)",
                "description": [
                    "Description 1: Describe what you accomplished in this project",
                    "Description 2: Another significant outcome or learning",
                    "Description 3: Third achievement showing your project management or technical skills"
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

def get_single_char_input():
    """Get a single character input without requiring Enter key"""
    if platform.system() == "Windows":
        import msvcrt
        return msvcrt.getch().decode('utf-8').lower()
    else:
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch.lower()

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

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='resume2latex - Convert JSON to LaTeX')
    parser.add_argument('json_file', nargs='?', help='Input JSON file path (optional when using --template)')
    parser.add_argument('-o', '--output', 
                       help='Output LaTeX file path (default: YOUR-NAME_resume.tex)')
    parser.add_argument('-v', '--validate', action='store_true', 
                       help='Validate the generated LaTeX file')
    parser.add_argument('-c', '--check', action='store_true',
                       help='Only check existing LaTeX file without generating new one')
    parser.add_argument('-t', '--template', '--t', '-template', '--template', action='store_true',
                       help='Create a new resume template JSON file')
    
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
        if validate_latex_syntax(args.json_file):
            sys.exit(0)
        else:
            sys.exit(1)
    
    # Check if json_file is provided when not in template mode
    if not args.json_file and not args.template and not args.check:
        print()
        print("ERROR: Either a Input JSON file or a specified command flag is required.")
        print()
        print("Usage: python3 resume2latex.py <json_file> [options]")
        print()
        print("Need help? (y/n)")
        
        try:
            user_input = get_single_char_input()
            if user_input in ['y', 'yes']:
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
                print("# More options:")
                print("  -h, --help        Show this help message and exit")
                print("  -v, --validate    Validate the generated LaTeX file")
                print("  -c, --check       Only check existing LaTeX file without generating new one")
                print("  -t, --template    Create a new resume template JSON file")
                print("  -o, --output [OUTPUT_NAME]")
                print("                    Output LaTeX file path (default: YOUR-NAME_resume.tex)")
                print()
                print("Good luck with everything!")
                sys.exit(0)
            if user_input in ['n', 'no']:
                print("—" * 50 + "\n")
                print("Good luck with everything!")
                print()
                sys.exit(1)        
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            sys.exit(1)
    
    # Load resume data
    resume_data = load_resume_data(args.json_file)
    
    # Generate LaTeX content
    latex_content = generate_resume_latex(resume_data)
    
    # Determine output filename
    if args.output:
        output_file = args.output
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
                
    except Exception as e:
        print(f"Error writing to {output_file}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 