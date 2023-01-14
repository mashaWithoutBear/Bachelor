from owlready2 import *
import numpy
import matplotlib as mpl
import plotly.express as px
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import collectPropertiesAndValues as cPV


owlready2.JAVA_EXE = "C:\\Program Files\\Java\\jre1.8.0_291\\bin\\java.exe"
ontoFile2= os.path.join(sys.path[0], "WorldModelLocomotiveVisualPerceptionWithInds.owl")
onto2= get_ontology("file://"+ontoFile2).load()

obligT=[]
propertiesT=[]
valuesT=[]
countT=[]
people= list(onto2.Person.instances())
props= cPV.allPropsOfNode(onto2.Person) # 13 props
obligProps=list(filter (lambda a: onto2.obligatory in a.is_a, props))
obligProps.append(onto2.hasSpeed)
notObligProps= list(filter (lambda a: a not in obligProps, props))

def flatten(lis):
    flat_list = [item for sublist in lis for item in sublist]
    return flat_list

def dealWilProp(string, pr):
    ind= props.index(pr)
    values= list(map(lambda a: pr[a],people))
    uniqueValues= cPV.removeDupl(values)
    for val in uniqueValues:
        obligT.append(string)
        propertiesT.append(pr.name)
        rawStr=str(val)
        if rawStr=='[]':
            rawStr='[none]'
        valStr=rawStr.strip('[').strip(']')
        valuesT.append(valStr)
        count= values.count(val)
        countT.append(count)

for pr in obligProps:
    dealWilProp('obligatory', pr)

for pr in notObligProps:
    dealWilProp('optional',pr)

inds= numpy.linspace(0.01,1,14)
inds2= numpy.linspace(0,1,7)
cMap=list(map(lambda a: mpl.colors.rgb2hex(mpl.cm.Spectral(a)), inds))
cMap2=list(map(lambda a: mpl.colors.rgb2hex(mpl.cm.Spectral(a)), inds2))

def showFigureAllPr():
    df2 = pd.DataFrame(
        dict(obligT=obligT, propertiesT=propertiesT, valuesT=valuesT, countT=countT)
    )
    df2["all"] = "all"
    fig = px.treemap(df2, path=['all','obligT','propertiesT', 'valuesT'], values='countT', color= 'propertiesT', color_discrete_sequence=cMap)
    fig.update_layout(margin = dict(t=0, l=0, r=0, b=0))
    fig.update_traces( marker_line_color='black', selector=dict(type='treemap'))
    fig.show()

def showFigurePoseSpeed():
    poses=[]
    speeds=[]
    for per in people:
        if onto2.hasPose[per]:
            poses.append(str(onto2.hasPose[per]).strip('[').strip(']'))
        if onto2.hasSpeed[per]:
            speeds.append(onto2.hasSpeed[per][0])
    df3=pd.DataFrame({'pose':poses, 'speed': speeds})
    df4= df3.groupby(['speed', 'pose'])['pose'].count()#.reset_index(name='dummy')
    w=df4.unstack()
    ax = w.plot.bar(ylabel= 'count', stacked=True, color=cMap2)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    for container in ax.containers:
        labels = [int(v) if v > 0 else "" for v in container.datavalues]
        ax.bar_label(container,labels=labels, label_type='center')
    ax.plot()
    plt.show()

showFigureAllPr()
showFigurePoseSpeed()
