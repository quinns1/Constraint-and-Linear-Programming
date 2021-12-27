# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 19:36:10 2021

@author: quinns4
"""

import pandas as pd
from ortools.sat.python import cp_model
import numpy as np

people = ['James', 'Daniel', 'Emily', 'Sophie']
starters = ['Prawn Coctail', 'Onion Soup', 'Mushroom Tart', 'Carpaccio']
main_courses = ['Baked Mackerel', 'Fried Chicken', 'Filet Steak', 'Vegan Pie']
desserts = ['Apple Crumble', 'Ice Cream', 'Chocolate Cake', 'Tiramisu']
drinks = ['Beer', 'Coke', 'White Wine', 'Red Wine']


def task1():
    """
    Solve the logical puzzle below using CP-SAT model.

    James, Daniel, Emily, and Sophie go out for dinner. They all order a starter, a main course, a desert, and drinks and they want to order as many different things as possible.
    Emily does not like prawn cocktail as starter, nor does she want baked mackerel as main course (1).
    Daniel does not want the onion soup as starter and James does not drink beer (2).
    Sophie will only have fried chicken as main course if she does not have to take the prawn cocktail as starter (3).
    The filet steak main course should be combined with the onion soup as starter and with the apple crumble for dessert (4).
    The person who orders the mushroom tart as starter also orders the red wine (5).
    The baked mackerel should not be combined with ice cream for dessert, nor should the vegan pie be ordered as main together with prawn cocktail or carpaccio as starter (6).
    The filet steak should be eaten with either beer or coke for drinks (7).
    One of the women drinks white wine, while the other prefers red wine for drinks (8).
    One of the men has chocolate cake for dessert, while the other prefers not to have ice cream or coke but will accept one of the two if necessary (9).
    Who has tiramisu for dessert?


    Returns
    -------
    None.

    """
    

    
    print('\n'+'-'*40)
    print('Task 1')
    print('-'*40+'\n')


    #Part A: Identify the objects, attributes and predicates for the puzzle and create the decision variables in a CP-SAT model [1 point]

    model = cp_model.CpModel()


    #Create all unique booleans for each possible pair
    person_starter = {}
    for person in people:        
        variables = {}
        for starter in starters:    
            variables[starter] = model.NewBoolVar(person+starter)
        person_starter[person] = variables
    
    person_main_course = {}
    for person in people:        
        variables = {}
        for main_course in main_courses:    
            variables[main_course] = model.NewBoolVar(person+main_course)
        person_main_course[person] = variables

    person_dessert = {}
    for person in people:        
        variables = {}
        for dessert in desserts:    
            variables[dessert] = model.NewBoolVar(person+dessert)
        person_dessert[person] = variables

    person_drink = {}
    for person in people:        
        variables = {}
        for drink in drinks:    
            variables[drink] = model.NewBoolVar(person+drink)
        person_drink[person] = variables


    for person in people:
        #At least one item per person for each course
        variables = []
        for starter in starters:
            variables.append(person_starter[person][starter])
        model.AddBoolOr(variables)

        variables = []
        for main_course in main_courses:
            variables.append(person_main_course[person][main_course])
        model.AddBoolOr(variables)

        variables = []
        for dessert in desserts:
            variables.append(person_dessert[person][dessert])
        model.AddBoolOr(variables)

        variables = []
        for drink in drinks:
            variables.append(person_drink[person][drink])
        model.AddBoolOr(variables)


        #Max one item per course per person
        for i in range(4):
            for j in range(i+1,4):
                model.AddBoolOr([
                        person_starter[person][starters[i]].Not(), 
                        person_starter[person][starters[j]].Not()])
                model.AddBoolOr([
                        person_main_course[person][main_courses[i]].Not(), 
                        person_main_course[person][main_courses[j]].Not()])
                model.AddBoolOr([
                        person_dessert[person][desserts[i]].Not(), 
                        person_dessert[person][desserts[j]].Not()])
                model.AddBoolOr([
                        person_drink[person][drinks[i]].Not(), 
                        person_drink[person][drinks[j]].Not()])


        #Every person has a different meal
        for i in range(4):
            for j in range(i+1,4):
                for k in range(4):
                    model.AddBoolOr([
                            person_starter[people[i]][starters[k]].Not(), 
                            person_starter[people[j]][starters[k]].Not()])
                    model.AddBoolOr([person_main_course[people[i]][main_courses[k]].Not(), 
                                    person_main_course[people[j]][main_courses[k]].Not()])
                    model.AddBoolOr([person_dessert[people[i]][desserts[k]].Not(), 
                                    person_dessert[people[j]][desserts[k]].Not()])
                    model.AddBoolOr([person_drink[people[i]][drinks[k]].Not(), 
                                    person_drink[people[j]][drinks[k]].Not()])


        #Constraints
        
        #The filet steak main course should be combined with the onion soup as starter and with the apple crumble for dessert (4).
        model.AddBoolAnd([person_main_course[person]['Filet Steak']]).OnlyEnforceIf([person_starter[person]['Onion Soup']])
        model.AddBoolAnd([person_main_course[person]['Filet Steak']]).OnlyEnforceIf([person_dessert[person]['Apple Crumble']])
       
        #The person who orders the mushroom tart as starter also orders the red wine (5).
        model.AddBoolAnd([person_starter[person]['Mushroom Tart']]).OnlyEnforceIf([person_drink[person]['Red Wine']])
       
        #The baked mackerel should not be combined with ice cream for dessert
        model.AddBoolAnd([person_main_course[person]['Baked Mackerel'].Not()]).OnlyEnforceIf([person_dessert[person]['Ice Cream']])
        
        #nor should the vegan pie be ordered as main together with prawn cocktail or carpaccio as starter (6).
        model.AddBoolAnd([person_main_course[person]['Vegan Pie'].Not()]).OnlyEnforceIf(person_starter[person]['Prawn Coctail'])
        model.AddBoolAnd([person_main_course[person]['Vegan Pie'].Not()]).OnlyEnforceIf(person_starter[person]['Carpaccio'])
        
        
        #The filet steak should be eaten with either beer or coke for drinks (7).
        model.AddBoolOr([person_drink[person]['Beer'],
                         person_drink[person]['Coke']]).OnlyEnforceIf(person_main_course[person]['Filet Steak'])
        
    #Emily does not like prawn cocktail as starter, nor does she want baked mackerel as main course (1).
    model.AddBoolAnd([person_starter['Emily']['Prawn Coctail'].Not()]) 
    model.AddBoolAnd([person_main_course['Emily']['Baked Mackerel'].Not()])
    
    #Daniel does not want the Prawn Coctail as starter and James does not drink beer (2).
    model.AddBoolAnd([person_starter['Daniel']['Prawn Coctail'].Not()])
    model.AddBoolAnd([person_drink['James']['Beer'].Not()])
    
    #Sophie will only have fried chicken as main course if she does not have to take the prawn cocktail as starter (3).
    model.AddBoolAnd([person_main_course['Sophie']['Fried Chicken'].Not()]).OnlyEnforceIf([person_starter['Sophie']['Prawn Coctail']])
    
    
    
    #One of the women drinks white wine, while the other prefers red wine for drinks (8).
    model.AddBoolOr([person_drink['Emily']['White Wine'],
                    person_drink['Sophie']['White Wine']])
    model.AddBoolOr([person_drink['Emily']['Red Wine'],
                    person_drink['Sophie']['Red Wine']])
    
    
    #One of the men has chocolate cake for dessert, while the other prefers not to have 
    #ice cream or coke but will accept one of the two if necessary (9).
    model.AddBoolOr([person_dessert['James']['Chocolate Cake'],
                    person_dessert['Daniel']['Chocolate Cake']])
    model.AddBoolOr([person_dessert['James']['Ice Cream'],
                      person_drink['James']['Coke']]).OnlyEnforceIf(person_dessert['Daniel']['Chocolate Cake'])
    model.AddBoolOr([person_dessert['Daniel']['Ice Cream'],
                      person_drink['Daniel']['Coke']]).OnlyEnforceIf(person_dessert['James']['Chocolate Cake'])
              
      
    solver = cp_model.CpSolver()  
    status = solver.SearchForAllSolutions(model, SolutionPrinter_task1(person_starter, person_main_course, person_dessert, person_drink))
    print(solver.StatusName(status))

    for person in people:
        if solver.Value(person_dessert[person]["Tiramisu"]):
            print(person+' has the Tiramisu')
            


class SolutionPrinter_task1(cp_model.CpSolverSolutionCallback):
    def __init__(self, starter, main_course, dessert, drink):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.starter_ = starter
        self.main_course_ = main_course
        self.drink_ = drink
        self.dessert_ = dessert
        self.solutions_ = 0

    def OnSolutionCallback(self):
        self.solutions_ = self.solutions_ + 1
        print("Solution:", self.solutions_ )
        
        for person in people:
            print(" - "+person+":")

            for starter in starters:
                if (self.Value(self.starter_[person][starter])):
                    print("    - ", starter)
            for main_course in main_courses:
                if (self.Value(self.main_course_[person][main_course])):
                    print("    - ", main_course)
            for dessert in desserts:
                if (self.Value(self.dessert_[person][dessert])):
                    print("    - ", dessert)
            for drink in drinks:
                if (self.Value(self.drink_[person][drink])):
                    print("    - ", drink)
        print()




def task2(soduku):    
    """
    Soduku solver using CP_SAT model 

    Parameters
    ----------
    soduku : Numpy Array
        Soduku puzzle to be solved (0 = value to be solved).

    Returns
    -------
    None.

    """
    
    print('\n'+'-'*40)
    print('Task 2')
    print('-'*40+'\n')

    print_soduku(soduku)
    all_solutions = True
    model = cp_model.CpModel()
    field = []
    
    #Part A. Create decision variables for given soduku puzzle
    for i in range(soduku.shape[0]):
        row = []
        for j in range(soduku.shape[0]):  
            if soduku[i][j] != 0:
                #Part B. Specify constraints in digits already given
                row.append(model.NewIntVar(int(soduku[i][j]), int(soduku[i][j]), str(i)+"_"+str(j)))
            else:
                row.append(model.NewIntVar(1, 9, str(i)+"_"+str(j)))
        #Part C1. Constraint #1 all values in row are different
        model.AddAllDifferent(row)
        field.append(row)

    
    #Part C2. Constraint #2 all values in column are different
    for i in range(soduku.shape[0]):
        col = []
        for j in range(soduku.shape[0]):
            col.append(field[j][i])
        model.AddAllDifferent(col)


    #Part C3. Constraint #3 all values in 3x3 sub-grid are different
    for h in range(soduku.shape[0]):
        grid = []
        for i in [(h // 3) * 3, (h // 3) * 3 + 1, (h // 3) * 3 + 2]:
            for j in [(h % 3) * 3, (h % 3) * 3 + 1, (h % 3) * 3 + 2]:
                grid.append(field[i][j])
                model.AddAllDifferent(grid)    
                       
             
    #Part D. Solf CP_SAT model and print all solutions
    solver = cp_model.CpSolver()              
    sp = SolutionPrinter_task2(soduku, field, all_solutions)  
    status = solver.SearchForAllSolutions(model, sp)



    
def print_soduku(sod):
    print('\nProblem Soduku')
    print('-', end='')
    print('-'*4*sod.shape[0])
    for i in range(sod.shape[0]):
        line = '|'
        for j in range(sod.shape[0]):
            line += ' ' + str(sod[i][j]) + ' '
            line += '|'
        print(line)
        print('-', end='')
        print('-'*4*sod.shape[0])
    
    

class SolutionPrinter_task2(cp_model.CpSolverSolutionCallback):
    def __init__(self, sod, field, solutions):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.sod_ = sod
        self.field_ = field
        self.all_solutions_ = solutions
        self.solutions_ = 0
        

    def OnSolutionCallback(self):
        self.solutions_ = self.solutions_ + 1
        print("\nSolution: ", self.solutions_ )
        print('-', end='')
        print('-'*4*self.sod_.shape[0])
        
        for i in range(self.sod_.shape[0]):
            line = '|'
            for j in range(self.sod_.shape[0]):
                line += ' ' + str(self.Value(self.field_[i][j])) + ' '
                line += '|'
            print(line)
            print('-', end='')
            print('-'*4*self.sod_.shape[0])



def task3(d, profit_margin_min = 2160):
    """
    Project plannign using CP-SAT solver

    Parameters
    ----------
    d : PD DATAFRAME
        4 seperate sheets (Project, Quotes, Dependancies, Value).
    profit_margin_min : INT, optional
        Minimum profit margin. The default is 2160.

    Returns
    -------
    None.

    """
    
    
    print('\n'+'-'*40)
    print('Task 3')
    print('-'*40+'\n')
    
    all_solutions = False
    
    #Part A. Load data
    projects = d['Projects']
    quotes = d['Quotes']
    dependencies = d['Dependencies']
    value = d['Value']

    model = cp_model.CpModel()
    
    #Part B1. Create decision variables for each project
    projs = {}
    for p in projects.index.values:
        projs[p] = model.NewBoolVar(p)
    
    
    #Part B2. Create decision variables for which contractor is working on which project and when    
    p_c = {}    #Decision variables for all project/contractor pairs
    for c in quotes.index.values:
        #Iterate through contractors
        for j in quotes.columns.values:
            #Iterate through jobs
            if str(quotes.loc[c][j]) == 'nan':
                #If contractor is not qualified to work job, do nothing
                pass
            else:
                for p in projects.index.values:
                    #Iterate through projects
                    for m in projects.columns.values:
                        #Iterate through months
                        if str(projects.loc[p][m]) == 'nan':
                            # If no project exists on this month, do nothing
                            pass
                        else:
                            if projects.loc[p][m] == j:
                                #If contractor is qualified to work job, and job exists on this month, create boolean var 
                                p_c[p+'_'+c+'_'+m+'_'+j] = model.NewBoolVar(p+'_'+c+'_'+m+'_'+j) 


    # Part C. Constraint #1 - Contractor cannot work on two projects at the same time
    for c in quotes.index.values:
        #Iterated through contractors
        for m in projects.columns.values:
            #Iterate through months
            jobs_on = []        #List of jobs a contractor is qualified to do for any given month
            for p in projects.index.values:
                #Iterate through projects
                for j in quotes.columns.values:
                    #Iterate trhough jobs
                    if str(quotes.loc[c][j]) == 'nan':
                        #If contractor is not qualified to do job, do nothing
                        pass
                    else:
                        #If contractor can do job, add to list
                        if projects.loc[p][m] == j:
                            jobs_on.append(p_c[p+'_'+c+'_'+m+'_'+j])  
            
            #Maximum of 1 job per contractor per month
            model.Add(sum(jobs_on) <= 1)
       
            
    # Part D. Constraint #2 - Only one contractor can work on an job at a time
    for p in projects.index.values:
        #Iterate through projects
        for m in projects.columns.values:
            #Iterate through months
            if str(projects.loc[p][m]) == 'nan':
                #If no job on, do nothing
                pass
            else:
                pot_job_cont = []       #List containing all potential contractors for specific job
                for c in quotes.index.values:
                    #Iterate through contractors
                    for j in quotes.columns.values:
                        #Iterate throguh jobs
                        if str(quotes.loc[c][j]) == 'nan':
                            #If no job do nothing
                            pass
                        else:
                            if projects.loc[p][m] == j:
                                #If job is relevant add to list
                                pot_job_cont.append(p_c[p+'_'+c+'_'+m+'_'+j])           
                
                #If project is going ahead, exactly one contractor works on job
                model.Add(sum(pot_job_cont) == 1).OnlyEnforceIf(projs[p])
                
                # Part E. Constraint #3 - If project is not taken on then 0 contractors work on any of the jobs
                model.Add(sum(pot_job_cont) == 0).OnlyEnforceIf(projs[p].Not())
    
            
    # Part F. Constraint #4 - Dependencies & conlicts
    for p1 in dependencies.index.values:
        for p2 in dependencies.columns.values:
            if str(dependencies.loc[p1][p2]) == 'required':
                #If dependancie is required. Project p1 and p2 must be completed IF project p1 is going ahead
                model.AddBoolAnd([projs[p2]]).OnlyEnforceIf(projs[p1])
            if str(dependencies.loc[p1][p2]) == 'conflict':
                model.AddBoolAnd([projs[p2].Not()]).OnlyEnforceIf(projs[p1])
                
          
                


    #Part G. Difference between value of all delivered projects and costs is at least profit_margin _min
    cost = 0
    for p in projects.index.values:
        #Itearte through projects
        for m in projects.columns.values:
            #Iterate through months
            if str(projects.loc[p][m]) == 'nan':
                #If no job exists, do nothing
                pass
            else:
                #Cost = sum of all jobs being carried out
                for c in quotes.index.values:
                    #Iterate through contractors
                    for j in quotes.columns.values:
                        #Iterate through jobs
                        if str(quotes.loc[c][j]) == 'nan':
                            #If contractor not qualified to do job, do nothing
                            pass
                        else:
                            if projects.loc[p][m] == j:
                                cost += int(quotes.loc[c][j])*p_c[p+'_'+c+'_'+m+'_'+j]
    
    val = 0
    #Value = sum of all projects being carried out
    for p in value.index.values:
        val += int(value.loc[p]['Value'])*projs[p]
    
    profit_margin = val - cost
    model.Add( profit_margin >= profit_margin_min)
    
    
    #Part H. Solve CP_SAT model    
    solver = cp_model.CpSolver()    
    # status = solver.Solve(model)
    # print(solver.StatusName(status))
    sp = SolutionPrinter_task3(projs, p_c, profit_margin, all_solutions)  
    status = solver.SearchForAllSolutions(model, sp)
    print("\nThere are {} solutions".format(sp.solutions_))
     


class SolutionPrinter_task3(cp_model.CpSolverSolutionCallback):
    def __init__(self, projects, pj, profit, solutions):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.projects_ = projects
        self.pj_ = pj
        self.profit_ = profit
        self.all_solutions_ = solutions
        self.solutions_ = 0
        

    def OnSolutionCallback(self):
        self.solutions_ = self.solutions_ + 1
        print('\n'+'-'*20)
        print("Solution: ", self.solutions_ )
        print('-'*20)
        
        
        print('Projects Taken On:')
        projects = []
        for k in self.projects_.keys():
            if self.Value(self.projects_[k]):
                projects.append(str(self.projects_[k]))

        contractor_jobs = []

        for k in self.pj_.keys():
            if self.Value(self.pj_[k]):
                details=str(self.pj_[k]).split('_')
                contractor_jobs.append(details)    

        for p in projects:
            print('\t- '+p)
            for cj in contractor_jobs:
                if cj[0] == p:
                    print('\t\t- '+cj[3]+' was carried out in month '+cj[2]+' by '+cj[1])
   
        print('\nProfit Margin: ', self.Value(self.profit_))
        
        

   
    

def main():
    
    data = pd.read_excel('cp_sat_data.xlsx', sheet_name = None, index_col=0)
    
    soduku_arr = np.array( [[0, 0, 0, 0, 0, 0, 0, 3, 0],
                            [7, 0, 5, 0, 2, 0, 0, 0, 0],
                            [0, 9, 0, 0, 0, 0, 4, 0, 0],
                            [0, 0, 0, 0, 0, 4, 0, 0, 2],
                            [0, 5, 9, 6, 0, 0, 0, 0, 8],
                            [3, 0, 0, 0, 1, 0, 0, 5, 0],
                            [5, 7, 0, 0, 6, 0, 1, 0, 0],
                            [0, 0, 0, 3, 0, 0, 0, 0, 0],
                            [6, 0, 0, 4, 0, 0, 0, 0, 5]])


    task1()
    task2(soduku_arr)
    task3(data)




if __name__=='__main__':
    main()
    