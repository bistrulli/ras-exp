import subprocess
import time
import os
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from cgroupspy import trees
from jvm_sys import jvm_sys
from docker_sys import dockersys
from pymemcache.client.base import Client
import traceback
        

isCpu=True
sys = jvm_sys("../",isCpu)
#sys = dockersys()
nstep = 3000
stime = 0.1
tgt=4
S=[]
nrep=60
drep=0
tgt_v=[]
queue=[]
rts=[]
step=0
Ik=0

sys.startSys(isCpu)
optS=None
r=Client("localhost:11211")
pop=100
sys.startClient(pop)
#r.set("t1_hw",20)
pops=[pop]

try:
    while True:
        while(r.get("sim")==None):
            print("waiting")
            time.sleep(0.2)
            
        if r.get("sim").decode('UTF-8')=="step":
            r.set("sim","-1")
            if(drep>=nrep):
                break
            drep+=1
            print("change")
            
        state=sys.getstate(r)[0]
        pops.append(np.sum(state))
        
        optS=[max(float(state[1])/tgt+(0.1*Ik),0.1)]
        
        r.set("t1_hw",optS[0])
        if(isCpu):
            sys.setU(optS[0],"tier1")
        
        queue.append(state[0])
        S.append(optS[0])
        #tgt_v.append((1)/(1+0.1*tgt)*np.sum(state))
        rt=float(r.get("rt_t1"))/(10**9)
        if(not np.isnan(rt)):
            rts.append(rt);
        time.sleep(0.05)
        if(len(rts)>1 and not np.isnan(rts[-1])):
            Ik+=rts[-1]-tgt*0.1
        step+=1
        
    print("finished",step,drep)
        
    T=np.linspace(0,len(rts),len(rts))
    avgrt=np.divide(np.cumsum(rts),T)
    
    print(np.abs(avgrt[-1]-tgt*0.1)*100/(tgt*0.1))
        
    plt.figure()
    plt.plot(rts,label="rt")
    plt.plot(avgrt,label="rt_cumavg")
    #plt.plot(tgt_v,color='r',linestyle='--',label="tgt")
    plt.axhline(y=tgt*0.1, color='r', linestyle='--',label="tgt")
    plt.legend()
    plt.savefig("rt.pdf")
    
    plt.figure()
    plt.plot(S,label="cores")
    plt.savefig("core.pdf")
    
    plt.figure()
    plt.plot(pops,label="pop")
    plt.savefig("pop.pdf")
    
    
except Exception as ex:
    traceback.print_exception(type(ex), ex, ex.__traceback__)

finally:
    sys.stopClient()
    sys.stopSystem()

