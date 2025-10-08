import numpy as np 
import scipy.optimize as opt

class gridData :
    

    def __init__(self):
        self.abs_Batt = []
        self.grid_import =[]
        self.total_exchange = []
        self.total_export=0
        self.total_import = 0
        self.new_batt_setpts = []
        self.batt_energy=[]
        self.total_cost = 0
        pass

class linear_fitting_Result:
    coeff = []
    lin_batt_estimates = []


def getGridData(battery_stpts,load,pv,storage_capacity,min_batt_energy,bmax,bmin,energy0,ev=[],cost:list=[] \
                ,disable_export=False):
    #print(cost)
    grid_data = gridData()
    N = len(load)
    grid_data.new_batt_setpts = []
    grid_data.total_import=0
    grid_data.total_exchange=0
    grid_data.total_export=0
    grid_data.total_cost = 0
    #print("grid_import",len(grid_data.grid_import))
    #print(N)
    for i in range(N):
        tmp=battery_stpts[i]
        tmp=min(tmp,bmax)
        tmp=max(tmp,bmin)

        tmp_e = grid_data.batt_energy[i-1] - tmp if(i>0) else energy0

        if(tmp_e > storage_capacity):
            tmp = -storage_capacity + grid_data.batt_energy[i-1]
            tmp_e = storage_capacity

        elif(tmp_e < min_batt_energy):
            tmp = grid_data.batt_energy[i-1] - min_batt_energy
            tmp_e = min_batt_energy

        if(len(ev) == 0):
            ev_power = 0
        else:
            ev_power = ev[i]
        e=load[i] - pv[i] -tmp + ev_power
        #if(e < 0 and disable_export):
        #    tmp = pv[i] - load[i]
        #    e=0
        grid_data.batt_energy.append(tmp_e)
        grid_data.new_batt_setpts.append(tmp)

        grid_data.abs_Batt.append(abs(tmp))
        
        grid_data.grid_import.append(e)

        grid_data.total_exchange = grid_data.total_exchange + abs(e)
        
        if(e > 0):
            grid_data.total_import = grid_data.total_import + e

        else:
            grid_data.total_export = grid_data.total_export + e

        if(cost != []):
            #print(cost,e,grid_data.total_cost,i)
            grid_data.total_cost = grid_data.total_cost + e*cost[i] #if(e>0) else 0

        #if(disable_export):



    return grid_data




def LinearFitting(battery_setpts, data_list):
    Bm = np.matrix(battery_setpts).transpose()
    N = len(battery_setpts)
    one_row = [1 for i in range(N)]
    data_list.append(one_row)
    #print(data_list)
    data_matrix_transpose = np.matrix(data_list)
    data_matrix = data_matrix_transpose.transpose()
    ata = data_matrix_transpose * data_matrix
    ata_inv = np.linalg.inv(ata)
    result =linear_fitting_Result()
    result.coeff = ata_inv * data_matrix_transpose * Bm
    battery_estimates = data_matrix * result.coeff
    result.lin_batt_estimates = [x.max() for x in battery_estimates]
    #print(result.lin_batt_estimates)
    return result


## build a small neural network to fit
def battEst(actFunc,data_vector,x,a)-> float:
   
    n= len(data_vector)
    m = int((len(x)-1)/(n+2))
    y1 = []
    for i in range(m):
        tmp = np.dot(x[i*n:(i+1)*n],data_vector) + x[m*n + i]
        y1.append(actFunc(tmp,a))

    y2 = actFunc(np.dot(x[m*n+m:m*n+2*m],y1) + x[m*n + 2*m],a)
    return y2

    
def sqError(x):
    n=len(fitting_results.battery_stpts)
    #print("n",n, len(fitting_results.data_list[0]))
    batt_est=[]
    fit_patrams = x[:fitting_results.fitting_params_num]
    actfunc_params = x[fitting_results.fitting_params_num:]
    for i in range(n):
        data_vector = [c[i] for c in fitting_results.data_list]
        batt_est.append(battEst(fitting_results.actFunc,data_vector,fit_patrams,actfunc_params))
    
    sq_err = sum([(batt_est[i] - fitting_results.battery_stpts[i])**2 for i in range(n)])
    return sq_err

class fittingParams:
    battery_stpts=[]
    data_list = []
    fitting_params = []
    actFunc = None
    actFunc_params = []
    fitting_params_num = 0
    actFunc_params_num = 0
    new_estimates = []


def tinyNNFit(actFunc, battery_stpts, data_list,fit_param_num,actFunc_param_num):
    fitting_results.actFunc = actFunc
    fitting_results.fitting_params_num = fit_param_num
    fitting_results.actFunc_params_num = actFunc_param_num
    fitting_results.fitting_params = [0.1]*fit_param_num
    fitting_results.actFunc_params = [0.1]*actFunc_param_num
    x = np.array(fitting_results.fitting_params + fitting_results.actFunc_params)
    fitting_results.battery_stpts = battery_stpts
    fitting_results.data_list = data_list
    res = opt.minimize(sqError,x0 = x)
    
    fitting_results.fitting_params = res.x[:fitting_results.fitting_params_num]
    fitting_results.actFunc_params = res.x[fitting_results.fitting_params_num:]
    #print(res.fun)
    #print("fitting params : ",fitting_results.fitting_params)
    #print("function params : ",fitting_results.actFunc_params)
    fitting_results.new_estimates = []
    for i in range(len(battery_stpts)):
        data_vector = [c[i] for c in fitting_results.data_list]
        fitting_results.new_estimates.append(battEst(fitting_results.actFunc,data_vector,fitting_results.fitting_params,fitting_results.actFunc_params))
    
    
    return fitting_results


    #print(actFunc())


fitting_results = fittingParams()
