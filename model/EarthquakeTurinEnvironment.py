#from mesa import Agent, Model
#import mesa.time as time
#import mesa.space as space
#from mesa.datacollection import DataCollector
import mesa
import pickle
import networkx as nx
import matplotlib.pyplot as plt
import random
import numpy as np
from BuildingSetup import *
from agent_init_utils import *
from HospitalAgent import HospitalAgent
from ResidentAgent import ResidentAgent
from AmbulanceAgent import AmbulanceAgent
from copy import deepcopy

class EarthquakeTurinEnvironment(mesa.Model):
    def __init__(self, my_model_params, DEBUG):
        self.params = my_model_params
        self.DEBUG = DEBUG
        self.timestep_days = self.params["env"]["timestep_days"]
        self.time = 0

        #init schedule
        self.schedule = mesa.time.RandomActivation(self)
        
        #create map and streets
        with open('street_network.data', 'rb') as f:
            self.streets = pickle.load(f)
            self.broken_streets_list = []

        #first buildings initialise, since we must know what streets are broken
        env_params = self.params["env"]
        damaged_buildings, collapsed_buildings = setup_buildings(model=self, env_params=env_params)

        #broken streets can't be used    
        (self.streets).remove_edges_from(self.broken_streets_list)    
        
        #create network grid
        self.grid = mesa.space.NetworkGrid(self.streets)
        self.G = self.streets

        # now start to initialise agents:
        unique_id = 0

        self.agents_ledger = {} # to store agents by id
        self.agent_type_dict_cache = {} #stores agents by type - keys are agent_type_names and values are a dictionary of all agents of that type


        # get a dict of the types of agents we want to init
        agent_types = deepcopy(self.params)
        del agent_types["env"]

        #resident agents are complicated because attached to buildings so we handle separately
        del agent_types["ResidentAgent"]

        # start with the residents, the most complex
        #print("Initialising RESIDENTS: {})
        tmp = unique_id
        
        unique_id = init_residents(model=self, damaged_list=damaged_buildings, collapsed_list=collapsed_buildings,resident_params=self.params["ResidentAgent"], unique_id=unique_id)
        if self.DEBUG:
            print(f"Residents: {unique_id - tmp}\n")

        #initialise all agents of a given, non-ResidentAgent type
        for agent_type_name in agent_types.keys():
            if self.DEBUG:
                print(f"Initialising {agent_type_name}")
            unique_id = init_agent_batch(model=self, agent_type_name=agent_type_name, unique_id=unique_id, agent_init_params=self.params[agent_type_name])

        #any agent who starts at the hospital node gets added to the hospital:
        hospital_node_dict = { v.node_id: v for k,v in self.agents_by_type("HospitalAgent").items()}
        for aid, agent in self.agents_by_type("ResidentAgent.py").items():
            if agent.node_id in hospital_node_dict:
                agent.enter_hospital[hospital_node_dict[agent.node_id]]

        #create list of wounded agents
        self.untreated_wounded = dict(filter(lambda a: not a[1].in_hospital_ambulance, self.agents_by_type("ResidentAgent").items()))

        #once this is done, this is the initial number of agents
        self.num_agents = unique_id

        #number of agents which have bled to death
        self.dead_count = 0
        self.healed_count = 0

        #list of agent ids over which we no longer need to timestep
        self.kill_list = []

        # boilerplate
        model_metrics = {
            "Number Dead": dead_count,
            "Number Healed" : healed_count,
            "Ambulance Occupancy Fraction": ambulance_occupancy_fraction,
            "Hospital Occupancy Fraction": hospital_occupancy_fraction
        }
        agent_metrics = {
            "Agent ID": "unique_id"
        }

        self.datacollector = mesa.DataCollector(
            model_reporters=model_metrics,
            agent_reporters=agent_metrics,
            )
        self.running = True
        self.datacollector.collect(self)

    def step(self):
        if self.DEBUG:
            print(f"BEGINNING STEP {self.schedule.steps} - Elapsed Time (days): {self.time}")

        self.time += self.timestep_days

        

        self.schedule.step()
        if self.DEBUG:
            print("\tStep completed; burying dead")

        self.untreated_wounded = dict(filter(lambda a: not a[1].in_hospital_ambulance, self.agents_by_type("ResidentAgent").items()))

        #remove all 'dead' agents:
        self.bury_dead()
        if self.DEBUG:
            print("\tDead buried; checking stop criteria")

        #Stopping criterion is that no more earthquake victims OR we time out
        wounded = self.agents_by_type("ResidentAgent")
        wounded = dict(filter(lambda a: not a[1].in_hospital_ambulance, wounded.items()))
        if len(wounded) == 0 or self.time > self.params["env"]["max_time_days"]:
            self.running = False
        if self.DEBUG:
            print(f"\tStopping criterion met?: {not self.running}")
            print("\tCollecting data")
        self.datacollector.collect(self)
        if self.DEBUG:
            print("\tData collected")

        return self.running

    def bury_dead(self):
        '''
        Removes 'dead' agents from the timestepping.  'dead' means any agent which no longer needs to be timestepped
        i.e. includes both agents which have died and which have been fully healed
        '''
        for unique_id in self.kill_list:
            try:
                a = self.agents_ledger[unique_id]
            except KeyError:
                continue
            self.grid.remove_agent(a)
            self.schedule.remove(a)
            
            #pop it from both the parent ledger and the cache ledger
            self.agents_ledger.pop(unique_id)
            self.agent_type_dict_cache["ResidentAgent"].pop(unique_id)
        
        self.kill_list = []

    def agents_by_type(self, agent_type_name):
        '''
        Return a list of all unique_ids which corresponds to the specified type name
        '''
        if not agent_type_name in self.agent_type_dict_cache:
            tmp_fil = lambda aid: True if self.agents_ledger[aid[0]].__class__.__name__ == agent_type_name else False
        
        #RHS = dictionary of all agents in the ledger with that class name
            self.agent_type_dict_cache[agent_type_name] = dict(filter(tmp_fil, self.agents_ledger.items()))
        
        # whether it was in the cache or not, it is now - so return it
        return self.agent_type_dict_cache[agent_type_name]

def dead_count(model):
    return model.dead_count

def healed_count(model):
    return model.healed_count

def hospital_occupancy_fraction(model):
    hospitals_dict = model.agents_by_type("HospitalAgent")
    total_capacity = sum([v.total_capacity for k,v in hospitals_dict.items()])
    used_capacity = sum( [len(v.current_patients_list) for k,v in hospitals_dict.items()] )
    return used_capacity / total_capacity

def ambulance_occupancy_fraction(model):
    ambulance_dict = model.agents_by_type("AmbulanceAgent")
    total_capacity = sum([v.total_capacity for k,v in ambulance_dict.items()])
    used_capacity = sum( [len(v.current_patients_list) for k,v in ambulance_dict.items()] )
    return used_capacity / total_capacity