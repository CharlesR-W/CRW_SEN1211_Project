#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 27 10:52:02 2023

@author: crw
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

filedir = "/home/crw/Programming/SEN1211/"
var_list = ['Number Dead','Number Healed','Ambulance Occupancy Fraction', 'Hospital Occupancy Fraction']
new_var_list = var_list + ["Fraction Dead", "Fraction Saved"]
timestep_min = 5
def myfilter(results):    
    tmp = []
    seen = []
    lv=0
    for lv in range(len(results)):
        time = (results[lv]["iteration"], results[lv]["Step"])
        if not time in seen:
            seen.append(time)
            obs = {x : results[lv][x] for x in var_list}
            tmp.append((time,obs))
    return tmp

def make_run_data(data):
    max_time = max([x[0][1] for x in data])
    num_its = max([x[0][0] for x in data])+1
    
    run_data = { (r,x) : [] for x in var_list for r in range(num_its)}
    
    lv=0
    lv_it=0
    while lv < len(data):
        next_data = data[lv]
        next_it = next_data[0][0]
        lv_it = next_it
        
        for x in var_list:
            run_data[(lv_it, x)] += [next_data[1][x]]
        lv += 1
    
    return run_data

def dead_and_healed(run_data):
    num_its = len(run_data) // len(var_list)
    for lv_it in range(num_its):
        total_people = run_data[lv_it,'Number Dead'][-1] + run_data[lv_it,'Number Healed'][-1]
        new_dead = np.array( run_data[ (lv_it,'Number Dead') ] ) / total_people
        new_saved = np.array( run_data[ (lv_it,'Number Healed') ] ) / total_people
        
        run_data[(lv_it,"Fraction Dead")] = list(new_dead)
        run_data[(lv_it,"Fraction Saved")] = list(new_saved)

def my_plots(run_data):

    max_time = max( [len(x) for x in run_data.values()] )
    num_its = len(run_data) // len(new_var_list)
    
    avg = {x:[] for x in new_var_list}
    std = {x:[] for x in new_var_list}
    
    for lv_t in range(max_time):
        for x in new_var_list:
            tmp = []
            for lv_it in range(num_its):
                try:
                    tmp.append( run_data[ (lv_it, x) ][lv_t] )
                except IndexError:
                    continue
            avg[x].append( np.mean(tmp) )
            std[x].append( np.std(tmp) )
    
    avg = {x : np.array(avg[x]) for x in avg.keys()}
    std = {x : np.array(std[x]) for x in std.keys()}
    
    #now start plotting
    fig,axs = plt.subplots(nrows=4,ncols=1,sharex=True,layout="constrained")
    time = np.linspace(0,max_time*timestep_min, max_time)
    for lv,x in enumerate(new_var_list[2:]):
        axs[lv].plot(time , avg[x])
        axs[lv].fill_between(time ,avg[x]+std[x], avg[x]-std[x],alpha=0.3)
        axs[lv].set_title(x)
        axs[lv].set_ylim([0,1])
        
    
    fig.supxlabel("Time (min)")
    
    print(f"{avg['Fraction Saved']}")
    print(f"{avg['Fraction Dead']}")
    print(f"{np.mean(avg['Hospital Occupancy Fraction'])}")
    print(f"{np.mean(avg['Ambulance Occupancy Fraction'])}")
    
    assert False
    
    return fig,axs

def final_plotter(results):
    data = myfilter(results)
    
    run = make_run_data(data)
    dead_and_healed(run)
    
    #assert False
    
    fig,axs = my_plots(run)
    return fig,axs

#%%
results = pd.read_pickle(filedir + "base_results.pickle")
fig,axs = final_plotter(results)

#%%
results = pd.read_pickle(filedir + "fast_heal_results.pickle")
fig,axs = final_plotter(results)

#%%
results = pd.read_pickle(filedir + "tenx_hospitals_results.pickle")
fig,axs = final_plotter(results)

#%%
tmp=[]
for lv in range(5):
    tmp += [((lv, x[0][1]),x[1]) for x in myfilter( pd.read_pickle(filedir + f"tenx_ambulances_results_{lv}.pickle") ) ]
tenx_ambulances_data = tmp

#results = pd.read_pickle(filedir + "tenx_ambulances_results.pickle")
#%%
fig,axs = final_plotter(tenx_ambulances_data)