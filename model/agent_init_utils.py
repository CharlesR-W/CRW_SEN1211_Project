import numpy as np
import random
from ResidentAgent import ResidentAgent
from HospitalAgent import HospitalAgent
from AmbulanceAgent import AmbulanceAgent
def init_agent_batch(model, agent_type_name, unique_id, agent_init_params):
    '''
    Initialise a whole batch of agents of a given type at one time.
    Assumes agent_type_name is the name of the agent class, e.g. "HospitalAgent" and not "hospital"
    '''
    num_agents = agent_init_params["num_agents"]
    #agents = []
    print(f"{agent_type_name} : {num_agents}")
    
    #go from string to the actual class
    cls = globals()[agent_type_name]

    # now init a ton of 'em
    for lv in range(num_agents):
        #create agent
        a = cls(unique_id=unique_id, model=model, agent_init_params=agent_init_params)

        #append to list and add to schedule
        #agents.append(a)
        model.schedule.add(a)

        #append to agent ledger
        model.agents_ledger[unique_id] = a
        
        unique_id += 1

        #assign it a random street location
        location = random.choice(list(model.streets.nodes))
        model.grid.place_agent(a, location)
        a.node_id = location
    
    #return the unique_id as a counter in case someone else needs it
    return unique_id


def init_residents(model, damaged_list, collapsed_list, resident_params, unique_id):
    '''
    Initialises all wounded resident agents, based on a list of collapsed buildings.
    Number of residents in building is pareto distributed.
    '''
    alpha = resident_params["alpha"]
    xm = resident_params["xm"]

    InvCDF = lambda f : xm * (1-f) ** (-1/alpha)
    for building_type in ["damaged", "collapsed"]:
        buildings = damaged_list if building_type == "damaged" else collapsed_list
        for node_id in buildings:
            #draw number of residents in building from pareto distribution
            number_in_building = InvCDF(np.random.uniform())

            #if only damaged, mitigate number of wounded 
            if building_type == "damaged":
                number_in_building *= resident_params["damaged_building_wounded_modifier"]


            number_in_building = int(number_in_building)
            #spawn that many agents
            for _ in range(number_in_building):
                a = ResidentAgent(unique_id=unique_id, model=model, agent_init_params=resident_params)
                model.schedule.add(a)
                model.grid.place_agent(a, node_id)
                a.node_id = node_id
                
                #append unique id to list of all residents
                model.agents_ledger[unique_id] = a

                unique_id += 1

    return unique_id