import numpy as np

def setup_buildings(model, env_params):
    '''
    #efined to set up the buildings in the model - we only care about the collapsed ones
    '''
    #p = env_params["building_collapse_probability"]
    num_buildings = env_params["num_buildings"]

    collapsed_list = []
    damaged_list = []

    #select a random node to have a building, and test for if it collapses
    num_nodes = len(model.streets)
    for lv in range(num_buildings):
        n = np.random.randint(low=0,high=num_nodes)
        node_info = model.streets.nodes[n+1]

        #now Idk what the format of this should be....
        x,y = node_info["pos"] #CHECK I _assume_ they're in metres
        x/=1000.0
        y/=1000.0
        xq, yq = env_params["epicenter_xy_km"]
        epicentral_km = np.sqrt((x-xq)**2 + (y-yq)**2)
        
        # returns building status as "safe", "damaged" or "collapsed"
        sdc_outcome = building_collapse_sampler(env_params, epicentral_km)

        if sdc_outcome == "collapsed":
            collapsed_list.append(n)

            # for each road attached to collapsed building, test if it is destroyed
            for edge in model.streets.edges(n):
                if np.random.uniform() <= env_params["road_block_prob"]:
                    model.broken_streets_list.append(edge)
        elif sdc_outcome == "damaged": #NB damaged buildings don't kill roads
            damaged_list.append(n)
        else: # if safe, who cares
            continue

    # return a list of all the buildings which have collapsed
    return damaged_list, collapsed_list

def local_richter_magnitude(M0, epicentral_km):
    '''
    Calculates the equivalent richter magnitude which would generate the same amplitude oscillation at the standard 100km distance
    when compared to the experienced quake.
    '''
    epicentral_km_ref = 100
    Mnew = M0 - 2.76 * np.log(epicentral_km / epicentral_km_ref) /np.log(10) #wikipedia Lillie formula

    return Mnew

def building_collapse_sampler(env_params, epicentral_km):
    '''
    Samples for one building whether it collapses, is damged, or is safe.
    returns a string describing the building state
    '''
    M0 = env_params["earthquake_magnitude"]
    Meff = local_richter_magnitude(M0, epicentral_km)

    Meff *= draw_building_modifiers(env_params)

    vuln_mod = Meff / 10 #* 0.9/0.7 #constructed so that Meff = 10 means 100% chance collapse
    p_collapse = 0.1 + 0.7 * vuln_mod
    p_dam = 0.3 - 0.15*vuln_mod
    p_safe = 0.6 - 0.55*vuln_mod

    p_dist = [p_safe, p_dam, p_collapse]

    outcome_idx = sample_discrete_dist(p_dist)

    outcome = ["safe", "damaged", "collapsed"]

    return outcome[outcome_idx]

def draw_building_modifiers(env_params):
    '''
    Calculates modifier to earthquake magnitude due to building height and material.  Modifier should modify
    the effective richter magnitude felt by the building
    '''
    smt_probs = env_params["building_height_smt_probs"]
    smt_mods = env_params["building_height_smt_modifiers"]
    cbs_probs = env_params["building_material_cbs_probs"]
    cbs_mods = env_params["building_material_cbs_modifiers"]

    mod_smt = smt_mods[ sample_discrete_dist(smt_probs) ]
    mod_cbs = cbs_mods[ sample_discrete_dist(cbs_probs) ]


    modifier = mod_cbs * mod_smt
    return modifier

def sample_discrete_dist(probs):
    '''
    given a discrete pdf as a list of probabilities, draws, and returns the index of the outcome
    '''
    p = np.random.uniform()
    acc = 0
    idx = -1
    while p >= acc:
        idx+=1
        acc += probs[idx]
    return idx    