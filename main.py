import ollama
import os
import requests
import pandas as pd
import json
# import sys
import fiona

#functions:
from flood_functions import get_svi_stats_and_tracts, get_flash_flood_warnings, get_flood_data, get_flood_map

#signatures:
signatures_path = "C:\\Users\\kimia\\OneDrive\\Documents\\Python Scripts\\FloodLlama\\signatures.txt"

#question = "What are the current flood alerts for the New Orleans area? "
# question= """For the "Lakeview neighborhood in New Orleans which is Located near Lake Pontchartrain", can you provide SVI statistics 
# for areas with an SVI score higher than 0.9?"""
question = """For Middlesex County in Massachusetts please provide SVI statistics for Household Characteristics Theme with an SVI score smaller than 0.5"""

question += """\n\n use the following function signutres and provide answer so that I can use the correct function.\n\n"""


# Read the content of the signatures.txt file
with open(signatures_path, 'r',encoding= "utf8") as file:
    prompt = file.read()

prompt += f"""[INST] {question}[/INST]"""

#test1
#print(prompt)

#test2(functions_calling_SVI)
# print(get_svi_stats_and_tracts("NJ","Middlesex County","RPL_THEME4",">",0.08))

#test3(function_calling_warning)
# print(get_flash_flood_warnings("FL"))

# test4(function_calling_data)
# print(get_flood_data("1130 Jaguar Pkwy San Antonio TX 78224"))
#94 Bayard St New Brunswick NJ 08901

#test5(function_calling_map)==FAILED

######################################################
print(prompt)

result = ollama.generate("llama2_function_calling_q3",prompt)
response = result['response']
sample_answer = response.strip()
print(response)
print("------------------")

sample_answer_dict = eval(sample_answer)
function_name = sample_answer_dict['function']
arguments = list(sample_answer_dict['arguments'].values())
print(function_name)
print(arguments)
print("------------------------")

result = eval(f"globals()['{function_name}'](*arguments)")
print(result)

second_prompt = f"""please polish the following answer based on the following question, coherent and human readble question:[BOS]{question}[EOS],
***
Answer:[BOS]"""+result+"""[EOS]"""

final_result = ollama.generate('llama2_chat_q2', second_prompt)
print(final_result)
