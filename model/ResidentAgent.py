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
class ResidentAgent(mesa.Agent):
    def __init__(self,unique_id, model, agent_init_params):
        super().__init__(unique_id,model)
        
        self.bleed_time_days = agent_init_params["bleed_time_days"]
        self.heal_time_days = agent_init_params["heal_time_days"]

        self.woundedness = np.random.uniform(low=0.0, high=10)
        self.in_hospital_ambulance = False
        self.target_hospital = None
        self.node_id = None

        #arbitrary scales
        self.min_woundedness = 0.0
        self.max_woundedness = 10.0

    def step(self):
        #print(f"I am agent {self.unique_id} and I am a RESIDENT!")
        if not self.in_hospital_ambulance: 
            self.bleed()
        else:
            #self.heal() #commented since the hospital agent will call heal() instead
            # NB THAT PATIENTS WILL NOT BLEED IN HOSPITALS OR AMBULANCES, EVEN IF NOT HEALING
            return

    def bleed(self):
        self.woundedness += self.model.timestep_days / self.bleed_time_days * (self.max_woundedness - self.min_woundedness)
        if self.woundedness >= self.max_woundedness:
            self.die(bleed_out=True)

    def heal(self):
        #decrease woundedness if hospital has enough beds to treat it
        # HospitalAgent should call this during .step(), NOT this agent
        heal_amount = self.model.timestep_days / self.heal_time_days * (self.max_woundedness - self.min_woundedness)
        self.woundedness -= heal_amount 
        if self.woundedness <= self.min_woundedness:
            self.die(bleed_out=False)
            remit = True
            return remit
        else:
            remit = False
            return remit

    def enter_hospital(self, hospital_agent):
        self.in_hospital_ambulance = True
        self.target_hospital = hospital_agent
        self.model.grid.move_agent(self, hospital_agent.node_id)
        hospital_agent.current_patients_list.append(self.unique_id)

    def enter_ambulance(self):
        self.in_hospital_ambulance = True

    def die(self, bleed_out=False):
        #remove from model lists
        self.model.kill_list.append(self.unique_id)
        if bleed_out:
            self.model.dead_count += 1
        else:
            self.model.healed_count += 1