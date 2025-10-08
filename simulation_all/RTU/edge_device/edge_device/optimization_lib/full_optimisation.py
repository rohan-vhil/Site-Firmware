import cvxpy as cp
import numpy as np 
import random
import sys
import math
sys.path.insert(0,"../")
import optimization_lib.fitting_functions as fitfuncs
import optimization_lib.common_functions as funcs
from scipy.optimize import linprog
import weakref
import copy
import enum
from cvxopt import matrix,solvers

class deviceType(enum.IntEnum):
    solar = 0
    battery = 1
    meter = 2 
    EV = 3
    DG=4
    grid = 5
    hvac=6

    @classmethod
    def from_param(cls, obj):
        return int(obj)

class optimal_result:
    battery_stpts = []
    grid_data : fitfuncs.gridData
    batt_energy:list
    raw_results : np.ndarray
    def __init__(self) -> None:
        self.battery_stpts = []
        self.curtailed_pv=[]
        self.ev_stpts = []
        self.ev_en = [] 
        self.grid_data = fitfuncs.gridData()
        self.batt_energy = []
        self.grid_import=[]
        self.grid_export=[]
        pass

from collections import namedtuple



class linearDeviceModel:
    A_B_ieq : np.ndarray
    A_B_eq :np.ndarray
    b_B_eq : np.ndarray
    b_B_ieq : np.ndarray
    L : np.ndarray
    bounds : tuple[np.ndarray,np.ndarray]
    iterate : bool
    var_set : tuple[int,int]
    iterate_var : float
    A_eq_row : tuple[int,int]
    A_ieq_row : tuple[int,int]
    A_eq_col: tuple[int,int]
    A_ieq_col : tuple[int,int]
    b_eq_index : tuple[int,int]
    b_ieq_index : tuple[int,int]
    bounds_index : tuple[int,int]
    bounds_inxs : list[tuple]
    iterate_vars : list
    orig_iterate_vars : list
    var_index : tuple[int,int]
    raw_result : tuple[int,int]
    output : tuple[int,int]
    device_type : deviceType
    def __init__(self):
        pass

    def buildConstraints(self):
        pass

    def getOutput(self):
        pass
class linearSystemModel:
    device_list : list
    A_B_ieq : np.ndarray
    A_B_eq :np.ndarray
    b_B_eq : np.ndarray
    b_B_ieq : np.ndarray
    bounds : tuple[np.ndarray,np.ndarray]
    L : np.ndarray
    Lu :np.ndarray
    pv_forecast : list
    load_forecast : list
    price_forecast : list
    N : int
    opt_result : np.ndarray
    opt_result_final : np.ndarray
    opt_status : bool
    results : optimal_result 
    dr_times : list # will be a list of tuples
    last_solved_copy :None
    prev_solve_limit : float
    dr_done:bool=False
    natural_max : float
    def __init__(self,pv_forecast =[0 for i in range(96)],load_forecast=[0 for i in range(96)],price_forecsat = [0 for i in range(96)]):
        self.device_list = []
        self.A_B_ieq = np.array([]).reshape(0,0)
        self.A_B_eq = np.array([]).reshape(0,0)
        self.b_B_eq = np.array([])
        self.b_B_ieq = np.array([])
        self.L = np.array([]).reshape(0,0)
        self.pv_forecast = pv_forecast
        self.load_forecast = load_forecast
        self.price_forecast = price_forecsat
        self.N = len(self.price_forecast)
        self.bounds = []
        self.Lu = load_forecast  #uncontrollable loads
        self.results = optimal_result()
        self.opt_result = None
        self.dr_done = False
        self.last_solved_copy = None
        self.dr_times = []
        self.opt_status = False

        pass

        pass

            
    def addSystemMatrix(self,Aeq,Aieq,beq,bieq,bounds):
        self.A_B_eq = funcs.addMatrixDiag(self.A_B_eq,Aeq)
        self.A_B_ieq = funcs.addMatrixDiag(self.A_B_ieq,Aieq)
        self.b_B_eq = np.concatenate((self.b_B_eq,beq))
        self.b_B_ieq = np.concatenate((self.b_B_ieq,bieq))
        self.bounds += bounds

    def addGridConstraint(self,minp=0,maxp=None,dr = False):
        maxLoad = (self.natural_max)
        if(maxp == None):
            maxp = maxLoad
        concat_matr = np.concatenate((self.L,-1*self.L))
        #print(concat_matr.shape,self.A_B_ieq.shape)
        if(self.A_B_ieq.shape != (0,0)):
            self.A_B_ieq = np.concatenate((self.A_B_ieq,concat_matr))

        else:
            self.A_B_ieq = concat_matr
        grid_lower_limit = np.array([minp for i in range(self.N)])
        if(not dr):
            grid_upper_limit = np.array([maxp for i in range(self.N)])
            
        
        elif( not self.dr_done):
            
            grid_upper_limit = np.array([maxLoad for i in range(self.N)])
            for dr_time in self.dr_times:
                grid_upper_limit[dr_time[0]:dr_time[1]] = np.array([maxp for i in range(dr_time[0],dr_time[1])])

            
        elif(dr & self.dr_done) : #signifies reducing eaks other than the drs
           
            for dr_times in self.dr_times:
                dr_peak = max(self.results.grid_import[dr_times[0]:dr_times[1]])
                #print("dr_peak : ",dr_peak,dr_times)
                grid_upper_limit = np.array([dr_peak if(i in range(dr_times[0],dr_times[1])) else maxp for i in range(self.N)])
            #print(dr_peak,maxp,grid_upper_limit)


            



        bup = grid_upper_limit - np.array(self.load_forecast)
        bl = -grid_lower_limit + np.array(self.load_forecast)

        badd = np.concatenate((bup,bl))

        self.b_B_ieq = np.concatenate((self.b_B_ieq,badd))

    def addDRConstraint():

        pass

    def addDevice(self,device:linearDeviceModel,index = None):
        device.var_set = (self.A_B_eq.shape[1],self.A_B_eq.shape[1] + device.A_B_eq.shape[1])
        device.A_eq_row = (self.A_B_eq.shape[0],self.A_B_eq.shape[0] + device.A_B_eq.shape[0])
        device.A_eq_col = (self.A_B_eq.shape[1],self.A_B_eq.shape[1] + device.A_B_eq.shape[1])
        device.A_ieq_row = (self.A_B_ieq.shape[0],self.A_B_ieq.shape[0] + device.A_B_ieq.shape[0])
        device.A_ieq_col = (self.A_B_ieq.shape[1],self.A_B_ieq.shape[1] + device.A_B_ieq.shape[1])
        device.b_eq_index = (len(self.b_B_eq),len(self.b_B_eq) + len(device.b_B_eq))
        device.b_ieq_index = (len(self.b_B_ieq),len(self.b_B_ieq) + len(device.b_B_ieq))
        device.bounds_index = (len(self.bounds),len(self.bounds) + len(device.bounds))
        device.var_index = (len(self.bounds),len(self.bounds) + len(device.bounds)) # number of variables is same as number of bounds
        #print(self.L,device.L)
        #print(self.L.shape,device.L.shape)
        #self.L =  funcs.addMatrixDiag(self.L,device.L)
        if(self.L.shape == (0,0)):
            self.L = device.L
        else:
            #print("add device", device,self.L.shape)
            self.L=np.concatenate((self.L,device.L),axis=-1)
            #print(self.L.shape)
        #print(self.L)

        self.addSystemMatrix(device.A_B_eq,device.A_B_ieq,device.b_B_eq,device.b_B_ieq,device.bounds)
        if(index ==  None):
            self.device_list.append(device)
        else:
            self.device_list[index] = device
        """
        self.A_B_eq = funcs.addMatrixDiag(self.A_B_eq,device.A_B_eq)
        self.A_B_ieq = funcs.addMatrixDiag(self.A_B_ieq,device.A_B_ieq)
        self.b_B_eq = np.concatenate((self.b_B_eq,device.b_B_eq))
        self.b_B_ieq = np.concatenate((self.b_B_ieq,device.b_B_ieq))
        """

    def editDevice(self,device:linearDeviceModel,index):
        self.device_list[index] = device

        self.A_B_eq[device.A_eq_row[0]:device.A_eq_row[1],device.A_eq_col[0]:device.A_eq_col[1]] = device.A_B_eq
        self.A_B_ieq[device.A_ieq_row[0]:device.A_ieq_row[1],device.A_ieq_col[0]:device.A_ieq_col[1]] = device.A_B_ieq

        self.b_B_eq[device.b_eq_index[0]:device.b_eq_index[1]] = device.b_B_eq
        self.b_B_eq[device.b_eq_index[0]:device.b_eq_index[1]] = device.b_B_eq

        self.bounds[device.bounds_index[0]:device.bounds_index[1]] = device.bounds
        


    def createObjectiveFunc(self):
        #print(self.price_forecast)
        #print(np.array(self.price_forecast).reshape(1,self.N).shape,self.L.shape)
        self.cost_obj = np.dot(np.array(self.price_forecast) , self.L)
        self.sum_obj = np.dot(np.array([0 for i in range(self.N)]),self.L)

        dr_list = [0 for i in range(self.N)]
        for dr in self.dr_times:
            dr_list[dr[0]:dr[1]] = [1 for i in range(dr[0],dr[1])]

        self.dr_obj = np.dot(np.array(dr_list),self.L)

        
        
    def formL(self):
        #self.Lmat = np.array([]).reshape(0,0)
        for i in range(self.N):
            self.Lmat=funcs.addMatrixDiag(self.Lmat,self.L.reshape(1,self.L.size))
        """
        for i in range(self.N - self.L.shape[0]):
            #print(i,type(self.L))
            self.L=np.concatenate((self.L,np.array([0 for j in range(self.L.shape[1])]).reshape(1,self.L.shape[1])),axis=0)
            #print(self.L)
        """
    
    def optimize(self,mode : str = "",obj : list = [],smoothen = True):
        #print("optimmize")
        #self.formL()
        #print(self.Lmat)
        #print("shapes : ",np.array(self.price_forecast).shape,self.L.transpose().shape)
        if(mode == "cost" or mode == "sum" or mode == "exchange"):
            self.optSolve(mode,obj,smoothen)
        elif(mode == "peak" or mode == "dr"):
            

            orig_peak = self.natural_max
            peak = orig_peak
            solved = True           
            bot = 0
            top = orig_peak
            while((abs(top - bot)) > 0.01):
                
                peak = (top + bot)/2
                #print("")
                #print(" ====peak=====",top,bot,peak)
                ref_copy = copy.deepcopy(self)
                ref_copy.addGridConstraint(0,peak,mode == "dr")
                solved = ref_copy.optSolve(mode,obj,smoothen)
                #tmp = copy.deepcopy(ref_copy) # save the last solved copy
                
                if(solved):
                    top = peak
                    #print("solved",peak)
                    self.last_solved_copy = copy.deepcopy(ref_copy) # save the last solved copy

                else:
                    bot = peak
                    
                #tmp = copy.deepcopy(ref_copy) # save the last solved copy
                del ref_copy
            #print(self.last_solved_copy.opt_result_final)
            self.opt_result_final = self.last_solved_copy.opt_result_final
            del self.last_solved_copy

    def filterSol(self,mode:str):
        self.results.grid_data.grid_import = np.array(self.load_forecast) + np.dot(self.L,self.opt_result_final)
        if(mode == "cost"):
            Q = matrix(2*np.identity(self.L.shape[1]))
            p = matrix(np.zeros(self.L.shape[1]))
            Gmat = np.concatenate((self.A_B_ieq,self.cost_obj.reshape(1,self.L.shape[1])))
            G = matrix(Gmat)
            hmat = np.concatenate((self.b_B_ieq,np.array(self.opt_status).reshape(1,)))
            h = matrix(hmat)
            A = matrix(self.A_B_eq)
            b = matrix(self.b_B_eq)
            sol = solvers.qp(Q,p,G,h,A,b)



        elif(mode == "peak"):
            print("reduce noise for peak")
            load_max = max(self.results.grid_data.grid_import)
            self.addGridConstraint(maxp=load_max)
            Q = matrix(2*np.identity(self.L.shape[1]))
            p = matrix(np.zeros(self.L.shape[1]))
            #Gmat = np.concatenate((system.A_B_ieq,system.cost_obj.reshape(1,system.L.shape[1])))
            G = matrix(self.A_B_ieq)
            #hmat = np.concatenate((system.b_B_ieq))
            h = matrix(self.b_B_ieq)
            A = matrix(self.A_B_eq)
            b = matrix(self.b_B_eq)
            sol = solvers.qp(Q,p,G,h,A,b)
            #charge = (sol['x'][0:battery.N])
            #discharge = (sol['x'][battery.N:])
            #plt.plot(charge + discharge)
        solution_array = np.array(sol['x']).flatten()

        self.opt_result_final = solution_array 
        self.results.grid_data.grid_import = np.array(self.load_forecast) + np.dot(self.L,self.opt_result_final)           

            

        pass
        #filter the solution to the lowest noise alternative


    def solverSelect(self,obj_val,solve_method="linear",smoothen=True):
        #print("solve with ",solve_method,obj_val)
        #print(smoothen)
        n = self.L.shape[1]
        if(solve_method == "linear"):
            func  = linprog(c=obj_val,A_ub=self.A_B_ieq,b_ub=self.b_B_ieq
                    ,A_eq=self.A_B_eq,b_eq=self.b_B_eq,bounds=self.bounds,method="highs-ds")
            self.opt_status = func.fun
            res =  func.x

            #Q = np.identity(self.N) #quadratic matrix
            
            if(not smoothen):
                return res

            #return res
        if(solve_method == "convex"):
            #print(solve_method)
            lb = np.array([self.bounds[i][0] for i in range(n)])
            ub = np.array([self.bounds[i][1] for i in range(n)])
            #print(ub)
            x= cp.Variable(n,bounds=[lb,ub])
            exchange_val = cp.sum(cp.abs(self.L@x + np.array(self.load_forecast)))
            if(type(obj_val) == str):
                #print("solve for exchange",self.L.shape,x.shape)

                objective = cp.Minimize(cp.sum(cp.abs(self.L@x + np.array(self.load_forecast))))
            else:
                #print("normal solve")
                objective = cp.Minimize(obj_val.T@x)
                #objective = cp.Minimize(0)
                #print(obj_val)
            constraints = []
            #print("inequality constraint",self.A_B_ieq.shape,x.shape,self.b_B_ieq.shape)
            if(self.A_B_ieq.shape != (0,0)):
                constraints.append(self.A_B_ieq @ x <= self.b_B_ieq)
            #print("equality constraint")
            constraints.append(self.A_B_eq @x == self.b_B_eq)
            if(hasattr(self,"prev_solve_limit")):
                constraints.append(exchange_val <= self.prev_solve_limit)
                pass
            prob = cp.Problem(objective,constraints)
            #print("solve the problem")
            try:
                prob.solve()
                self.opt_status = prob.value
                #print(self.opt_status)
            except Exception as e:
                print("exception",e)
                self.opt_status = None
            res = x.value
            #print(self.opt_status)
            if(not smoothen):
                return x.value
            #return x.value
        if(self.opt_status != None):
            lb = np.array([self.bounds[i][0] for i in range(n)])
            ub = np.array([self.bounds[i][1] for i in range(n)])
            y=cp.Variable(n,bounds=[lb,ub])
            exchange_val = cp.sum(cp.abs(self.L@y + np.array(self.load_forecast)))
            constraints = []
            #for i in range(n):
            #    constraints.append(x >= self.bounds[i][0])
            #    constraints.append(x <= self.bounds[i][1])
            if(self.A_B_ieq.shape != (0,0)):
                constraints.append(self.A_B_ieq @y <= self.b_B_ieq)
            constraints.append(self.A_B_eq @y== self.b_B_eq)
            if(type(obj_val) == str):
                objective_func = (cp.sum(cp.abs(self.L@y + np.array(self.load_forecast))))
            else:
                objective_func = obj_val.T@y
            constraints.append(objective_func <= self.opt_status)
            if(hasattr(self,"prev_solve_limit")):
                #print("has prev limit",self.prev_solve_limit)
                constraints.append(exchange_val <= self.prev_solve_limit)
            P=np.identity(n)
            objective = cp.Minimize(cp.quad_form(y,P))

            prob = cp.Problem(objective,constraints)
            prob.solve(solver=cp.CLARABEL)
            #print(prob.value,self.opt_status,objective_func.value,exchange_val.value)
            if(type(obj_val) == str):
                objective_exchange_value = sum(abs(np.dot(self.L,y.value) - self.pv_forecast + self.load_forecast))

                self.prev_solve_limit = objective_exchange_value
            return y.value


    def optSolve(self,mode : str = "",obj : list = [],smoothen=True):
        self.createObjectiveFunc()

        if(obj != []):
            obj_val = obj
        elif(mode == "cost"):
            obj_val = self.cost_obj
        elif(mode == "peak" or mode == "sum"):
            #print(self.sum_obj)
            obj_val = self.sum_obj
        elif(mode=="exchange"):
            obj_val = "exchange"

        elif(mode == "dr"):
            obj_val =self.dr_obj
        i=0

        self.opt_result = self.solverSelect(obj_val,"linear",smoothen=smoothen)
        i=0
        #if(func.fun == None):
        if(self.opt_status == None or self.opt_status == np.inf):
            #print("improper sol",self.opt_status)
            return False
        
        else:
            #print("save final result")
            self.opt_result_final = copy.deepcopy(self.opt_result)
            #print(self.opt_result_final,self.opt_status)
            return True
            pass


    def getResults(self):

        self.results.grid_data.grid_import = np.array(self.load_forecast) + np.dot(self.L,self.opt_result_final)
        
        for device in self.device_list:
            device.raw_result = self.opt_result_final[device.var_index[0]:device.var_index[1]]
            device.getOutput()


class thermalHvac():
    He:float
    Ca:float
    alpha:float
    beta:float
    Tamb :list
    power_hvac:list
    dt:float
    N : int
    Te : np.ndarray
    Ta0 : float
    Tmax : float
    Tmin :float
    pmax : float
    pmin:float

    def __init__(self,He:float,Ca:float,N:int) -> None:
        self.He = He
        self.Ca = Ca
        self.N = N
        self.dt = 24*3600/self.N
        self.beta = math.exp(-He*self.dt/Ca)
        self.alpha = (1-self.beta)/self.He
        #self.Te = np.array(Te)
        #self.Ta0=Ta0
        
        pass

class thermalSystem(linearDeviceModel):
    He:float
    Ca:float
    alpha:float
    beta:float
    Tamb :list
    power_hvac:list
    dt:float
    N : int
    Te : np.ndarray
    Ta0 : float
    Tmax : float
    Tmin :float
    pmax : float
    pmin:float

    def __init__(self,He:float,Ca:float,Te:list,Ta0) -> None:
        self.He = He
        self.Ca = Ca
        self.N = len(Te)
        self.dt = 24*3600/self.N
        self.beta = math.exp(-He*self.dt/Ca)
        self.alpha = ((1-self.beta)/self.He) * self.N/24
        self.Te = np.array(Te)
        self.Ta0=Ta0
        self.device_type = deviceType.hvac
        
        pass

    def buildConstraints(self):
        mat1 = -self.alpha * np.identity(self.N)
        mat2_beta =-self.beta * np.identity(self.N)
        mat2_beta = np.roll(mat2_beta,-1,axis=1)
        mat2_beta[0] = np.zeros(self.N)

        mat2 = mat2_beta + np.identity(self.N)
        temp_constraint = np.zeros(2*self.N)
        temp_constraint[-1] = 1
        temp_constraint = temp_constraint.reshape(1,2*self.N)
        #energy_constraints = np.concatenate(np.ones(self.N),np.zeros(self.N))    


        self.A_B_eq = np.concatenate((mat1,mat2),axis=-1)
        self.A_B_eq = np.concatenate((self.A_B_eq,temp_constraint))

        b1 = (1-self.beta) * np.array(self.Te)
        b2 = np.zeros(self.N)
        b2[0] = self.Ta0 * self.beta

        self.b_B_eq = b1 + b2
        self.b_B_eq = np.concatenate((self.b_B_eq,np.array([self.Ta0])))
        
        self.b_B_ieq = np.array([0])
        #self.b_B_ieq = np.array([])
        #self.A_B_ieq = np.array([]).reshape(0,0)
        self.A_B_ieq = np.concatenate((np.zeros(self.N),np.zeros(self.N))).reshape(1,2*self.N)

        self.L=np.concatenate((np.identity(self.N),0*np.identity(self.N)),axis=-1)
        #self.A_B_ieq = np.zeros((self.L.shape[0],self.L.shape[1]))

    def setBounds(self,Tmax,Tmin,pmax,pmin=0):
        self.pmax = pmax
        self.Tmax = Tmax
        self.Tmin = Tmin
        self.pmin = pmin
        lb_B = np.concatenate((self.pmin*np.ones(self.N),self.Tmin*np.ones(self.N))).transpose()
        ub_B = np.concatenate((self.pmax*np.ones(self.N),self.Tmax*np.ones(self.N))).transpose()
        self.bounds = [(lb_B[i],ub_B[i]) for i in range(2*self.N)]

        pass

    def getOutput(self):
        self.power_hvac = list(self.raw_result)[0:self.N]
        self.Tamb = list(self.raw_result)[self.N:]
        print("got temperature")

        




class batterySystem(linearDeviceModel):
    battery_power:float
    battery_storage:float
    battery_charge:list
    battery_discharge:list
    soc0:float=100
    battery_energy:list
    batt_cycle_limit:int
    Bmax : float
    Bmin : float
    socmin:float
    socmax:float
    charge : list
    discharge:list

    N:int
    def __init__(self, battery_power,batteyr_storage,soc0,cycle_limit=1,power_pct = 100,N:int=96) -> None:
        self.battery_power = battery_power * power_pct / 100
        self.N = N
        self.power_pct = power_pct
        self.battery_storage = batteyr_storage
        self.soc0 = soc0 *self.battery_storage /100
        self.battery_energy = [self.soc0*self.battery_storage]
        self.batt_cycle_limit = cycle_limit
        self.Bmax = self.battery_power * (24/self.N)
        self.Bmin = -self.battery_power * (24/self.N)
        self.socmin = 0
        self.socmax = self.battery_storage
        self.bounds_inxs = [(0,self.N),(self.N,2*self.N)]
        self.iterate = True
        self.iterate_var = 100
        self.iterate_vars = [100,100]
        self.orig_iterate_vars = [100,100]
        #self.L = np.array([-1,-1])
        self.L=np.concatenate((-1*np.identity(self.N),-1*np.identity(self.N)),axis=-1)
        self.device_type = deviceType.battery
        pass    

    def buildConstraints(self):
        self.power_pct = self.iterate_var
        self.discharge_pct = 100
        self.charge_pct = 100
        self.Bmax = self.battery_power * (24/self.N) * self.discharge_pct /100
        self.Bmin = -self.battery_power * (24/self.N) * self.charge_pct /100
        self.A_B_eq = np.ones(2*self.N).reshape(1,2*self.N)
        self.b_B_eq = np.array([0])
        A_B_ieq1 = np.concatenate((np.ones(self.N),-np.ones(self.N)))
        delta = np.tril(np.ones((self.N,self.N)))
        A_B_ieq2 = np.concatenate((-delta,-delta),axis=1)
        A_B_ieq3 = np.concatenate((delta,delta),axis=1)
        self.A_B_soc = np.concatenate((A_B_ieq2,A_B_ieq3))
        self.A_B_ieq = np.concatenate((A_B_ieq1.reshape(1,2*self.N),self.A_B_soc))
        lb_B = np.concatenate((np.zeros(self.N),self.Bmin*np.ones(self.N))).transpose()
        ub_B = np.concatenate((self.Bmax*np.ones(self.N),np.zeros(self.N))).transpose()
        self.b_B_ieq = np.concatenate(([2*self.batt_cycle_limit*self.battery_storage],(self.socmax-self.soc0)*np.ones(self.N)))
        self.b_B_ieq = np.concatenate((self.b_B_ieq,(self.soc0-self.socmin)*np.ones(self.N)))
        self.bounds = [(lb_B[i],ub_B[i]) for i in range(2*self.N)]

    def getOutput(self):
        self.discharge = list(self.raw_result)[0:self.N]
        self.charge = list(self.raw_result)[self.N:]    
        self.output = np.array(self.discharge) + np.array(self.charge)


class solarSystem(linearDeviceModel):
    pv_forecast : np.ndarray
    N : int
    output:list

    def __init__(self,forecast : list):
        self.N = len(forecast)
        self.pv_forecast = forecast
        self.L = -1*np.identity(self.N)


    def buildConstraints(self):

        lb = np.zeros(self.N)
        ub = np.array(self.pv_forecast)
        self.A_B_ieq = np.zeros(self.N).reshape(1,self.N)
        self.b_B_ieq = np.array([0])

        self.A_B_eq = np.zeros(self.N).reshape(1,self.N)
        self.b_B_eq = np.array([0])



        self.bounds = [(lb[i],ub[i]) for i in range(self.N)]

    def getOutput(self):
        self.output = list(self.raw_result[0:self.N])




        

class linearModel:
    battery_power:float
    battery_storage:float
    market_prices:float
    battery_charge:list
    battery_discharge:list
    soc0:float=100
    battery_energy:list
    N:int
    batt_cycle_limit:float
    thermal_hvac:thermalSystem
    bounds:list
    Bmax : float
    Bmin : float
    socmin:float
    socmax:float
    A_B_ieq : np.ndarray
    A_B_eq :np.ndarray
    b_B_eq : np.ndarray
    b_B_ieq : np.ndarray
    bounds : tuple[np.ndarray,np.ndarray]
    def __init__(self, battery_power,batteyr_storage,prices,soc0,cycle_limit=1,power_pct = 100) -> None:
        self.battery_power = battery_power * power_pct / 100
        self.power_pct = power_pct
        self.battery_storage = batteyr_storage
        self.market_prices = prices
        self.soc0 = soc0 *self.battery_storage /100
        self.battery_energy = [self.soc0*self.battery_storage]
        self.N=len(self.market_prices)
        self.batt_cycle_limit = cycle_limit
        self.Bmax = self.battery_power * (24/self.N)
        self.Bmin = -self.battery_power * (24/self.N)
        self.socmin = 0
        self.socmax = self.battery_storage
        pass    

    def createBatteryConstraints(self):
        #create all the required matrices for linear battery constraints
        O = np.ones(self.N)
        Z = np.zeros(self.N)
        self.Bmax = self.battery_power * (24/self.N) * self.power_pct /100
        self.Bmin = -self.battery_power * (24/self.N) * self.power_pct /100
        self.A_B_eq = np.ones(2*self.N).reshape(1,2*self.N)
        self.b_B_eq = np.array([0])
        A_B_ieq1 = np.concatenate((np.ones(self.N),-np.ones(self.N)))
        delta = np.tril(np.ones((self.N,self.N)))
        A_B_ieq2 = np.concatenate((-delta,-delta),axis=1)
        A_B_ieq3 = np.concatenate((delta,delta),axis=1)

        self.A_B_soc = np.concatenate((A_B_ieq2,A_B_ieq3))

        self.A_B_ieq = np.concatenate((A_B_ieq1.reshape(1,2*self.N),self.A_B_soc))
        lb_B = np.concatenate((np.zeros(self.N),self.Bmin*np.ones(self.N))).transpose()

        ub_B = np.concatenate((self.Bmax*np.ones(self.N),np.zeros(self.N))).transpose()
        self.b_B_ieq = np.concatenate(([2*self.batt_cycle_limit*self.battery_storage],(self.socmax-self.soc0)*np.ones(self.N)))
        self.b_B_ieq = np.concatenate((self.b_B_ieq,(self.soc0-self.socmin)*np.ones(self.N)))
        self.bounds = [(lb_B[i],ub_B[i]) for i in range(2*self.N)]
        #print("A_B_eq",A_B_eq)
        #print("b_B_eq",b_B_eq)
        #print("A_B_ieq1",A_B_ieq)


        pass

    def addThermalSystem(self, He:float,Ca:float,N:int,Qmax:float,Tmax:float=26,Tair_s:float=24.0,Te:list=[],Tmin:float=23,binary=False):

        
        self.thermal_hvac = thermalHvac(He,Ca,N)
        A_alpha = -self.thermal_hvac.alpha*np.identity(N)
        A_beta = -self.thermal_hvac.beta *np.roll( np.identity(N),shift=1,axis=0) + np.identity(N)
        A_beta[0,N-1] = 0
        #print(A_alpha)
        #print(A_beta)
        n=N
        I1 = np.identity(n)
        I2 = np.identity(n)
        Z1 = np.zeros((n,n))
        Z2 = np.zeros((n,n))
        IZ = np.append(np.append(I1,Z1,1),np.append(Z2,I2,1),0)
        self.A_eq =  np.append(A_alpha,A_beta,1)
        self.A = np.append(self.A_eq,IZ,0) #the overall inequality matrix for the linear HVAC model
        bTe = ([Tair_s * self.thermal_hvac.beta + (1-self.thermal_hvac.beta)*Te[0]])
        for i in range(1,N):
            bTe.append((1-self.thermal_hvac.beta)*Te[i])
        self.bTeq = np.array(bTe)
        #print(bTe)
        bTeu = np.array([Tmax for i in range(N)])
        bTel = np.array([Tmin for i in range(N)])
        bQmax = ([Qmax for i in range(n)])
        bTmax = ([Tmax for i in range(n)])
        #print(bQmax)
        bQmin = ([0 for i in range(n)])
        bTmin = ([Tmin for i in range(n)])
        #print(len(bTe),len(bQmin),len(bQmin))
        self.blb = np.array(bTe + bQmin + bTmin)
        self.bub = np.array(bTe + bQmax + bTmax)
        self.bounds=[(0,Qmax) for i in range(N)] + [(Tmin,Tmax) for i in range(N)]

        A_alpha_bin = -Qmax*self.thermal_hvac.alpha * np.identity(n)
        A_beta = -self.thermal_hvac.beta *np.roll( np.identity(N),shift=1,axis=0) + np.identity(N)
        A_beta[0,N-1] = 0

        #I2 = np.identity(n)

        #IZ=np.append(Z2,I2,1)
        self.A_eq_bin = np.append(A_alpha_bin,A_beta,1)
        self.A_bin = np.append(self.A_eq_bin,IZ,0)
        bQmax = [1 for i in range(n)]
        bQmin = [0 for i in range(n)]
        self.blb_bin = np.array(bTe + bQmin + bTmin)
        self.bub_bin = np.array(bTe + bQmax + bTmax)
        

        

        



    def buildLinearModel(self):
        iden_list = []
        bm_l = [self.battery_power for i in range(self.N)]
        for i in range(self.N):
            iden_list.append([])
            for j in range(self.N):
                if(i==j):
                    iden_list[i].append(1)
                else:
                    iden_list[i].append(0)

            for k in range(self.N):
                if(i==k):
                    iden_list[i].append(1)
                else:
                    iden_list[i].append(0)

        ineq1_lhs = iden_list
        ineq1_rhs = bm_l #C+D < Bm
        ineq2_lhs = []
        for x in iden_list:
            ineq2_lhs.append([-y for y in x])

        ineq2_rhs = bm_l #-C-D < Bm

        ineq3_lhs = [1 for i in range(self.N)] + [-1 for i in range(self.N)]
        ineq3_rhs = 2*self.battery_storage*self.N/96  #D-C < BEmax , limit on charge discharge cycles
        eq_lhs = [1 for i in range(2*self.N)] #sum(C+D)==0
        eq_rhs = 0


        ineq4_lhs = [] #soc constraints
        ineq5_lhs = []
        for i in range(self.N):
            ineq4_lhs.append([])
            ineq5_lhs.append([])
            for j in range(self.N):
                if(i>=j):
                    ineq4_lhs[i].append(-1)
                    ineq5_lhs[i].append(1)
                else:
                    ineq4_lhs[i].append(0)
                    ineq5_lhs[i].append(0)

                
            for k in range(self.N):
                if(i>=k):
                    ineq4_lhs[i].append(-1)
                    ineq5_lhs[i].append(1)
                else:
                    ineq4_lhs[i].append(0)
                    ineq5_lhs[i].append(0)

        ineq4_rhs = [self.battery_storage - self.battery_energy[0] for i in range(self.N)]
        ineq5_rhs = [self.battery_energy[0] for i in range(self.N)]

        ineq_lhs = ineq1_lhs + ineq2_lhs + ineq4_lhs + ineq5_lhs
        ineq_rhs = ineq1_rhs + ineq2_rhs + ineq4_rhs + ineq5_rhs
        ineq_lhs.append(ineq3_lhs)
        ineq_rhs.append(ineq3_rhs)


class optimalSystemDescription:
    solar :list
    load : list
    solar_real :list
    load_real :list
    N : int
    batt_power : float
    batt_storage : float
    B_min : float
    B_max :float
    storage_limit :float
    min_batt_energy : float
    B:list
    E :list
    Breal : list
    Ereal :list
    constraints :list
    constraints_real : list
    energy : list
    energy_real : list
    cost : list
    optimal_results : optimal_result #first result of optimisation on estimated data
    optimal_results_real : optimal_result #post analysis result of optimisation on real data
    optimal_results_sim : optimal_result #a simulation is run, its results come here
    optimal_results_fit : optimal_result #the result of fitting 
    nn_fit_results :fitfuncs.fittingParams
    simulated_grid_data : fitfuncs.gridData
    zn_grid_data :fitfuncs.gridData
    actFunc : None
    curtail_export : bool
    sim_batt :list
    sim_solar :list
    sim_energy : list    
    zn_bt_Stpts : list
    zn_batt_en : list
    zn_grid : list
    days : int
    problem_status:str
    def __init__(self,solar_prod,load_est,batt_power,batt_storage,load_pct=0,solar_pct=0,battp_limit_pct=100,batts_limit=100,deep_discharge_limit = 0,soc0=50,deviate=0,days=1) :
        self.solar = solar_prod
        self.N = len(solar_prod)
        self.solar_real = [x * (1+deviate/100) * random.uniform(1 - solar_pct/100,1+solar_pct/100) for x in self.solar]
        self.load = load_est
        self.load_real = [x * random.uniform(1 - load_pct/100,1+load_pct/100) for x in self.load]
        self.batt_power = batt_power
        self.batt_storage = batt_storage
        self.B_max = battp_limit_pct * self.batt_power * 24 * days / (self.N * 100)
        self.B_min = -self.B_max    
        self.curtail_export = False
        self.storage_limit = self.batt_storage * batts_limit /100
        self.min_batt_energy = self.batt_power * deep_discharge_limit / 100
        self.days = days

        self.B = [cp.Variable() for i in range(self.N)]
        self.E = [self.load[i] - self.solar[i] - self.B[i] for i in range(self.N)]
        self.Breal = [cp.Variable() for i in range(self.N)]
        self.Ereal = [self.load_real[i] - self.solar_real[i] - self.Breal[i] for i in range(self.N)]

        self.energy = [soc0 * self.batt_storage / 100]
        self.energy_real = [soc0 * self.batt_storage / 100]   

        self.optimal_results = optimal_result()
        self.optimal_results_real = optimal_result()#best possible optimal results
        self.optimal_results_fit = optimal_result() #in order to compare
        self.optimal_results_sim = optimal_result() #base optimal on real data

        #print(self.B_max,self.B_min,self.storage_limit)
        self.constraints = []
        self.constraints_real = []
        self.cost=[]
        self.constraints.append(sum(self.B)==0)
        self.constraints_real.append(sum(self.Breal)==0)
        for i in range(self.N):
            #self.constraints.append(self.B[i] <= self.B_max)
            #self.constraints.append(self.B[i] >= self.B_min)
            #self.constraints_real.append(self.Breal[i] >= self.B_min)
            #self.constraints_real.append(self.Breal[i] <= self.B_max)
            
            if(i > 0):
                self.energy.append(self.energy[i-1] - self.B[i-1])
                self.energy_real.append(self.energy_real[i-1] - self.Breal[i-1])

                self.constraints.append(self.energy[i] >= self.min_batt_energy)
                self.constraints_real.append(self.energy_real[i] >= self.min_batt_energy)
                self.constraints.append(self.energy[i] <= self.storage_limit)
                self.constraints_real.append(self.energy_real[i] <= self.storage_limit)
        

    def includeEV(self):
        slots = list(range(48,96))
        ev_batt = 30000
        self.ev_batt = 32000
        self.ev_power = [cp.Variable() for i in range(self.N)]
        self.ev_power_real = [cp.Variable() for i in range(self.N)]
        self.E = [self.load[i] - self.solar[i] - self.B[i] + self.ev_power[i] for i in range(self.N)]
        self.Ereal = [self.load_real[i] - self.solar_real[i] - self.Breal[i] + self.ev_power_real[i] for i in range(self.N)]
        self.ev_en = [0.65*ev_batt]
        self.ev_en_real = [0.65*ev_batt]
        for i in range(self.N):
            self.constraints.append(self.ev_power[i] <= 3300/4)
            self.constraints_real.append(self.ev_power_real[i] <= 3300/4)
            self.constraints.append(self.ev_power[i] >= 0)
            self.constraints_real.append(self.ev_power_real[i] >= 0)

            if(i not in slots):
                self.constraints.append(self.ev_power[i] == 0)
            
            if(i > 0):
                self.ev_en.append(self.ev_en[i-1] + self.ev_power[i-1])
                self.ev_en_real.append(self.ev_en_real[i-1] + self.ev_power_real[i-1])

                self.constraints.append(self.ev_en[i] >= 0)
                self.constraints_real.append(self.ev_en_real[i] >= 0)
                self.constraints.append(self.ev_en[i] <= ev_batt)
                self.constraints_real.append(self.ev_en_real[i] <= ev_batt)
        
        self.constraints.append(self.ev_en[self.N-1] >= 0.9*ev_batt)
            

    def enableBatteryExchangeLimit(self,k=2):
        absB = [cp.abs(x) for x in self.B]
        absBreal = [cp.abs(x) for x in self.Breal]
        self.constraints.append(sum(absB) <= k* self.batt_storage * self.days)
        self.constraints_real.append(sum(absBreal) <= k*self.batt_storage * self.days)

    def disableBatteryExport(self):
        for i in range(self.N):
            self.constraints.append(self.B[i] <= self.load[i])
            self.constraints_real.append(self.Breal[i] <= self.load_real[i])

    def disableExport(self):
        self.curtail_export = True
        self.pv_curtailed = [cp.Variable() for i in range(self.N)] #added extra variables for PV
        self.E = [self.load[i] - self.B[i] - self.pv_curtailed[i] for i in range(self.N)]
        for i in range(self.N):
            self.constraints.append(self.E[i] >= 0)
            self.constraints.append(self.pv_curtailed[i] <= self.solar[i])
            

        self.pv_curtailed_real = [cp.Variable() for i in range(self.N)] #added extra variables for PV
        self.Ereal = [self.load_real[i] - self.Breal[i] - self.pv_curtailed_real[i] for i in range(self.N)]
        for i in range(self.N):
            self.constraints_real.append(self.Ereal[i] >= 0)
            self.constraints_real.append(self.pv_curtailed_real[i] <= self.solar_real[i])


    def minimizePeak(self):
        first_peak = max(self.load)
        opt=False
        peak = first_peak
        delta = first_peak/100
        top = first_peak
        bot = (sum(self.load) - sum(self.solar))/self.N
        #bot=0
        #print(first_peak)
        opt_found = False
        rem = False
        #base_cost = sum([self.load[i]*self.cost[i] for i in range(self.N)])
        #cost_pre = base_cost
        self.optimal_results.grid_data.total_cost = 0
        while(top-bot > first_peak/500):# and self.optimal_results.grid_data.total_cost < cost_pre):
            #print(top,bot)
            peak = (top + bot)/2
            if(rem):
                for i in range(self.N):
                    self.constraints.pop()

            

            rem = True

            for i in range(self.N):
                self.constraints.append(self.E[i] <= peak)
            absE = [cp.abs(x) for x in self.E]
            costE = [self.E[i]*self.cost[i] for i in range(self.N)]
            obj = cp.Minimize(sum(absE))

            prob = cp.Problem(obj,self.constraints)
            prob.solve()

            if(prob.status == 'optimal'):
                #print(prob.status)
                opt = True
                top=peak
                self.optimal_results.battery_stpts = [sum([x.value]) for x in self.B]
                #self.optimal_results.ev_stpts = [sum([x.value]) for x in self.ev_power]
                #self.optimal_results.ev_en =  [sum([x.value]) for x in self.ev_en[1:]]
                self.optimal_results.grid_data = fitfuncs.getGridData(self.optimal_results.battery_stpts,self.load,self.solar,self.batt_storage,self.min_batt_energy,self.B_max,self.B_min,self.energy[0],self.optimal_results.ev_stpts,self.cost,self.curtail_export)

            else:
                bot = peak

        if( not opt):
            #print("not opt")
            self.optimal_results.battery_stpts = [0 for i in range(self.N)]
            self.optimal_results.grid_data = fitfuncs.getGridData(self.optimal_results.battery_stpts,self.load,self.solar,self.batt_storage,self.min_batt_energy,self.B_max,self.B_min,self.energy[0],self.optimal_results.ev_stpts,self.cost,self.curtail_export)

        

    def optimize(self,arg):
        #print("optimal")
        if(type(arg) == str):
            match arg:
                case "absEnergy":
                    absE = [cp.abs(x) for x in self.E]
                    absEreal = [cp.abs(x) for x in self.Ereal]
                    optE = sum(absE)
                    optEreal = sum(absEreal)
                    
                case "varianceEnergy":
                    avg_E = sum(self.E)/self.N
                    varE = [(x-avg_E)**2 for x in self.E]
                    avg_Ereal =sum(self.E)/self.N
                    varEreal = [(x-avg_Ereal)**2 for x in self.Ereal]
                    optE = sum(varE)
                    optEreal = sum(varEreal)

                case "costE":
                    cost = [self.cost[i]*self.E[i] for i in range(self.N)]
                    #print(self.cost)
                    cost_real = [self.cost[i]*self.Ereal[i] for i in range(self.N)]
                    optE = sum(cost)
                    optEreal = sum(cost_real)

                case "peak":
                    self.minimizePeak()
                    return


        
        obj = cp.Minimize(optE)
        prob = cp.Problem(obj,self.constraints)
        prob.solve(solver=cp.CLARABEL,verbose=False)
        self.problem_status = prob.status
        self.optimal_results.battery_stpts = [sum([x.value]) for x in self.B]
        if(self.curtail_export):
            self.optimal_results.curtailed_pv = [sum([x.value]) for x in self.pv_curtailed]
            pv = self.optimal_results.curtailed_pv 
        else: 
            pv = self.solar
        self.optimal_results.grid_data = fitfuncs.getGridData(self.optimal_results.battery_stpts,self.load,pv,self.batt_storage,self.min_batt_energy,self.B_max,self.B_min,self.energy[0],cost=self.cost)
        
        objreal = cp.Minimize(optEreal)
        prob_real = cp.Problem(objreal,self.constraints_real)
        prob_real.solve(solver=cp.CLARABEL)
        self.optimal_results_real.battery_stpts = [sum([x.value]) for x in self.Breal]
        if(self.curtail_export):
            self.optimal_results_real.curtailed_pv = [sum([x.value]) for x in self.pv_curtailed_real]
            pv_real = self.optimal_results_real.curtailed_pv 
        else: 
            pv_real = self.solar_real

        self.optimal_results_sim.grid_data =  fitfuncs.getGridData(self.optimal_results.battery_stpts,self.load_real,pv_real,self.batt_storage,self.min_batt_energy,self.B_max,self.B_min,self.energy[0],cost = self.cost,disable_export= self.curtail_export)   
        #print(self.cost) 
        self.optimal_results_real.grid_data = fitfuncs.getGridData(self.optimal_results_real.battery_stpts,self.load_real,pv_real,self.batt_storage,self.min_batt_energy,self.B_max,self.B_min,self.energy[0],cost = self.cost,disable_export=self.curtail_export)
        
    def fitANN(self,actFunc,data_list,fitting_params_num,actFunc_param_num,data_list_real,do_part_fit=False,part_fit_len=96):
        self.nn_fit_results = fitfuncs.tinyNNFit(actFunc,self.optimal_results.battery_stpts,data_list,fitting_params_num,actFunc_param_num)
        #get basic battery setpoints
        
        self.actFunc = actFunc
        self.optimal_results_sim.battery_stpts = []
        self.optimal_results_sim.batt_energy = []
        self.sim_batt=[]
        self.sim_energy=[]
        for i in range(self.N):
            data_vector = [x[i] for x in data_list_real]
            tmp = fitfuncs.battEst(actFunc,data_vector,self.nn_fit_results.fitting_params,self.nn_fit_results.actFunc_params)
            self.sim_batt.append(tmp)
            #self.optimal_results_sim.battery_stpts.append(tmp)
            #self.runSym(tmp,i,self.sim_batt,self.sim_energy)
            
        self.simulated_grid_data = fitfuncs.getGridData(self.sim_batt,self.load_real,self.solar_real,self.batt_storage,self.min_batt_energy,self.B_max,self.B_min,self.energy[0],self.cost,self.curtail_export)
        
       
        self.optimal_results_fit.battery_stpts=[]
        #print(self.optimal_results_sim.grid_data)
        for i in range(self.N):
            data_vector = [x[i] for x in data_list]
            tmp = fitfuncs.battEst(actFunc,data_vector,self.nn_fit_results.fitting_params,self.nn_fit_results.actFunc_params)
            self.optimal_results_fit.battery_stpts.append(tmp)
        
        self.optimal_results_fit.grid_data = fitfuncs.getGridData(self.optimal_results_fit.battery_stpts,self.load,self.solar,self.batt_storage,self.min_batt_energy,self.B_max,self.B_min,self.energy[0],self.cost,self.curtail_export)

        #self.optimal_results_sim.grid_data = fitfuncs.getGridData(self.optimal_results.battery_stpts,self.load_real,self.solar_real) #performance on real data

    def runSym(self,tmp,i,batt_arr,energy_arr,real_simulation=True):
        #energy_arr = self.sim_energy if(real_simulation) else self.optimal_results_sim.batt_energy
            
        tmp = min(tmp,self.B_max)
        tmp = max(tmp,self.B_min)
        tmp_e = energy_arr[i-1] - tmp if (i>0) else self.energy[0]
        #print(tmp_e)
        if(tmp_e>self.storage_limit):
            tmp = -self.storage_limit + energy_arr[i-1]
            tmp_e = self.storage_limit
        
        elif(tmp_e < self.min_batt_energy):
            tmp = energy_arr[i-1] - self.min_batt_energy    
            tmp_e = self.min_batt_energy

        energy_arr.append(tmp_e)
        batt_arr.append(tmp)
        #self.sim_batt.append(tmp) if(real_simulation) else self.optimal_results_sim.battery_stpts.append(tmp)
        
    
    #def minimizeVarianceCost(self):


    def runZeroNet(self):
        #absEx= 0
        zn_spts = [max(min(self.load_real[i]-self.solar_real[i],self.B_max),self.B_min) for i in range(self.N)]
        self.zn_grid_data = fitfuncs.getGridData(zn_spts,self.load_real,self.solar_real,self.storage_limit,self.min_batt_energy,self.B_max,self.B_min,self.energy[0])


from collections import namedtuple

aggregate_results = namedtuple('aggregate_results','agg_grid total_agg_grid_import total_agg_grid_export')
site_level_results = namedtuple('site_level_results','grid battery')
class aggSystem:
    sites : list
    agg_constraints :list
    Eagg : list
    absEagg : cp.Variable
    sqEagg : cp.Variable
    agg_system_results : aggregate_results
    average_e : float
    individual_site_results : list
    def __init__(self, site_list : list) -> None:
        self.sites = site_list #Assumption is that the site list fresh and values have not been calculated or populated
        self.agg_constraints = []
        self.Eagg = []
        self.absEagg = 0
        self.sqEagg = 0
        i=0
        self.average_e = 0
        for x in self.sites:
            self.agg_constraints += x.constraints  #aggregate constraints
            self.average_e += sum(x.load) - sum(x.solar)

        self.average_e = self.average_e / (site_list[0].N)     
        for i in range(site_list[0].N):
            eagg = 0
            for x in self.sites:
                eagg += x.E[i] 

            self.Eagg.append(eagg)

        for i in range(site_list[0].N):
            for x in self.sites:
                self.absEagg += cp.abs(x.E[i])
                self.sqEagg += x.E[i]**2
        #self.agg_system_results = aggregate_results(0,0,0)
                
        self.individual_site_results = []
        self.agg_load=[0]*site_list[0].N
        #print(site_list[0].N)
        for i in range(site_list[0].N):
            for j in range(len(self.sites)):
                self.agg_load[i] += self.sites[j].load[i]
        
            
    def minimize(self):
        #for i in range(self.sites[0].N):
         #   self.agg_constraints.append(self.Eagg[i] <= 1360)
        
        #obj = cp.Minimize(self.sqEagg)
        #prob = cp.Problem(obj,self.agg_constraints)
        #prob.solve(solver=cp.CLARABEL)
        #first_peak = max([sum([x.value]) for x in self.Eagg])
        #Eagg_val = [sum([x.value]) for x in self.Eagg]
        #absEagg_Val = [abs(x) for x in Eagg_val]
        


        #self.individual_site_results = [] 
        #print("optimal", sum(absEagg_Val))
        #self.agg_system_results  = aggregate_results([sum([x.value]) for x in self.Eagg],0,0)
        #for i in range(len(self.sites)):
            #self.individual_site_results.append(site_level_results([sum([x.value]) for x in self.sites[i].E],[sum([x.value]) for x in self.sites[i].B]))

        first_peak = max(self.agg_load)
        opt=False
        peak = first_peak
        delta = first_peak/100
        top = first_peak
        bot = self.average_e
        #print(first_peak)
        opt_found = False
        rem = False
        while(top-bot > first_peak/50):
        #while(not opt):
            #peak=peak - delta
            peak = (top + bot)/2
            #print("trying with peak",peak)
            if(rem):
                for i in range(self.sites[0].N):
                    self.agg_constraints.pop()

            rem = True

            for i in range(self.sites[0].N):
                
                self.agg_constraints.append(self.Eagg[i] <= peak)
            obj = cp.Minimize(self.absEagg)
            prob = cp.Problem(obj,self.agg_constraints)
            prob.solve(solver=cp.CLARABEL)

            if(prob.status == 'optimal'):
                opt_found = True
                Eagg_val = [sum([x.value]) for x in self.Eagg]
                absEagg_Val = [abs(x) for x in Eagg_val]
                top = peak
                self.individual_site_results = []
                #print("optimal", peak,sum(absEagg_Val))
                self.agg_system_results  = aggregate_results([sum([x.value]) for x in self.Eagg],0,0)
                for i in range(len(self.sites)):
                    self.individual_site_results.append(site_level_results([sum([x.value]) for x in self.sites[i].E],[sum([x.value]) for x in self.sites[i].B]))
            else:
                bot = peak
                #print("infeasible",peak)
                #opt=True

   


    def minimizeCost(self,costs):
        total_cost = sum([self.Eagg[i]*costs[i] for i in range(self.sites[0].N)])
        avg_eagg = sum(self.Eagg)/self.sites[0].N
        var = sum([cp.abs(x) for x in self.Eagg])
        #self.agg_constraints.append(var <= 85361)
        #for x in self.sites:
        #    for i in range(x.N):
        #        self.agg_constraints.append(cp.abs(x.B[i]) <= 300)

        obj = cp.Minimize(total_cost)
        prob = cp.Problem(obj,self.agg_constraints)
        prob.solve(solver = cp.CLARABEL)

        if(prob.status == 'optimal'):
            #Eagg_val = [sum([x.value]) for x in self.Eagg]
            self.individual_site_results = []
            #print("optimal", peak,sum(absEagg_Val))
            self.agg_system_results  = aggregate_results([sum([x.value]) for x in self.Eagg],0,0)
            for i in range(len(self.sites)):
                self.individual_site_results.append(site_level_results([sum([x.value]) for x in self.sites[i].E],[sum([x.value]) for x in self.sites[i].B]))
        #get aggregate_load


            #get results for indivudual sites
        

            
                            
    
    #def minimizeAggPEak(self):
        #get first peak
        