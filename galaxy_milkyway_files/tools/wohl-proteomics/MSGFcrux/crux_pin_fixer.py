import orangecontrib
from orangecontrib.bio.ontology import OBOParser
import sys
import csv
import getopt
import re

###############################################
#CRUX PIN FIXER
#William Barshop - 2016/08/26
date="2016/08/26"
#Laboratory of James A. Wohlschlegel, UCLA
#
#VERSION:--------------------------------------
#0.6.1 ALPHA
version="0.6.1"
#
#DESCRIPTION:----------------------------------
#crux_pin_fixer.py is a script designed to correct pin files generated from msgf2pin
#and reformat the PSMIDs to be crux friendly.
#This requires reformatting of the PSMids from msgf2pin (formatted as : 2015-05-26-wb-HEK293-Std-rtid2_SII_192_1_192_2_1 )
#to something more crux friendly -- ie replacing the filename with an integer fileID and placing in either
#"target" or "decoy" at the start of the PSM file ID... like ( target_0_35_1_5 )
#
#The script will OUTPUT a "mapping" file with two columns, the data analysis file name, and the corresponding
#crux-internal integer label.  If no filename is given for the output, the basename of the pin will be used
#and appended with the extension .cruxmap
#Additionally, if no output location is given, the reprocessed pin file will be output to the basename of the input file
#and appended with .crux_ready.pin
#
#can now also strip the MSGF+ required selenocysteine modification out...
#
#SYNTAX AND USAGE:-----------------------------
#python crux_pin_fixer.py -i <INPUT-TAB-DELIM-PIN.pin> -o <OUTPUT-FILE> -m <MAP-FILE> -u <unimod.obo>
#
###############################################

def help():
    print "Syntax and usage as follows:"
    print "python crux_pin_fixer.py -i <INPUT-TAB-DELIM-PIN.pin> -o <OUTPUT-FILE> -m <MAP-FILE> -u <unimod.obo> -s"
    print "Version:",version
    print "Dated:",date

input = None
output = None
mapfile = None
mod_obo = None

try:
    opts, args = getopt.getopt(sys.argv[1:], "ho:i:m:u:s", ["help", "output=","input=","map=","mod_obo="])
except getopt.GetoptError as err:
    # print help information and exit:
    print str(err)
    print "-------------------------------------------------"
    print "Invalid syntax or option!"
    help()
    sys.exit(2)

for option, value in opts:
    if option in ("-h","--help"):
        help()
        sys.exit()
    elif option in ("-o","--output"):
        output = value
    elif option in ("-i","--input"):
        input = value
    elif option in ("-m","--map"):
        mapfile = value
    elif option in ("-u","--unimod"):
        mod_obo = value
    elif option in ("-s","--seleno"):
        seleno = value
if input is None:
    print "Come on... at least give me an input...."
    help()
    sys.exit(2)

if mapfile is None:
    mapfile = input.rsplit(".",1)[0]
    mapfile +=".cruxmap"

if output is None:
    output = input.rsplit(".",1)[0]
    output +=".crux_ready.pin"

if mod_obo is None:
    print "mod_obo is needed! Please run with \'-u unimod_obo\' in the arguments "
    sys.exit(2)

print "Input file will be read from",input
print "Output file will be written to",output
print "Mapfile output file will be written to",mapfile

fileNameDictionary={}
#            if len(myline)>2:
#                if myline[2] in bio_cond_groups:
#                    bio_cond_groups[myline[1]].append(myline[2])
#                else:
#                    bio_cond_groups[myline[1]]=[myline[2]]
#print bio_cond_groups,"These are the biological conditions."

file_int=0


mod_bracket_re='\[|\]'
mod_dict={}

with open(mod_obo,"r") as unimod_obo:
        peptide_index=0
        obo_parser=orangecontrib.bio.ontology.OBOParser(unimod_obo)
        with open(input,"r") as openfile:
            with open(output,"wb") as outputwriter:
                for eachline in openfile:
                    line=eachline.split("\t")
                    if peptide_index==0:
                        for each_column in line:
                            if each_column=="Peptide":
                                break
                            else:
                                #print each_column
                                peptide_index+=1
                    #print line  


                    if line[0]=="SpecId":
                        outputwriter.write(eachline)
                        continue
                    elif line[0]=="DefaultDirection":
                        outputwriter.write(eachline)
                        continue

                    if line[1] == "1":
                        target="target"
                    else:
                        target="decoy"
                    
                    if target:
                        file_name=line.split("target_SII",1)[0][:-1]
                    else:
                        file_name=line.split("decoy_SII",1)[0][:-1]

                    file_name=line[0].split("_")[0]
                    #print file_name
                    if file_name not in fileNameDictionary:
                        fileNameDictionary[file_name]=file_int
                        file_int+=1


                    #print line, "THIS IS LINE"
                    #print line[0], "THIS IS LINE 0"






                    #print len(line),"this is line len"
                    #print line
                    #print line[peptide_index]



                    new_peptide=None
                    #print "LIN53",line[peptide_index]
                    #print line, peptide_index
                    #print "line len",len(line)
                    if seleno:
                        this_pep=line[peptide_index].replace("[UNIMOD:162]","")
                        line[peptide_index]=this_pep


                    if "UNIMOD" in line[peptide_index]:
                        split_peptide=re.split(mod_bracket_re,line[peptide_index])
                        #print split_peptide
                        new_peptide=[]
                        for each_split in split_peptide:
                            if "UNIMOD" in each_split:
                                if each_split in mod_dict:
                                    new_peptide.append(mod_dict[each_split])
                                else:
                                    
                                    trigger=False
                                    for event,value in obo_parser:
                                        if "TAG_VALUE" in event and not trigger:
                                            if each_split in value[1]:
                                                #print "YO",value[1]
                                                trigger=True
                                                pass
                                        elif trigger:
                                            #print value[1],"val1"
                                            if "delta_mono_mass" in value[1]:
                                                mass="[+"
                                                mass+=value[1].split("\"")[1]
                                                if "-" in mass:
                                                    mass.replace("+","")
                                                mass+="]"
                                                #print mass,"THIS IS MAH MASS"
                                                trigger=False
                                                break
                                        else:
                                            continue
                                        
                                    mod_dict[each_split]=mass
                                    new_peptide.append(mass)
                                        
                            else:
                                new_peptide.append(each_split)
                        new_peptide=''.join(new_peptide)
                        

    
                                
    

                                    



                    newSpecID = target + "_" + str(fileNameDictionary[file_name]) + "_" + str(line[2]) + "_" + str(line[0].split("_")[5]) + "_" + str(line[0].split("_")[6])
                    #print newSpecID
                    #print line
                    #print eachline
                    line[0] = newSpecID
                    if not new_peptide is None:
                        line[peptide_index]=new_peptide #####CHECK IF THIS SHOULD BE 53
                    #print line,"AFTER"
                    writeLine = ""
                    for eachItem in line:
                        writeLine += eachItem
                        writeLine += "\t"
                    writeLine=writeLine[:-2]+"\n"
                    #print writeLine
                    outputwriter.write(writeLine)
        
                    #pause=raw_input("continue?")

with open(mapfile,"wb") as mapfilewriter:
    mapfilewriter.write("Crux File Integer\tOriginal File Name\n")
    for each in fileNameDictionary:
        #print each
        mapfilewriter.write(str(fileNameDictionary[each])+"\t"+each+"\n")
print "Finished!"
