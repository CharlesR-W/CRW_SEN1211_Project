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
class HospitalAgent(mesa.Agent):
    def __init__(self,unique_id, model, agent_init_params):
        super().__init__(unique_id,model)

        self.total_capacity = agent_init_params["total_hospital_capacity"] / agent_init_params["num_agents"] #i.e. divide the 'total capacity' of beds evenly between all hospitals
        self.current_patients_list = []
        self.node_id = None
        

    def step(self):        
        tmp_patients_list = []
        for lv, patient in enumerate(self.current_patients_list):
            if lv >= self.total_capacity: # if we have already done the max number of heals
                remit = False
            else: #if we still have heals left
                try:
                    patient_agent = self.model.agents_ledger[patient]
                except KeyError:
                    continue
                remit = patient_agent.heal()
            
            if not remit: #if patient is not fully healed, they stay
                tmp_patients_list.append(patient)

        #copy the list of who remains in the hospital
        self.current_patients_list = tmp_patients_list

    def has_beds(self):
        if self.total_capacity >= len(self.current_patients_list):
            return True
        else:
            return False