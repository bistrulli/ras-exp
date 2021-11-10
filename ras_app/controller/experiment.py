import subprocess
import time
import os
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from cgroupspy import trees
from jvm_sys import jvm_sys
from pymemcache.client.base import Client
import traceback
        

isCpu=True
sys = jvm_sys("../",isCpu)
nstep = 500
stime = 0.1
tgt=2
S=[]

rt = []

optS=None

pop=np.random.randint(low=10, high=100)

sys.startSys(isCpu)
r=Client("localhost:11211")
sys.startClient(pop)
queue=[]

tgt_v = (1)/(1+0.1*tgt)*pop

try:
    for i in tqdm(range(nstep)):
        state=sys.getstate(r)[0] 
        print(state[0],i)
        
        optS=[max(0.001,float(state[1])/tgt)]
        
        r.set("t1_hw",optS[0])
        if(isCpu):
            sys.setU(optS[0],"tier1")
        
        queue.append(state[0])
        S.append(optS[0])
        print(state,optS,tgt_v)
        time.sleep(stime)
    
    sys.stopClient()
    sys.stopSystem()
    
    
    T=np.linspace(1,nstep,nstep+1)
    q_avg=np.divide(np.cumsum(queue),T) 
    
    e=abs(q_avg[-1]-tgt_v)*100/tgt_v
    
    print(e)
    
    plt.figure()
    plt.plot(q_avg)
    plt.axhline(y=tgt_v, color='r', linestyle='--',label="tgt")
    plt.legend()
    plt.savefig("rt.pdf")
    
    plt.figure()
    plt.plot(S,label="cores")
    plt.savefig("core.pdf")

except Exception as ex:
    traceback.print_exception(type(ex), ex, ex.__traceback__)
    sys.stopClient()
    sys.stopSystem()

