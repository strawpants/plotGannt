#!/usr/bin/env python
# coding: utf-8

# # Make a Gantt plot 
# 
# Author: Roelof Rietbroek,  18 December 2019
# inspired [by](https://sukhbinder.wordpress.com/2016/05/10/quick-gantt-chart-with-matplotlib/)


import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import matplotlib.dates
from matplotlib.dates import num2date,date2num,YEARLY,WEEKLY,MONTHLY, DateFormatter, rrulewrapper, RRuleLocator, datestr2num, MonthLocator,YearLocator
from dateutil.parser import ParserError
import numpy as np
import re
import collections
from yaml import safe_load as yamlload
import sys
import argparse
import locale

Task=collections.namedtuple("Task","name slots color")

MileStone=collections.namedtuple("MileStone","name epoch color linewidth fontsize")

def conv2date(dtstr,tstart=None):
    """Convert epoch string or time interval to matplotlib date"""
    #we possibly have a timeinterval  as input so wrap in exception block
    try:
        dout=datestr2num(dtstr)
    except ParserError as e:
        if not tstart:
            raise RuntimeError("cannot parse relative times without specifying tstart in the tasks file")
        #try interpreting this as an interval length (in days or months)
        m=re.search("\+([0-9]+)([dm])",dtstr)
        if not m:
            raise RuntimeError("Cannot parse relative time string: use +XXXd or +XXm") 
        if m.group(2) == "m":
            dt=30.5*float(m.group(1)) #scale with average days per month
        elif m.group(2) == "d":
            dt=float(m.group(1))
        
        dout=tstart+dt
    return dout

def readTasksMilestones(yamlfile):
    with open(yamlfile,"rt") as fid: 
        yatasks=yamlload(fid)

    #check if a starting time is present (this will allow relative time indicators)
    if "tstart" in yatasks:
        tstart=datestr2num(yatasks["tstart"])
    else:
        tstart=None

     #put the tasks in an ordered dict
    tasks=[]
    for ky,task in yatasks["Tasks"].items():
        slot=[]
        for period in task["periods"]:
            slot.append((conv2date(period[0],tstart),conv2date(period[1],tstart)))
        if "longname" in task:
            name=task["longname"]
        else:
            name=ky
        tasks.append(Task(name=name,slots=slot,color=task["color"]))
    milestones=[]
    for ky,milestone in yatasks["Milestones"].items():
        if "color" in milestone:
            color=milestone["color"]
        else:
            color="black"
        if "linewidth" in milestone:
            linewidth=milestone["linewidth"]
        else:
            linewidth=4

        if "fontsize" in milestone:
            fontsize=milestone["fontsize"]
        else:
            fontsize=24
        
        if "longname" in milestone:
            name=milestone["longname"]
        else:
            name=ky
        milestones.append(MileStone(name=name,epoch=conv2date(milestone["epoch"],tstart),color=color,linewidth=linewidth,fontsize=fontsize)) 

    return tasks,milestones

def plotGantt(args):
    tasks,milestones=readTasksMilestones(args.taskfile)
    fsize=24

    width=20
    height=20/args.ratio
    fig=plt.figure(figsize=(width,height))
    ylabels=[]
    pos=[]
    myFmt = DateFormatter('%b %Y')
    # myFmt = DateFormatter('%Y')
    if args.locale:
        locale.setlocale(locale.LC_ALL,args.locale)
   
    ax = fig.add_subplot(111)
    yval=len(tasks)
    axlim=[sys.float_info.max,sys.float_info.min]
    for task in tasks:
        for st,nd in task.slots:
            ax.barh(yval,width=nd-st,height=0.9,left=st,color=task.color)
            axlim[0]=min(axlim[0],st)
            axlim[1]=max(axlim[1],nd)
        ylabels.append(task.name)
        pos.append(yval)
        yval-=1
    ax.set_xlim(axlim)

    #also plot Milestones
    for milestone in milestones:
        ytop=1.02*ax.get_ylim()[1]
        ax.axvline(milestone.epoch,ymax=1.02,clip_on=False,color=milestone.color,linewidth=milestone.linewidth,marker="o",markersize=3*milestone.linewidth,markevery=[1])
        #make a label
        ax.text(milestone.epoch,ytop,milestone.name,fontsize=milestone.fontsize,color=milestone.color,rotation=45)
    ax.xaxis.set_major_formatter(myFmt)
    #rule = rrulewrapper(MONTHLY, interval=3)
    # rule = rrulewrapper(YEARLY, interval=1)
    # loc = RRuleLocator(rule)
    hyrloc= MonthLocator((1,7))
    qloc= MonthLocator((1,4,7,10))
    ax.xaxis.set_major_locator(hyrloc)
    ax.xaxis.set_minor_locator(qloc)
    labelsx = ax.get_xticklabels()
    plt.setp(labelsx, rotation=45, fontsize=fsize)
    locsy, labelsy = plt.yticks(pos,ylabels)
    plt.setp(labelsy, fontsize = fsize)
    ax.grid(color = 'grey',which='major', linestyle = '-')
    ax.grid(color = 'grey', which='minor',linestyle = ':')

    plt.tight_layout()

    plt.savefig(args.output)
    


def main(argv):# plot

    usage=" Make a Gannt plot from the tasks in a configuration file"
    parser = argparse.ArgumentParser(description=usage,formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('taskfile', metavar='YAMLTASKFILE', type=str, nargs='?',
                    help='Specify the inputfile for the tasks (default is tasks.yml)',default="tasks.yml")
    
    parser.add_argument('-o','--output', metavar='OUTPUTFILE', type=str,
                    help='Specify the output graphicsfile (e.g. Gannt.svg(default), Gannt.png or Gannt.pdf),',default="Gannt.svg")
    
    parser.add_argument('-l','--locale', metavar='LOCALE', type=str,
                    help='Set the locale used for formatting dates e.g. (de_DE), defaults to en_US',default="en_US.utf-8")
    
    parser.add_argument('-r','--ratio', metavar='ASPECTRATIO', type=float,
            help='Specify the aspect ratio (w/h as a float)  of the plot, defaults to 16:9',default=16/9)
    
    # parser.add_argument('-q','--quarterly', default=False,action='store_true',
            # help='Make a plot which has esily recognizable quaterlies')

    # parser.add_argument('
    
    args=parser.parse_args(argv[1:]) 
    
    plotGantt(args)

if __name__ == "__main__":
    main(sys.argv)

