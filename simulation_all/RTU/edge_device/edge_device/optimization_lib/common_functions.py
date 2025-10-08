import numpy as np
def sampledAverage(data_list:list,sample_gap:int):
    average_list = [0 for i in range(sample_gap)]
    index = 0
    n=0
    while(index + sample_gap < len(data_list)):
        for i in range(sample_gap):
            average_list[i] = average_list[i] + data_list[i+index]
        index = index + sample_gap
        n=n+1
    #print(n)
    average_list = [x/n for x in average_list]
    return average_list


def conversionFactor(data_list:list,factor):
    return [x/factor for x in data_list]

def interPolate(data_list : list, num : int):
    extended_list = []
    l = len(data_list)

    for i in range(l-1):
        extended_list += list(np.linspace(data_list[i],data_list[i+1],num))

        if(i<l-2):
            extended_list.pop()

    return extended_list

def reshapeVectorToMatrix(a : np.ndarray):
    if(len(a.shape) == 1):
        a = a.reshape(1,len(a))
    
    return a
    

def addMatrixDiag(A:np.ndarray,A2:np.ndarray):
    
    A=reshapeVectorToMatrix(A)
    #print(A2)
    A2=reshapeVectorToMatrix(A2)
    ncols_add = A2.shape[1]
    nrows_add = A2.shape[0]
    nrows = A.shape[0]
    ncols = A.shape[1]
    #print(ncols_add,nrows)
    zh = np.zeros((nrows,ncols_add))
    zv = np.zeros((nrows_add,ncols))
    At = np.hstack((A,zh))
    Al = np.hstack((zv,A2))
    Anew = np.vstack((At,Al))
    return Anew