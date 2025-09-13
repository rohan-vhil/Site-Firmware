from flask import Flask

import full_optimisation as opt
import csv 
import matplotlib.pyplot as plt
import math
import numpy as np
from datetime import datetime
#from flask import Flask
from flask import Flask, jsonify, request 
import json
import gc
import time
import numpy

import sys
sys.path.insert(0,"../")


app = Flask(__name__)




@app.route('/runOpt',methods=["POST"])
def runOptimisation():
   
    if request.method == "POST":
        st_time = time.time()
        
        
        data={}
        print("getting data",request)
        data_api = json.loads(request.get_json())
        #data_api = request.get_json()

        #print(data_api['solar'])
        
        if "solar" in data_api:
            data['solar'] = data_api['solar']
        else:
            data['solar'] = [0 for i in range(96)]
        if 'load' in data_api:
            data['load'] = data_api['load']
        else:
            data['load'] = [0 for i in range(96)]
        if "optMode" in data_api:
            data["mode"] = data_api["optMode"]
        else :
            data["mode"] = "absEnergy"
        if "batt_power" in data_api:
            batt_power = data_api["batt_power"]
        else :
            batt_power=5000
        if "batt_capacity" in data_api:
            storage_capacity = data_api["batt_capacity"]
        else:
            storage_capacity = 5000

        if "cost" in data_api:
            data['cost'] = data_api['cost']
        else:
            data['cost'] = []

        if "soc0" in data_api:
            data["soc0"] = data_api["soc0"]

        else :
            data["soc0"] = 10

        if "soc0" in data_api:
            data['soc0'] = data_api['soc0']
        else:
            data['soc0'] = 10
        results = opt.optimalSystemDescription(data['solar'],data['load'],0,0, batt_power,storage_capacity,soc0=data['soc0'])
        results.disableBatteryExport()
        #n=len(data['solar'])
        #results.cost = [base_cost*inc if(i in tou_range) else base_cost for i in range(n*d)]
        results.disableExport()
        results.enableBatteryExchangeLimit()
        results.cost = data['cost']
        grid_data=[data['load'][i]-data['solar'][i] for i in range(len(data['solar']))]
        results.optimize(data['mode'])
        #return ret_var, 201
        result_dict={
            "solar":data['solar'],
            "load":data['load'],
            "battery":results.optimal_results.battery_stpts,
            "net_consumption_without_battery":grid_data,
            "net_consumption_with_battery":results.optimal_results.grid_data.grid_import,
            "battery energy":results.optimal_results.grid_data.batt_energy
            
        }
        del data
        del data_api
        del grid_data
        del results
        gc.collect()
        


        ret_var = json.dumps(result_dict)
        
 
        return ret_var
#print(results)





@app.route('/runVPPOpt',methods=["POST"])
def runAggOpt():
    if request.method == 'POST':
        #print("running aggregate optimisation")
        
        #data_api = request.get_json()
        data_api = json.loads(request.get_json())
        #print(data_api)
        sites=[]
        for site_data in data_api['vpp_data']:
            data={}
            
            #site = opt.optimalSystemDescription(site['solar'])
            if "batt_power" in site_data:
                batt_power = site_data["batt_power"]
            else :
                batt_power=5000
            if "batt_capacity" in site_data:
                storage_capacity = site_data["batt_capacity"]
            else:
                storage_capacity = 5000

            if "cost" in site_data:
                data['cost'] = site_data['cost']
            else:
                data['cost'] = []

            if "soc0" in site_data:
                data["soc0"] = site_data["soc0"]

            else :
                data["soc0"] = 10

            if "soc0" in site_data:
                data['soc0'] = site_data['soc0']
            else:
                data['soc0'] = 10

            site = opt.optimalSystemDescription(site_data['solar'],site_data['load'],0,0, batt_power,storage_capacity,soc0=data['soc0'])
            site.enableBatteryExchangeLimit()
            sites.append(site)

        system=opt.aggSystem(site_list=sites)
        #system.minimizeCost(ext_costs)
        system.minimize()

        results_dict=[]
        agg_solar=[0]*96
        agg_load = [0]*96
        agg_battery = [0]*96
        agg_grid = [0]*96
        for i in range(96):
            for j in range(len(sites)):
                agg_solar[i] += sites[j].solar[i]
                agg_load[i] += sites[j].load[i]
                agg_battery[i] += system.individual_site_results[j].battery[i]
                agg_grid[i] += system.individual_site_results[j].grid[i]
        agg_net = [agg_load[i] - agg_solar[i] for i in range(len(agg_load))]
        agg_result = {'solar':agg_solar,
                           'load':agg_load,
                           'battery':agg_battery,
                           'net_consumption_without_battery':agg_net,
                           'net_consumption_with_battery':agg_grid}
        results_dict.append(agg_result)
        
        for i in range(len(sites)):
            net = [sites[i].load[j] - sites[i].solar[j] for j in range(sites[i].N)]
            site_result = {'solar':sites[i].solar,
                           'load':sites[i].load,
                           'battery':system.individual_site_results[i].battery,
                           'net_consumption_without_battery':net,
                           'net_consumption_with_battery':system.individual_site_results[i].grid}
            results_dict.append(site_result)

        return json.dumps(results_dict)


if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8000)
