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
class AmbulanceAgent(mesa.Agent):
    def __init__(self,unique_id, model, agent_init_params):
        super().__init__(unique_id,model)

        # number of people which can fit in the ambulance
        self.total_capacity = agent_init_params["ambulance_capacity"]

        # list of unique_ids currently in transport
        self.current_patients_list = []

        #shouldn't start out queueing
        self.work_complete = False

        self.speed_ms = agent_init_params["speed_ms"]

        # where is the ambulance going
        self.target_node = None

        # percent travelled along this current road
        self.route_completion = None # list of percentages, should be [x,0,0,0....]
        self.current_route = None # list of nodes connected by edges
        
        #self.target_nearest_wounded() # initialise
        self.first_step = True

        # Number of nodes the ambulance chooses to search for wounded at
        self.pathfinding_candidates = agent_init_params["ambulance_pathfinding_nodes_cutoff"]

    def step(self):

        #if you're done, dont waste compute
        if self.work_complete:
            return

        #CHECK the logic of arrive / work_complete - make sure that there's no way a patient gets left behind
        if self.first_step:
            self.target()
            self.first_step = False

        # move along road if we have a route/target
        if self.current_route is not None:
            arrives = self.drive()
        elif self.carrying_wounded():  #if we have no route, but are carrying wounded, check for a hospital again
            self.target_nearest_hospital()
            if self.current_route is None: # if still no hospitals, break
                return
            else: #else if you did find a hospital this time, go
                arrives = self.drive()
        else: #if you have no path and aren't carrying agents, die
            self.work_complete = True
            return
            
        
        #if it gets where its going
        if  arrives and self.carrying_wounded(): # if it has wounded, assume its going to a hospital
            self.drop_wounded()
        elif arrives and not self.carrying_wounded(): #if not carrying wounded, assume its going to find them
            self.pickup_wounded()

        #now target
        if self.current_route is None:
            self.target_node=None
            self.target()

    def drive(self):
        '''
        Simulate agent driving down a road
        '''
        days_to_seconds = 24*60*60.
        metres_travelled = self.speed_ms * self.model.timestep_days * days_to_seconds

        #if self.is_waiting:
        #    return
        
        #see how much is left on this leg of road
        if len(self.current_route) == 1:
            arrives = True
            self.node_id = self.current_route[-1]
            self.current_route = None
            self.route_completion = None
            return arrives
        else:
            next_leg = (self.current_route[0],self.current_route[1])
            leg_completion = self.route_completion[0]
            leg_remaining_m = (1-leg_completion) * self.model.streets.edges[next_leg]["Length"]
        
        # if we pass onto a new road,
        while metres_travelled >= leg_remaining_m:
            #if this is the last leg we're about to complete

            #otherwise onto the next leg
            #remove the completed leg
            self.current_route = self.current_route[1:]
            self.route_completion = self.route_completion[1:]

            metres_travelled -= leg_remaining_m

            if len(self.current_route) == 1:
                        arrives = True
                        self.node_id = self.current_route[-1]
                        self.current_route = None
                        self.route_completion = None
                        return arrives

            next_leg = (self.current_route[0], self.current_route[1])
            leg_completion = self.route_completion[0]
            leg_remaining_m = (1-leg_completion) * self.model.streets.edges[next_leg]["Length"]
            self.node_id = self.current_route[0]

        self.route_completion[0] = metres_travelled / leg_remaining_m

        self.node_id = self.current_route[0] # MAKE SURE THIS IS A NODE NUMBER

        self.change_nodes() #finalise the result fo the drive action by moving to a node

        arrives = False
        return arrives

    def change_nodes(self):
        '''
        Move agent and all patients to the nearest node after driving
        '''
        new_node = self.node_id
        #move self
        self.model.grid.move_agent(self, new_node)

        #move all child agents
        for aid in self.current_patients_list:
            try:
                a = self.model.agents_ledger[aid]
                self.model.grid.move_agent(a, new_node)
            except:
                continue

    def carrying_wounded(self):
        if len(self.current_patients_list) > 0:
            return True
        else:
            return False
    
    def drop_wounded(self):  
        #print("[AmbulanceAgent] Dropping off wounded")   
        for aid in self.current_patients_list:
            try:
                agent = self.model.agents_ledger[aid]
                agent.enter_hospital(self.target_hospital)
            except KeyError:
                pass
                #if self.DEBUG
                    #print("[AmbulanceAgent: Error] Invalid Key in self.current_patients_list")

        self.current_patients_list = []
            
        self.target_hospital = None

    def pickup_wounded(self):
        #print("[AmbulanceAgent] Picking up wounded")
        #CHECK arg of the function below
        #NB that we dont check if in treatment, since this place shouldn't be a hospital
        wounded_here = dict(filter(lambda a: a[1].node_id==self.node_id, self.model.untreated_wounded.items()))
        for aid,a in wounded_here.items():
            if len(self.current_patients_list) >= self.total_capacity:
                break
            else:
                self.current_patients_list.append(a.unique_id)
                a.enter_ambulance()

        
    def get_targets_list(self):
        '''
        Return a list of node_ids for which there is a valid target there (hospital or wounded)
        '''
        if self.carrying_wounded():
            hospitals = self.model.agents_by_type("HospitalAgent")
            usable_hospitals = dict(filter(lambda a: a[1].has_beds(), hospitals.items())) # CHECK
            target_nodes = set([a[1].node_id for a in usable_hospitals.items()])
        else:
            if len(self.model.untreated_wounded) == 0: # if not carrying wounded AND no untreated_wounded left, die
                self.work_complete = True
                return
            target_nodes = set([a[1].node_id for a in self.model.untreated_wounded.items()])
        target_nodes = list(target_nodes)
        return target_nodes

    def target(self):
        target_nodes = self.get_targets_list()
        if target_nodes is None:
            return

        #choose a random subset of these to search - using all of them is way too many
        if self.pathfinding_candidates < len(target_nodes):
            target_nodes = np.random.choice(target_nodes,size=self.pathfinding_candidates)

        best_dist = float("inf")
        for t in target_nodes: #select N:
            try:
                dist, path = nx.single_source_dijkstra(G=self.model.streets, source=self.node_id, target=t)
            except nx.NodeNotFound:
                #print("invalid node")
                continue
            except nx.NetworkXNoPath:
                #print("Not connected")
                continue

            if dist < best_dist:
                best_dist = dist
                best_path = path
                self.target_node = t

        if self.carrying_wounded():
            try:
                self.target_hospital = list(filter(lambda a: a[1].node_id==self.target_node, self.model.agents_by_type("HospitalAgent").items() ))[0][1]
            except:
                pass
                #print("")
            
        try:
            #keep track of the edges to follow
            self.current_route = best_path
            #entries are % of distance travelled along each edge in the path
            self.route_completion = [0 for _ in self.current_route]
        except:
            return