import pandas as pd
from ortools.linear_solver import pywraplp
import copy
from itertools import combinations



def task1(d):
    """
    Given supply chain information provided in accompanied data. Minimize the overall cost

    Parameters
    ----------
    d : Pandas DF
        Supply chain data.

    Returns
    -------
    None.

    """
    
    print('\n'+'-'*40)
    print('\t\t\t\tTask 1')
    print('-'*40+'\n')
    
    print_results = False
    
    #Part A. Load data
    supplier_stock = d['Supplier stock']
    raw_materials = d['Raw material costs']
    raw_material_shipping = d['Raw material shipping']
    product_requirements = d['Product requirements']
    production_capacity = d['Production capacity']
    production_cost = d['Production cost']
    customer_demand = d['Customer demand']
    shipping_costs = d['Shipping costs']
    
    # Part B. Create decision variables    
    solver = pywraplp.Solver('LPWrapper', pywraplp.Solver.GLOP_LINEAR_PROGRAMMING)
    
    # Part B: Decision variables
    orders_from_supplier = {}
    production_volume = {}
    delivery_customers = {}
    suppliers = supplier_stock.index.values
    materials = supplier_stock.columns.values
    factories = shipping_costs.index.values
    products = customer_demand.index.values
    customers = customer_demand.columns.values 

                        
    # Part B (i): Orders from suppliers - For each Supplier/Factory/Material combination create decision variable
    for s in suppliers:
        for m in materials:
            for f in factories:
                if not str(supplier_stock.loc[s,m]) == 'nan':
                    orders_from_supplier[s+'_'+m+'_'+f] = solver.NumVar(0, solver.infinity(),s+'_'+m+'_'+f)
    
    
    # Part B (ii): Production Volume - For each Factory/Product combination create decision variables
    for f in factories:
        for p in products:
            if not str(production_capacity.loc[p,f]) == 'nan':
               production_volume[f+'_'+p] = solver.NumVar(0, solver.infinity(), f+'_'+p)
                        
                    
   # Part B (iii): Delivery to customers - For each Factory/Customer/Product combination create a decision variable                                    
    for c in customers:
        for p in products:
            for f in factories:
                if not str(production_capacity.loc[p,f]) == 'nan' and not str(customer_demand.loc[p,c]) == 'nan':
                    delivery_customers[c+'_'+p+'_'+f] = solver.NumVar(0, solver.infinity(), c+'_'+p+'_'+f) 
                
                    
    # Part C: Implement constraints that ensures factories produce more than they ship to customers                        
    customer_requirement = customer_demand.sum(axis=1)
    for p in products:
        constraint = solver.Constraint(customer_requirement.loc[p],  solver.infinity())
        for f in factories:
            if not str(production_capacity.loc[p,f]) == 'nan':
                constraint.SetCoefficient(production_volume[f+'_'+p], 1)
                                
                
    # Part D. Implements constraints that ensure customer demands are met
    for c in customers:
        for p in products:
            if not str(customer_demand.loc[p,c]) == 'nan':       
                constraint = solver.Constraint(customer_demand.loc[p,c], solver.infinity())
                for f in factories:
                    if not str(production_capacity.loc[p,f]) == 'nan':
                        constraint.SetCoefficient(delivery_customers[c+'_'+p+'_'+f], 1)
                    
                        
    # Part E. Implement constraints that suppliers have all ordered items in stock
    for s in suppliers:
        for m in materials:
            if not str(supplier_stock.loc[s,m])== 'nan':
                constraint = solver.Constraint(0, supplier_stock.loc[s,m])
                for f in factories:
                    constraint.SetCoefficient(orders_from_supplier[s+'_'+m+'_'+f], 1)


    
    # Part F. Ensure factories order enough material to be able to manufacture all items     
    material_requirements = {}
    # First determine how much material is required accross the board to fulfil all customers demands
    for m in materials:
        if m not in material_requirements.keys():
            material_requirements[m] = 0
        for p in products:
            if not str(product_requirements.loc[p,m]) == 'nan':
                material_requirements[m] += customer_requirement[p]*product_requirements.loc[p,m]

    
    # Implement constraints that the material requirements are satisfied accross all factories
    for m in materials:
        constraint = solver.Constraint(material_requirements[m], solver.infinity())
        for s in suppliers:
            for f in factories:
                if not str(supplier_stock.loc[s,m])== 'nan':
                    for p in products:
                        if not str(product_requirements.loc[p,m]) == 'nan' and not str(production_capacity.loc[p,f]) == 'nan':
                            constraint.SetCoefficient(orders_from_supplier[s+'_'+m+'_'+f], 1) 

    # If a factory is producing product it is also shipping it to customer
    for f in factories:
        for p in products:
            if not str(production_capacity.loc[p,f]) == 'nan':
                constraint = solver.Constraint(0,0)
                constraint.SetCoefficient(production_volume[f+'_'+p], 1)
                for c in customers:
                    if not str(customer_demand.loc[p,c]) == 'nan':
                        constraint.SetCoefficient(delivery_customers[c+'_'+p+'_'+f], -1)
                        
                        
    # If a factory is producing a product it is ordering the required material
    for f in factories:
        for m in materials:
            constraint = solver.Constraint(0,0)
            for p in products:
                if not str(production_capacity.loc[p,f]) == 'nan' and not str(product_requirements.loc[p,m]) == 'nan' :
                    constraint.SetCoefficient(production_volume[f+'_'+p], product_requirements.loc[p,m])
                    for s in suppliers:
                        if not str(supplier_stock.loc[s,m]) == 'nan':
                            constraint.SetCoefficient(orders_from_supplier[s+'_'+m+'_'+f], -1)


    # Part G. Implement constraints that all manufacturing capacities are not exceeded
    for f in factories:
        for p in products:
            if not str(production_capacity.loc[p,f]) == 'nan':
                constraint = solver.Constraint(0, production_capacity.loc[p,f])
                for c in customers:
                    if not str(customer_demand.loc[p,c]) == 'nan':
                        constraint.SetCoefficient(production_volume[f+'_'+p], 1)
  
   
    
    # Part H. Define object function - including shipping & material costs - production cost - delivery cost
    cost = solver.Objective()
                                                      
    # Part H (i): Material Cost
    for s in suppliers:
        for m in materials:
            for f in factories:
                if not str(supplier_stock.loc[s,m]) == 'nan':
                    cost.SetCoefficient(orders_from_supplier[s+'_'+m+'_'+f] , float(raw_materials.loc[s,m]))
                    cost.SetCoefficient(orders_from_supplier[s+'_'+m+'_'+f] , float(raw_material_shipping.loc[s,f]))               
    
            
    # Part H (ii): Production Cost
    for f in factories:
        for p in products:
            for m in materials:
                if not str(production_capacity.loc[p,f]) == 'nan' and not str(product_requirements.loc[p,m]) == 'nan':
                    cost.SetCoefficient(production_volume[f+'_'+p], float(production_cost.loc[p,f]))
                 
                
    # Part H (iii): Delivery to each customer cost
    for c in customers:
        for p in products:
            for f in factories:
                if not str(production_capacity.loc[p,f]) == 'nan' and not str(customer_demand.loc[p,c]) == 'nan':
                    cost.SetCoefficient(delivery_customers[c+'_'+p+'_'+f], float(shipping_costs.loc[f,c]))
                        
    cost.SetMinimization()
    

    # Part I. Solve linear program
    solver.Solve()
    total_cost = 0   
    

    for s in suppliers:
        for m in materials:
            for f in factories:
                if not str(supplier_stock.loc[s,m]) == 'nan':
                    total_cost += orders_from_supplier[s+'_'+m+'_'+f].solution_value() * float(raw_materials.loc[s,m])
                    total_cost += orders_from_supplier[s+'_'+m+'_'+f].solution_value() * float(raw_material_shipping.loc[s,f])

            
    # Part H (ii): Production Cost
    for f in factories:
        for p in products:
            if not str(production_capacity.loc[p,f]) == 'nan':
                total_cost += production_volume[f+'_'+p].solution_value() * float(production_cost.loc[p,f])
         
                  
    # Part H (ii): Cost of delivery                                  
    for c in customers:
        for p in products:
            for f in factories:
                if not str(production_capacity.loc[p,f]) == 'nan' and not str(customer_demand.loc[p,c]) == 'nan':
                    total_cost += delivery_customers[c+'_'+p+'_'+f].solution_value() * float(shipping_costs.loc[f,c])
                  
                
    print("Total Optimal Cost: ", total_cost)
    

    # Part J. Determine how much material to be ordered from each supplier
    print('\nPart J. How much material is ordered from each supplier')
    f_s_m = {}
    for f in factories:
        f_s_m[f] = {}
        for s in suppliers:
            f_s_m[f][s] = {}
            for m in materials:
                if not str(supplier_stock.loc[s,m]) == 'nan':
                    f_s_m[f][s][m] = orders_from_supplier[s+'_'+m+'_'+f].solution_value()
                
    for f in factories:
        for s in f_s_m[f].keys(): 
            for m in f_s_m[f][s].keys():
                if int(f_s_m[f][s][m]) > 0:
                    print('{} has to order {} of {} from {}'.format(f, int(f_s_m[f][s][m]), m, s))
      
    

    # Part K. Determine for each factory supplier bill for material and delivery
    # For each factory - supplier combination, compute total bill including raw materials and delivery charges
    print('\nPart K. Bill for materials and delivery for each factory')
    
    f_bill = {}         
    for f in factories:
        f_bill[f] = {}
        for s in suppliers:
            f_bill[f][s] = 0
            for m in materials:
                if not str(supplier_stock.loc[s,m]) == 'nan':
                    f_bill[f][s] += orders_from_supplier[s+'_'+m+'_'+f].solution_value()*float(raw_material_shipping.loc[s,f])
                    f_bill[f][s] += orders_from_supplier[s+'_'+m+'_'+f].solution_value()*float(raw_materials.loc[s,m])


    for f in factories:
        for s in f_bill[f].keys():
            if  int(f_bill[f][s]) == 0:
                continue
            print("{} total bill from {} is {}".format(f, s, int(f_bill[f][s])))
    
                
    # Part L. Determine number of products manufactured by each factory and total manufacturing cost
    # For each factory/product compute number produced
    print('\nPart L. Number of units being manufactured by each factory')
    
    f_total_cost = {}
    f_p = {}
    
    for f in factories:
        f_total_cost[f] = 0
        f_p[f] = {}
        for p in products:
            f_p[f][p] = 0
            if not str(production_capacity.loc[p,f]) == 'nan':
                f_p[f][p] += production_volume[f+'_'+p].solution_value() 
                f_total_cost[f] += production_volume[f+'_'+p].solution_value() * production_cost.loc[p,f]
                        

    for f in factories:
        for p in f_p[f].keys():
            if int(f_p[f][p]) == 0:
                continue
            print('{} manufactures {} of {}'.format(f, int(f_p[f][p]), p))
    
            
    
    print('\nPart L (ii): Total manufacturing cost for each factory')
    for f in factories:
        print('{} total manufacturing cost is {}'.format(f, f_total_cost[f]))
        

    # Part M. For each customer determine how many units are being manufactured at each factory and shipping cost for customers
    print('\nPart M (i): Units being shipped to customers from each factory') 
    
    c_u = {}    # Customer units shipped
    c_sc = {}   # Customer shipping cost
    
    for c in customers:
        c_u[c] = {}
        c_sc[c] = 0
        for f in factories:
            c_u[c][f] = {}
            for p in products:
                if not str(production_capacity.loc[p,f]) == 'nan' and not str(customer_demand.loc[p,c]) == 'nan':
                    c_u[c][f][p] = delivery_customers[c+'_'+p+'_'+f].solution_value()
                    c_sc[c] += delivery_customers[c+'_'+p+'_'+f].solution_value() * float(shipping_costs.loc[f,c])
                    

    for c in customers:
        for f in c_u[c].keys():
            for p in c_u[c][f].keys():
                if int(c_u[c][f][p]) == 0:
                    continue
                print('{} is being shipped {} of {} from {}'.format(c, int(c_u[c][f][p]), p, f))

    print('\nPart M (ii): Total shipping cost for each customer')
    for c in customers:
        print("Total shipping cost for {} is {}".format(c, c_sc[c]))
        
    
    # Part N [i]. Determine fraction of each material each factory has to order for each customer
    print('\nPart N (i): Fraction of material each factory has to make per customer')
    
    cmf = {}
    total_m = {}
    for c in customers:
        cmf[c] = {}
        total_m[c] = {}
        for m in materials:
            cmf[c][m] = {}
            total_m[c][m] = 0
            for f in factories:
                if f not in cmf[c][m].keys():
                    cmf[c][m][f] = 0
                for s in suppliers:
                    for p in products:
                        if not str(supplier_stock.loc[s,m]) == 'nan' and not str(product_requirements.loc[p,m]) == 'nan' and \
                        not str(production_capacity.loc[p,f]) == 'nan' and not str(customer_demand.loc[p,c]) == 'nan':
                            cmf[c][m][f] += orders_from_supplier[s+'_'+m+'_'+f].solution_value()
                            total_m[c][m] += orders_from_supplier[s+'_'+m+'_'+f].solution_value()

    cmf_fract = {}
    for c in customers:
        cmf_fract[c] = {}
        print(c)
        for m in cmf[c].keys():
            cmf_fract[c][m] = {}
            for f in cmf[c][m].keys():
                pass
                try:
                    fraction = cmf[c][m][f]/total_m[c][m]
                    cmf_fract[c][m][f] = fraction
                except ZeroDivisionError:
                    continue
                if fraction == 0.0:
                    continue
                print('\t- {} has to order {}% of {}'.format(f, fraction*100, m))


        
def task2(d):
    """
    Given travel distances find shortest route visiting all towns contained in towns_to_visit list. 
    Using Linear Programming

    Parameters
    ----------
    d : pandas DF
        Town distances.

    Returns
    -------
    None.

    """

    print('\n'+'-'*40)
    print('\t\t\t\tTask 2')
    print('-'*40+'\n')

    distances = d['Distances']

    all_towns = distances.columns.values
    towns_to_visit = ['Cork', 'Dublin', 'Limerick', 'Waterford', 'Galway', 'Wexford', 'Belfast', 'Athlone', 'Rosslare', 'Wicklow']
    starting_town = 'Cork'
    solver = pywraplp.Solver('LPWrapper', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    
    towns_pairs = {}
    
    # Part A. Create decision variables for pairs of towns
    for t1 in towns_to_visit:
        for t2 in towns_to_visit:
            if t1 == t2:
                continue
            towns_pairs[t1+'_'+t2] = solver.IntVar(0, 1, t1+'_'+t2)
            
    # # Part B. Ensure driver arrives in all towns to visit
    for t in towns_to_visit:
        constraint = solver.Constraint(1,1)           
        for pair in towns_pairs:
            if t == pair.split('_')[0]:
                constraint.SetCoefficient(towns_pairs[pair], 1)
            
    # Part C. Implement constraints that drive departs each town visited
    for t in towns_to_visit:
        constraint = solver.Constraint(1, 1)           
        for pair in towns_pairs:
            if t == pair.split('_')[1 ]:
                constraint.SetCoefficient(towns_pairs[pair], 1)
                
         
    # Part D. Implement constraints that there are no self-contained routes.    
    subsets = list()
    
    for n in range(len(towns_to_visit)):
        if n > 1:
            subsets += list(combinations(towns_to_visit, n))            # Get all possible subsets
    
    # For each subset implement a constraint that the number of journey pairs is less than the total number of destinations in the subset
    for subset in subsets:    
        constraint = solver.Constraint(0, len(subset)-1)
        for pair in towns_pairs:
            t1, t2 = pair.split('_')[0], pair.split('_')[1]
            if t1 in subset and t2 in subset:
                constraint.SetCoefficient(towns_pairs[pair], 1)


    # Task E: Minimize distance to be travelled
    
    distance = solver.Objective()

    for pair in towns_pairs:
        t1, t2 = pair.split('_')[0], pair.split('_')[1]
        distance.SetCoefficient(towns_pairs[pair], float(distances.loc[t1,t2]))
    
    distance.SetMinimization()
    solver.Solve()
    
    total_distance = 0
    for pair in towns_pairs:
        t1, t2 = pair.split('_')[0], pair.split('_')[1]
        total_distance += towns_pairs[pair].solution_value() * distances.loc[t1,t2]

    print('Total Distance: ', total_distance )
    
    
    # Task F: Output optimal route
    
    towns_left = copy.deepcopy(towns_to_visit)
    current_stop = starting_town
    route = []
    while len(towns_left) > 0:      
        for pair in towns_pairs:
            if towns_pairs[pair].solution_value() > 0:                  # If town pair is on route  
                t1, t2 = pair.split('_')[0], pair.split('_')[1]         # t1 = Origin, t2 = Destination
                if t1 == current_stop and t2 in towns_left:             # If this is the next pair, save destination and continue
                    route.append(current_stop)
                    towns_left.remove(current_stop)
                    current_stop = t2
            if len(towns_left) == 1:
                route.append(current_stop)
                towns_left.remove(current_stop)
            
    print('\nOptimal Route is:')
    
    route.append(starting_town)
    for t in route:
        print('\t-',t)
            

    
def task3(d):
    """
    Train network - optimize the number of trains active on a network.

    Parameters
    ----------
    d : Pandas DF
        Train network data.

    Returns
    -------
    None.

    """
    
    print('\n'+'-'*40)
    print('\t\t\t\tTask 3')
    print('-'*40+'\n')
    
    #Part A. Load data
    stops = d['Stops']
    distances = d['Distances']
    passengers = d['Passengers']
    trains = d['Trains']
    
    lines = trains.index.values
    stations = passengers.columns.values
    
    # Create all possible start and end points
    all_routes = []             
    for s1 in stations:
        for s2 in stations:
            if s1 == s2:
                continue
            all_routes.append((s1,s2))

    count = 0
    
    # with open('task3.txt', 'w') as f:
    #     f.write('Task 3 b\n')
    
    print('\n\n'+'-'*40)
    print('\t\t\tTask 3: Part B')
    print('-'*40+'\n')
    
  
    station_pair_list = list()                  # List of all connected station pairs
    pair_lines = {}                             # Dictionary of containing list of lines operating on all connected station pairs
    
    # List containing lines which are loops
    loop_lines = ['L2']
    
    for l in lines:
        for s1 in stations:
            if str(stops.loc[s1,l]) == 'nan':
                continue
            for s2 in stations:
                if str(stops.loc[s2,l]) == 'nan' or s1 == s2:
                    continue
                if abs(stops.loc[s2,l] - stops.loc[s1,l]) == 1:
                    if (s1,s2) not in pair_lines.keys():                # If
                        pair_lines[(s1,s2)] = []
                    pair_lines[(s1,s2)].append(l)
                    if (s1,s2) not in station_pair_list:
                        station_pair_list.append((s1,s2))
                else:
                    if l in loop_lines:
                        no_stops = stops[l].count()             #Number of stops
                        if (stops.loc[s1,l] == 1 and stops.loc[s2,l] == no_stops) or (stops.loc[s2,l] == 1 and stops.loc[s1,l] == no_stops):
                            if (s1,s2) not in pair_lines.keys():
                                pair_lines[(s1,s2)] = []
                            pair_lines[(s1,s2)].append(l)
                            if (s1,s2) not in station_pair_list:
                                station_pair_list.append((s1,s2))
    
    
    all_optimal_routes = {}              # Dict for recording all optimal routes key=(source,destination) Value =[route]
    for start_end in all_routes:
        start = start_end[0]
        end = start_end[1]

        # Part B. Determine time required to travel between two stations
        solver = pywraplp.Solver('LPWrapper', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
        
               
        # Create decision variables for each connected pair of stations
        station_pairs = {}
        
        # Part B (a). For each line, create a decision variable for stations connected
        for l in lines:
            for s1 in stations:
                if str(stops.loc[s1,l]) == 'nan':
                    continue
                for s2 in stations:
                    if str(stops.loc[s2,l]) == 'nan' or s1 == s2:
                        continue
                    if abs(stops.loc[s2,l] - stops.loc[s1,l]) == 1:
                        station_pairs[l+'_'+s1+'_'+s2] = solver.IntVar(0, 1, l+'_'+s1+'_'+s2)
                        # station_pair_line_list.append((l,s1,s2))
                    else:
                        if l in loop_lines:
                            no_stops = stops[l].count()
                            if (stops.loc[s1,l] == 1 and stops.loc[s2,l] == no_stops) or (stops.loc[s2,l] == 1 and stops.loc[s1,l] == no_stops):
                                station_pairs[l+'_'+s1+'_'+s2] = solver.IntVar(0, 1, l+'_'+s1+'_'+s2)
                                # station_pair_line_list.append((l,s1,s2))

     
        # Part B (b) (i). Implement constraints that origin is included in the path
        constraint = solver.Constraint(1,1)
        for pair in station_pairs:
            s1, s2 = pair.split('_')[1], pair.split('_')[2]
            if start == s1:
                constraint.SetCoefficient(station_pairs[pair], 1)           
        
        # Part B (b) (ii). Implement constraints that final station is last stop
        constraint = solver.Constraint(1,1)
        for pair in station_pairs:
            s1, s2 = pair.split('_')[1], pair.split('_')[2]
            if end == s2:
                constraint.SetCoefficient(station_pairs[pair], 1)
    
        # Part B (b) (ii). Implement constraints that there are no dead ends.
        
        # Ensure start and end are not visited more than once
        constraint = solver.Constraint(0,0)
        for pair in station_pairs:
            s1, s2 = pair.split('_')[1], pair.split('_')[2]
            if end == s1:
                constraint.SetCoefficient(station_pairs[pair], 1)
                
        constraint = solver.Constraint(0,0)
        for pair in station_pairs:
            s1, s2 = pair.split('_')[1], pair.split('_')[2]
            if start == s2:
                constraint.SetCoefficient(station_pairs[pair], 1)
        
        
        # Ensure all stations that are visited (excluding origin and destination) have two journey pairs (arriving and leaving) or not visited at all
        for s in stations:
            if s in start_end:
                continue
            constraint = solver.Constraint(0, 0)
            for pair in station_pairs:
                s1, s2 = pair.split('_')[1], pair.split('_')[2]
                if s == s1 :
                    constraint.SetCoefficient(station_pairs[pair], 1)
                if s == s2 :
                    constraint.SetCoefficient(station_pairs[pair], -1)
        
        # Part B (c). Minimize the overall travel time
        distance = solver.Objective()
    
        for pair in station_pairs:
            s1, s2 = pair.split('_')[1], pair.split('_')[2]
            distance.SetCoefficient(station_pairs[pair], float(distances.loc[s1,s2]))
        
        distance.SetMinimization()
        solver.Solve()
        
        total_distance = 0
        for pair in station_pairs:
            s1, s2 = pair.split('_')[1], pair.split('_')[2]
            total_distance += station_pairs[pair].solution_value() * distances.loc[s1,s2]
            
        route = []
        last_stop = start
        # Obtain route from optimized result including lines
        while not last_stop == end:                                            # Continue looping until we reach the last stop
            for pair in station_pairs:
                l, s1, s2 = pair.split('_')[0], pair.split('_')[1], pair.split('_')[2]
                if s1 == last_stop:
                    if station_pairs[pair].solution_value() > 0:
                        pair_route = (s1,s2)
                        route.append(pair_route)
                        last_stop = s2
               
        # with open('task3.txt', 'a') as f:
        print('Origin: {} Destination: {} Total Travel Time: {}'.format(start_end[0], start_end[1], total_distance))
        # f.write('\nOrigin: {} Destination: {} Total Travel Time: {}'.format(start_end[0], start_end[1], total_distance))
        # f.write('\nOptimal Route: ')
        print('Optimal Route: ')
        for hop in route:
            print('\t- Hop: {}   Active Lines: {}'.format(hop, pair_lines[hop]))
            # f.write('\n\t- Hop: {}   Active Lines: {}'.format(hop, pair_lines[hop]))
        

        all_optimal_routes[start_end] = route

    print('\n\n'+'-'*40)
    print('\t\t\tTask 3: Part C')
    print('-'*40+'\n')
    
    solver = pywraplp.Solver('LPWrapper', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    
    # Part C (a). Create decision variables for number of trains on each line
    train_requirements = {}
    for l in lines:
        train_requirements[l] = solver.IntVar(0, solver.Infinity(), l)
                                   
        
    # Part C (b). Ensure passenger demand is met
    
    '''
    1. Compute all traffic between hops
        for each hop
            for each route check if hop takes place:
                increment hop traffic by total passangers traversing route
    2. For each hop implement constraints that traffic is satisfied with enough trains
    '''        
    
    hop_traffic = {}                                            # Dictionary of total traffic in any given hop
    
    for sp in station_pair_list:                                # for each hop
        total_traffic = 0
        for k in all_optimal_routes:                            # For each route
            if sp in all_optimal_routes[k]:
                total_traffic += passengers.loc[k[0], k[1]]     # If hop takes place on route. Increment total passangers passing through
        
        hop_traffic[sp] = total_traffic       

    for hop in hop_traffic:
        constraint = solver.Constraint(hop_traffic[hop], solver.infinity())
        for l in lines:
            if l in pair_lines[hop]:
                constraint.SetCoefficient(train_requirements[l], int(trains.loc['L1']))
                
      
                
    number_of_trains = solver.Objective()

    for l in lines:
        number_of_trains.SetCoefficient(train_requirements[l], 1)
    
    number_of_trains.SetMinimization()    
    solver.Solve()
    total_trains_required = 0
    for l in lines:
        total_trains_required += train_requirements[l].solution_value()
        print('Line: {} Trains Required: {}'.format(l, train_requirements[l].solution_value()))

    print('Total Trains Required: ', total_trains_required)

    
        

def main():
    
    task1_data = pd.read_excel('lp_1_data.xlsx', sheet_name = None, index_col=0)
    task2_data = pd.read_excel('lp_2_data.xlsx', sheet_name = None, index_col=0)
    task3_data = pd.read_excel('lp_3_data.xlsx', sheet_name = None, index_col=0)
    
    task1(task1_data) 
    task2(task2_data)
    task3(task3_data)
    
    



if __name__ == '__main__':
    main()