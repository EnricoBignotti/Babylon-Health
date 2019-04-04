# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 11:12:24 2019

@author: Francesca
"""

import numpy as np
import pandas as pd
import re
import csv

def predicate_sort(df):
    '''
        Creates a sorted list of predicates to in turn sort all the predicates
        to have the same structure within the DataFrame and then
        enable the sorting of the DataFrame in a RDF-like fashion  
    
    '''
    predicates= pd.Categorical(df['predicate'].unique(), categories=['rdf:type', 'rdfs:subClassOf', 'rdfs:comment', 'rdfs:label', 'owl:versionInfo'], ordered=True)
    df['predicate'] = pd.Categorical(df['predicate'],predicates,ordered=True)
    return df.sort_values(by=['subject','predicate'],inplace = True)

def df_to_turle(df):
    '''
        Formatting each columns of the DataFrame according to the Turtle syntax  
    
    '''
    df['subject'] = '<' + df['subject'] + '>'
    df['predicate'] = df['predicate'].str.replace('http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'rdf:type')
    df['predicate'] = df['predicate'].str.replace('http://www.w3.org/2000/01/rdf-schema#label', 'rdfs:label')
    df['predicate'] = df['predicate'].str.replace('http://www.w3.org/2000/01/rdf-schema#comment', 'rdfs:comment')
    df['predicate'] = df['predicate'].str.replace('http://www.w3.org/2000/01/rdf-schema#subClassOf', 'rdfs:subClassOf')
    df['predicate'] = df['predicate'].str.replace('http://www.w3.org/2002/07/owl#versionInfo', 'owl:versionInfo')
    owl = df['object'].str.startswith("http://w")
    df.loc[owl, 'object'] = df['object'].str.replace('http://www.w3.org/2002/07/owl#Class','owl:Class;')
    uri = df['object'].str.startswith("http://o")
    df.loc[uri, 'object'] = '<' + df['object'] + '>;'
    literal = df['object'].str[0].str.isupper()
    df.loc[literal, "object"] = '\"' + df['object'] + '\"@en .'
    return df
#read the .tsv as a DataFrame, then applies the functions to format it according to the Turtle syntax
ont1 = pd.read_csv('1.tsv',sep='\t',names=['subject','predicate','object'],quoting=csv.QUOTE_NONE)
df_to_turle(ont1)
predicate_sort(ont1)
ont1.to_csv('ont1.txt',sep=' ',header=None,index=None)
with open('ont1.txt', 'r') as istr:
    with open('ont1.rdf', 'w') as ostr:
        for line in istr:
            if 'rdf:type' in line:
                line = line +'\t\t' 
            print(line, file=ostr)

ont2 = pd.read_csv('2.tsv',sep='\t',names=['subject','predicate','object'])
df_to_turle(ont2)
predicate_sort(ont2)

ont2.to_csv('ont2.txt',sep=' ',header=None,index=None)
with open('ont2.txt', 'r') as istr:
    with open('ont2.rdf', 'w') as ostr:
        for line in istr:
            if 'rdf:type' in line:
                line = line +'\t\t' 
            print(line, file=ostr)

#create a new DataFrame that contains the rows which are not present either
#in ont1 or ont2, sort it and rest the index
            
diff = pd.concat([ont1,ont2],ignore_index=True).drop_duplicates(keep=False)
predicate_sort(diff)
diff.reset_index(inplace=True)

# Now we find the equivalent classes within the DataFrame

#list of mappings
mapping=[]
#index of the DataFrame to use as a condition while looping through the DataFrame
df_index = diff.last_valid_index()
#since the rows repeat themselves in a fixed intervalm we save this interval
skip = len(list(diff['predicate'].unique()))+1
#initialize index at 1 since index 0 is a class predicate
index = 1
while index < df_index and skip < df_index:
    #check that the object value is the same at index and down in the DataFrame
    #in other words, we check that both rows have the same value for rdfs:comment
    if diff.iloc[index].object == diff.iloc[skip].object:
        index += 1
        skip += 1
        #now, we check that both rows have the same value for rdfs:label
        if diff.iloc[index].object == diff.iloc[skip].object:
            #create a list that contains the two classes, connected via owl:equivalentClass 
            eq_class = [diff.iloc[index].subject, 'owl:equivalentClass', diff.iloc[skip].subject]
            #adds the list to the mappings list 
            mapping.append(eq_class)            
            index += 2
            skip += 2
        else:
            #if only rdfs: is the same, move on to the next rdfs:comment row
            index+=3
            skip+=3
    else:
        #if nothing is found, move on to the next rdfs:comment row
        index+=3
        skip+=3
#creates the mapping file
with open('mapping.csv', 'w') as mappings:
    wr = csv.writer(mappings, quoting=csv.QUOTE_NONE,lineterminator='\n')
    for element in mapping:
        wr.writerow([element[0] + '' + element[1] + '' + element[2]])

#creates the mapping DataFrame and adds it to the final DataFrame
map_df = pd.DataFrame(data=[[mapping[0][0],mapping[0][1],mapping[0][2]],[mapping[1][0],mapping[1][1],mapping[1][2]]], columns=['subject','predicate','object'])
ont3=pd.concat([ont1, map_df], axis=0)
ont3.to_csv('ont3.txt',sep=' ',header=None,index=None)
with open('ont3.txt', 'r') as istr:
    with open('ont3.rdf', 'w') as ostr:
        for line in istr:
            if 'rdf:type' in line:
                line = line +'\t\t' 
            print(line, file=ostr)
