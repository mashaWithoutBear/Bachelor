from owlready2 import *
from collections import OrderedDict
import numpy

owlready2.JAVA_EXE = "C:\\Program Files\\Java\\jre1.8.0_291\\bin\\java.exe"
ontoFile= os.path.join(sys.path[0], "WorldModelLocomotiveVisualPerception.owl")#"C:\\Users\\mku\\Documents\\ScenarienTesting\\ontology\\ki-lok-ontology\\KI-LOK-Scenerio-Description_Mascha_WIP.owl"
onto = get_ontology("file://"+ontoFile).load()
def render_using_label(entity):
    return entity.name
#print entity based on its label, without the whole address
set_render_func(render_using_label)

def isLeaf(node):
    try:
        node.subclasses()
        return not list(node.subclasses())
    except:
        return True

def populateDicWithFilledInProps(ind,dic):
    properties=ind.get_properties()
    for pr in properties:
        if isLeaf(pr):
            dic[pr]= pr[ind]

def applyFuncAndFlattenList(func, obj):
    lis= list(map(func, obj))
    flatList= [item for sublist in lis for item in sublist]
    return flatList

def retrieveAnonAncestors(node):
    if isinstance(node,Thing):
        cl=node.is_a # list!
    else:
        cl=node
    listOfAncs= applyFuncAndFlattenList((lambda a:a.ancestors(include_constructs=True)), cl)
    ret= list( filter (lambda a:  not isinstance(a, ThingClass) ,listOfAncs )) #listOfAncs #only anonymous! Classes filtered out. why actually?..
    return ret

def classRestrictions(anonAnc):
    #whatch out with classes with multiple anonymous ancestors!!!
    restrs=[]
    for anAnonAnc in anonAnc:
        try:
        #if restriction is a AND OR etc construct
            anAnonAnc.Classes
        #might be a class &..., not only restrictions, e.g. PoliceVehicle is a SpecialVehichle & hasColouring... 
        #I'm only interested in CRs!-> filter out named classes
            restrs.append(list(filter(lambda l:not isinstance(l,ThingClass),list(anAnonAnc.Classes)))) 
        except:
        #if there is just the restriction
            restrs.append([anAnonAnc])
    try: 
        restrs[0][0]
        flatList= [item for sublist in restrs for item in sublist]
    except: flatList= restrs
    return flatList# restrs

def narrowestInterval(prop, value, node): # finds narrowerst interval of values by searching for anonymous ancestors with relevant class restriction
    minInit=(value).__dict__['min_inclusive']
    minAct=minInit
    maxInit=(value).__dict__['max_inclusive']
    maxAct=maxInit
    ans=retrieveAnonAncestors(node)
    restrictions=classRestrictions(ans)
    for restriction in restrictions:
        if restriction.property==prop:
            try:
                minCurr= (restriction.value).__dict__['min_inclusive']
                if minCurr>minAct:
                    minAct=minCurr
                maxCurr= (restriction.value).__dict__['max_inclusive']
                if maxCurr <maxAct:
                    maxAct=maxCurr
            except: continue

    return (minAct, maxAct)

def removeDupl(lis):#
    result = [] 
    for i in lis: 
        if i not in result: 
            result.append(i)
    return result

def discretize(prop, interval):
    min, max=interval
    ret=numpy.linspace(min, max, num=7, endpoint=True, dtype=(prop.range[0]).__dict__["base_datatype"]) #dtype has to be dependent of prop!
    retF= removeDupl(ret)
    return list(retF)

def dealWithDataProp(prop, value, node):
    ret=[]
    if value==type(False):
        return [True,False]
    elif value==type(1.3): #TODO: change from dummy value to actual values!
        print('its a float')
        return [1.3] 
    try: #check whether it's a ConstrainedDatatype
            (value).__dict__["base_datatype"]
            interval=narrowestInterval(prop, value, node)
            return discretize(prop, interval) # in up to 7 equidistand values. 7 is hardcoded
    except:
            print("not a constraint") 
    try: #check whether it's a OneOf
            (value).instances
            return (value).instances
    except:
            pass       
    if type(value)==type(1):
        ret= [1] #TODO: change from dummy value to actual values!
    return ret

def subtree(node):
    return list(onto.search(subclass_of= node))

def leavesOf(node, instances):
    if instances:
        try: 
            inst=node.instances()
            if inst:
                return inst
        except:
            print('{}has no instances'.format(node))
    leaves= list(filter(lambda node: isLeaf(node) ,subtree(node)))
    return leaves

def dealWithParamValues(dic, node):
    dicRet={}
    for key, value in dic.items():  
        if isinstance(key, owlready2.prop.DataPropertyClass):
            dicRet[key]=dealWithDataProp(key, value[0], node)
            continue
        try: #check if the range is a class expression, like (cl1 OR cl2 ...)
            values=(value[0]).Classes # only those properties with 1 class expression!
            dicRet[key]=values
        except: 
            dicRet[key]=flatten(list(map(lambda a: leavesOf(a, True), value)))  
    return dicRet

def flatten(lis):
    flat_list = [item for sublist in lis for item in sublist]
    return flat_list

def isInDomain(cl, prop):#
    answer= False
    try: 
        answer= cl in (prop.domain[0]).Classes
    except:
        answer = cl in prop.domain
    return answer

def listOfParents(node):#
    cl=node 
    if isinstance(node,Thing): #if node is an ind
        cl=node.is_a[0]
    return cl.ancestors()

def allPropsOfNode (node):
    #not quite all properties though, just those which have any of the superclasses of this 
    #individiual as domain! Others should be collected from class restrictions
    properties= list(onto.properties())
    propOfNode= []
    #go through all parents because if class vehicle has property hasColouring, the bus1's parent class, Bus, won't have this property!
    #because otherwise reasoner would say that everything that has a colour is a Bus
    for cl in listOfParents(node):
        propOfNode.append( list(filter(lambda ap: ( isInDomain(cl, ap)) if ap.domain else False, properties)))
    removeDupl(propOfNode)
    flat_list = [item for sublist in propOfNode for item in sublist]
    return flat_list


def createDicForProps(node, props):
    dummy={}
    for pr in props:
        #check whether this property can only have one value for this individual; and has been assigned by reasoner!!! 
        if pr[node]:
            dummy[pr]=list(pr[node])
            continue
        dummy[pr]=[(pr.range)[0]] #only 1st element of the list of a property's range! all relevant props in the ontology have only 1 entry in range
    return dummy

def createDic(node):
    propOfNode=allPropsOfNode(node) #list
    dic= createDicForProps(node, propOfNode)
    return dic

def createDict(node):
        dic2= createDic(node)
        dic3=dealWithParamValues(dic2, node)
        dicAllFilledInProps={}
        populateDicWithFilledInProps(node,dicAllFilledInProps)
        dic3.update(dicAllFilledInProps)
        return OrderedDict(dic3)