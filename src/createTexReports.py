import subprocess,os

def generate_tex_report(template_name,format_dict):
    template_location = "templates/"+template_name
    with open(template_location,"r") as myFile:
        tex_template = myFile.read()
    tex_text = tex_template.format(**format_dict)
    with open("temp/temp.tex","w") as myFile:
        myFile.write()
