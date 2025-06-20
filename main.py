import re
import csv
import os
from pathlib import Path
from typing import List, Dict, Tuple
import pandas as pd

# Usage example

def parse_voicelines(filepath):

    
    with open(filepath, 'r', encoding='utf-8') as f:
        content=f.read()

    all_gojo_dialogues = {}
    all_dialogues=[]

    all_dialogues.append(['previous_speaker', 'prev_text', 'target\'s voicelines', 'next_speaker', 'next_text'])
    

    start_idx = content.find("[Events]")

    lines = content[start_idx:].splitlines()
    count=1

    for i,line in enumerate(lines):
        if line.startswith("Dialogue") and "Gojou" in line:
            parts = line.split(",", 9)

            # if len(parts)>=10:
            #     dialogue_text = parts[9].replace("\\N","\n").strip()
            #     all_gojo_dialogues[count] = dialogue_text
            #     count+=1

            if len(parts)<10:
                continue;
    

            gojo_text = parts[9].replace("\\N","\n").strip()

            prev_text=""
            prev_speaker=""
            next_text=""
            next_speaker=""

            if i>0 and lines[i-1].startswith("Dialogue"):
                prev_parts = lines[i-1].split(",",9)
                if len(prev_parts)>=10:
                    prev_text = prev_parts[9].replace("\\N","\n").strip()
                    prev_speaker =  prev_parts[4].strip()

            if i+1<len(lines) and lines[i+1].startswith("Dialogue"):
                next_parts = lines[i+1].split(",",9)
                if len(next_parts)>=10:
                    next_text = next_parts[9].replace("\\N","\n").strip()
                    next_speaker = next_parts[4].strip()

            all_gojo_dialogues[i] = {
                "target_chracter": gojo_text,
                "prev_speaker": prev_speaker,
                "prev_dialogue": prev_text,
                "next_speaker":next_speaker,
                "next_dialogue":next_text

            }

            all_dialogues.append([prev_speaker, prev_text, gojo_text, next_speaker, next_text])

    # i=1

    # for ch in content[start_idx:]:
    #     i+=1
    #     idx = content.find("Gojou")
    #     to_find_till_key = content.find("Dialogue")
    #     dialogue = content[idx + 17: to_find_till_key]

    #     # all_gojo_dialogues.append({i, dialogue})
    #     all_gojo_dialogues[i] = dialogue


    # # print(f"Content of file: \n{type(content)}")
    print(f"{len(all_gojo_dialogues)} Gojo dialogues are as follows:\n")

    for i,j in all_gojo_dialogues.items():
        print("Dialogues for index {i}:\n")
        # print(f"Dialogue no {i}: {j}")
        print(f"{j['prev_speaker']}: {j['prev_dialogue']}")
        print(f"Gojo: {j['gojo']}")
        print(f"{j['next_speaker']}: {j['next_dialogue']}")

    return all_dialogues

def main():

    dataset = "gojo_voicelines.csv"
    relative_path = "Gojo Satoru dataset/"

    files = [ #enter your list of files to be parsed here
    ]

    data=[]


    with open(dataset,'w') as f:
        writer = csv.writer(f)
        for idx,file in enumerate(files):
            file_path = relative_path + '/' + file
            rows = parse_voicelines(file_path)

            if idx==0:
                data.extend(rows)
            else:
                data.extend(rows[1:])
        
        writer.writerows(data)


if __name__ == "__main__":
    main()
