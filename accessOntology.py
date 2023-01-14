from owlready2 import *
import random
from collections import OrderedDict
import numpy
import collectPropertiesAndValues as cPV
import sys
import itertools


owlready2.JAVA_EXE = "C:\\Program Files\\Java\\jre1.8.0_291\\bin\\java.exe"
ontoFile= os.path.join(sys.path[0], "WorldModelLocomotiveVisualPerception.owl")
ontoFile2= os.path.join(sys.path[0], "WorldModelLocomotiveVisualPerceptionWithInds.owl")
onto = get_ontology("file://"+ontoFile).load()

def assignValueToProp(indiv, prop, value):
    if isinstance(value,numpy.int32):
            value=int(value)
    try: 
        prop[indiv]=value
    except: 
        prop[indiv]=[value]

#filter out anonymous disjoint classes to access general class axioms 
def anonymousDisjointClasses():
    lis=list(onto.disjoint_classes())
    lisNew=[]
    for l in lis:
        try: 
            l.entities[0].name # if an entity has a name, its not an anonymous class
        except:
            lisNew.append(l)
            pass
    return lisNew

def hasPossibleValue(perosn, prop, values):
    broken=False
    if prop[perosn]:# prop has been filled in
        return True
    for value in values:
        brokenInner=False
        assignValueToProp(perosn, prop, value)
        if breaksConstr(perosn): #one constraint has been broken --> this value does not work, try next one
            continue #with the next value
        else: #the value has not broken any numeric constraints, check class constraints
            lisN=anonymousDisjointClasses()
            for r in lisN:
                try:
                    if r.entities[0]._satisfied_by(perosn) and r.entities[1]._satisfied_by(perosn):
                        brokenInner=True
                        break #one constraint has been broken by this value, no need to check other constraints 
                    else: 
                        #this constraint was ok
                        continue
                except:
                    pass
            if brokenInner: #if inner loop is broken, go to next value
                continue 
            broken=True # if this lane is reached, the last value did not break any constrints
            break
    if broken:
        return True
    else: 
        destroy_entity(perosn)
        return False


def fillInAllOblProps(person,obligatoryProps, dictExplain, i ):
    for prop, values in obligatoryProps.items():
        valuesRandom=random.sample(values, len(values))
        if not hasPossibleValue(person, prop, valuesRandom): # either an implicit conflict with initial pair, or a conflict with one of previous obligatory props filled in at random. If latter, backtracking needed!
            keys=list(i.keys())
            dictExplain.append({'p1':str(keys[0]), 'vp1': str(i[keys[0]]), 'p2':str(keys[1]), 'vp2':str(i[keys[1]]), 'reason':'no suitable value for ' +prop.name})
            dictExplain.append({'p1':str(keys[1]), 'vp1': str(i[keys[1]]), 'p2':str(keys[0]), 'vp2':str(i[keys[0]]), 'reason':'no suitable value for ' +prop.name})
            break

def breaksConstr(ind):
    dic= {}
    for prop in ind.get_properties():
        for value in prop[ind]:
            dic[prop]=value
    for rule in rules:
        try:
            if rule(dic):
                return True
        except KeyError:
            pass
    return False

rules = [lambda d: d[onto.hasSpeed]<6  and d[onto.hasPose]==onto.running,
            lambda d: d[onto.hasSpeed]>0  and d[onto.hasPose]==onto.sitting,
            lambda d: d[onto.hasSpeed]>0  and d[onto.hasPose]==onto.standing,
            lambda d: d[onto.hasSpeed]>0  and d[onto.hasPose]==onto.laying,
            lambda d: d[onto.hasSpeed]>2  and d[onto.hasPose]==onto.crawling,
            lambda d: (d[onto.hasSpeed]>5  or d[onto.hasSpeed]<1) and d[onto.hasPose]==onto.walking,
            lambda d: d[onto.hasSpeed]>10  and d[onto.usingMobilityAid]==onto.wheelChair,
    ] 

def generate_pairs(params, key1, key2, res):
	tuples_a = [(key1, val) for val in params[key1]]
	tuples_b = [(key2, val) for val in params[key2]]
	pairs = itertools.product(tuples_a, tuples_b)
	res.append([{pair[0][0]: pair[0][1], pair[1][0]: pair[1][1]} for pair in pairs])

def flatten(lis):
    flat_list = [item for sublist in lis for item in sublist]
    return flat_list

def generate_all_pairs(params):
    result = []
    for key1, key2 in itertools.combinations(params.keys(), r=2):
        generate_pairs(params, key1, key2, result)
    res=flatten(result)
    return res

def obligProps(dict):
    obligatoryProps= OrderedDict()
    for key, value in dict.items():
        if onto.obligatory in key.is_a:
                obligatoryProps[key]=dict[key]
    obligatoryProps[onto.hasSpeed]=dict[onto.hasSpeed]
    return obligatoryProps

def returnDict():
    dictExplain=[]
    ind= onto.Person()
    dict=cPV.createDict(ind)
    destroy_entity(ind)
    
    #filter out only obligatory properties
    obligatoryProps= obligProps(dict)
    
    init=generate_all_pairs(dict)

    for i in init:
        #initial check of values pair for speed rules
        broken_out=False
        for rule in rules:
            try:
                if rule(i):
                    keys=list(i.keys())
                    dictExplain.append({'p1':str(keys[0]), 'vp1': str(i[keys[0]]), 'p2':str(keys[1]), 'vp2':str(i[keys[1]]), 'reason':'invalid speed & pose combination'})
                    dictExplain.append({'p1':str(keys[1]), 'vp1': str(i[keys[1]]), 'p2':str(keys[0]), 'vp2':str(i[keys[0]]), 'reason':'invalid speed & pose combination'})
                    broken_out=True
                    break
            except KeyError:
                pass
        if broken_out: #pair did not satisfy one numeric constraint
            continue # with next pair
        
        #pair passed numeric constraints    
        indiv=onto.Person()
        for prop, value in i.items():
            assignValueToProp(indiv, prop, value)
        
        #check whether pair passes non-numeric constraints
        lis=anonymousDisjointClasses()

        for r in lis:
            try: #check whether ind satisfies conditions to be assigned to 2 disjoint classes at the same time
                if r.entities[0]._satisfied_by(indiv) and r.entities[1]._satisfied_by(indiv):
                        keys=list(i.keys())
                        dictExplain.append({'p1':str(keys[0]), 'vp1': str(i[keys[0]]), 'p2':str(keys[1]), 'vp2':str(i[keys[1]]), 'reason':str(r.entities)})
                        dictExplain.append({'p1':str(keys[1]), 'vp1': str(i[keys[1]]), 'p2':str(keys[0]), 'vp2':str(i[keys[0]]), 'reason':str(r.entities)})
                        destroy_entity(indiv)
                        broken_out=True
                        break
            except: # error returned when constraint contains numeric property, because ._satisfied_by(indiv) is not implemented for those
                continue
        if broken_out:
            continue # with next pair/ ind  

        #pair passes test and is a candidate for a valid individual  
        fillInAllOblProps(indiv,obligatoryProps, dictExplain, i )

    onto.save(file=ontoFile2)
    print('total no of pairs:',len(init))
    print('no of valid inds:',len(list(onto.Person.instances())))
    print('no of discarded inds:',len(dictExplain)/2) #because I entered every discarded pair twice for the matrix, only lower half of which will be shown
    return dictExplain