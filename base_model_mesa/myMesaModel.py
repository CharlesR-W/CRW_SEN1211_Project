#from mesa import Agent, Model
#import mesa.time as time
#import mesa.space as space
#from mesa.datacollection import DataCollector
import mesa
import pickle
import networkx as nx
import matplotlib.pyplot as plt
import random
class myAgent(mesa.Agent):
    def __init__(self,agent_id, model):
        super().__init__(agent_id,model)

    def step(self):
        print(f"I am agent {self.unique_id}!")

class myModel(mesa.Model):
    def __init__(self):
        self.schedule = mesa.time.RandomActivation(self)
        with open('street_network.data', 'rb') as f:
            self.streets = pickle.load(f)

        self.grid = mesa.space.NetworkGrid(self.streets)

        self.num_agents=10

        for lv in range(self.num_agents):
            a = myAgent(lv, self)
            self.schedule.add(a)
            location = random.choice(list(self.streets))
            self.grid.place_agent(a, location)

        model_metrics = {
            "Number of Agents": count_agents
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
        print(f"I have entered step {self.schedule.steps}")
        self.schedule.step()
        self.datacollector.collect(self)

def count_agents(self):
    return self.num_agents


#%%
model = myModel()
for i in range(3):
    model.step()

# Get the Pandas Dataframe from the model, by using the table name we defined in the model
model_data = model.datacollector.get_model_vars_dataframe()
agent_data = model.datacollector.get_agent_vars_dataframe()
print(model_data)
print(agent_data)