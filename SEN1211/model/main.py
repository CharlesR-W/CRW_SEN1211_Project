from sacred import Experiment
from copy import deepcopy
from EarthquakeTurinEnvironment import EarthquakeTurinEnvironment
import mesa
from mesa.visualization.modules.NetworkVisualization import NetworkModule
import networkx

ex = Experiment('EarthquakeTurinABM_Default')

#number of people in the city
turin_population = 9e5 #googled somewher

turin_radius_km = 11 #calculated from wikipedia

#number of overall hospital beds per person (based on countrywide data)
italy_beds_per_capita = 31.4/1e4 #WHO data

#cities presumably have a higher effective density of hospital beds due to economies of scale: increase the above by this factor
urban_factor = 1.5

italy_ambulance_per_capita = 1.0 / 51e3 #website says

#decrease ambulances, buildings, and hospital capacity by this amount - population changes with building number
simulation_scale_factor = 1/5 #NB doesn't change ambulance _capacity_!

#percent of people wounded in any way by the Earthquake
earthquake_casualty_rate = 0.10 #idk made it up

turin_large_buildings = 300 #mexico city had 2080 (wikipedia), and has about 10x pop; 300 since Western Europe GDPPc>Mexico

building_collapse_percent = 44 / 2080 #44 collapses in MC, compared to num highrises, MSNBC article

hospital_init_params = {
    "num_agents"            : 10, #CTO Turin
    "total_hospital_capacity"     : int(italy_beds_per_capita * turin_population * urban_factor * simulation_scale_factor),
}

pareto_alpha = 1.16 #corresponds to the famous "80-20" rule
resident_init_params = {
    "alpha"                             : pareto_alpha, #alpha in pareto distribution
    "xm"                                : simulation_scale_factor * turin_population * (1- 1/pareto_alpha) / turin_large_buildings,   #scale factor for Pareto distn - should be something like the average number of people per building
                                                                                                            #a bit slopppy since I want num_buildings draws from the distn to have expected value of turin_pop, but this is close enough I think
    "bleed_time_days"                   : 6/24.0, #six hours to die
    "heal_time_days"                    : 2/24.0, #two hours to heal
    "damaged_building_wounded_modifier" : 0.1 #the fraction of wounded caused by a damaged building compared to a collapsed one
}

ambulance_init_params = {
    "num_agents"        : int(italy_ambulance_per_capita * turin_population * urban_factor * simulation_scale_factor), #EXPT
    "speed_ms"          : 30,
    "ambulance_capacity" : 3,
    "ambulance_pathfinding_nodes_cutoff" : 20, # number of searches an ambulance will perform for nearby victims - i.e. look at 100 and choose the closest, rather than look at all of them - for computational ease.
}

minutes_to_days = 1/(60*24)
env_init_params = {
    "earthquake_magnitude"          : 6, #richter scale
    "epicenter_xy_km"               : (-50,-50), #distance in km
    "city_radius"                   : turin_radius_km,
    "num_buildings"                 : turin_large_buildings,
    "timestep_days"                 : 5 * minutes_to_days, # = minutes
    "road_block_prob"               : 0.1, #prob for _each_ road attached to a building to be blocked
    "building_material_cbs_probs"   : [0.5, 0.3, 0.2], #prob that a building is specific material, cbs = concrete, brick, steel
    "building_material_cbs_modifiers" : [0.5, 1.0, 0.2], #modifier of richter mag. corresponding to specific material 
    "building_height_smt_probs"     : [0.5, 0.4, 0.1], #prob of building being a specific height; smt = short, medium, tall
    "building_height_smt_modifiers" : [0.2, 0.6, 1.0], #modifier of richter mag corresponding to building height
    "max_time_days"             : 3 
}

#compress everythin for ease of use
default_param_dict = {
    "HospitalAgent"     : hospital_init_params,
    "ResidentAgent"     : resident_init_params,
    "AmbulanceAgent"    : ambulance_init_params,
    "env"               : env_init_params
}

#env = EarthquakeTurinEnvironment(params)
#vis_grid = mesa.visualization.NetworkModule(portrayal_method=grid_portrayal)
chart1 = mesa.visualization.ChartModule([{"Label": "Number Dead",
                  "Color": "Black"}],
                data_collector_name='datacollector')
chart2 = mesa.visualization.ChartModule([{"Label": "Number Healed",
                  "Color": "Black"}],
                  data_collector_name='datacollector')
chart3 = mesa.visualization.ChartModule([{"Label": "Ambulance Occupancy Fraction",
                  "Color": "Black"}],
                  data_collector_name='datacollector')
chart4 = mesa.visualization.ChartModule([{"Label": "Hospital Occupancy Fraction",
                  "Color": "Black"}],
                  data_collector_name='datacollector')

server = mesa.visualization.ModularServer(EarthquakeTurinEnvironment,
                   [chart1,chart2,chart3,chart4],
                   "TurinEarthquake",
                   {"params":default_param_dict}) #this is the dumbest initialisation thing ive ever seen
server.port = 8521 # The default
server.launch()
'''
@ex.config
def cfg():
    params = deepcopy(default_param_dict)
    #change anything here

@ex.automain
def run(params):
    #env = EarthquakeTurinEnvironment(params)
    #vis_grid = mesa.visualization.NetworkModule(portrayal_method=grid_portrayal)
    chart1 = mesa.visualization.ChartModule([{"Label": "Number Dead",
                      "Color": "Black"}],
                    data_collector_name='datacollector')
    chart2 = mesa.visualization.ChartModule([{"Label": "Number Healed",
                      "Color": "Black"}],
                      data_collector_name='datacollector')
    chart3 = mesa.visualization.ChartModule([{"Label": "Ambulance Occupancy Fraction",
                      "Color": "Black"}],
                      data_collector_name='datacollector')
    chart4 = mesa.visualization.ChartModule([{"Label": "Hospital Occupancy Fraction",
                      "Color": "Black"}],
                      data_collector_name='datacollector')
    
    server = mesa.visualization.ModularServer(EarthquakeTurinEnvironment,
                       [chart1,chart2,chart3,chart4],
                       "TurinEarthquake",
                       {"params":params}) #this is the dumbest initialisation thing ive ever seen
    server.port = 8521 # The default
    server.launch()
'''