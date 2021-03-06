import time
import os
import numpy as np
import matplotlib.pyplot as plt
from jvm_sys import jvm_sys
from pymemcache.client.base import Client
import traceback
from controltheoreticalmulti import CTControllerScaleXNode
import collections

class systemMnt():
    rt = None
    
    def __init__(self):
        self.rt=collections.deque(maxlen=1)
        
    def getRT(self):
        if(len(self.rt)==0):
            return None
        else:
            return  [np.mean(self.rt)]
        

isCpu=False
sys = jvm_sys("../",isCpu)
#sys = dockersys()
nstep = 3000
stime = 0.1
tgt=4
S=[]
nrep=30
drep=0
tgt_v=[]
queue=[]
rts=[]
step=0
Ik=0

sys.startSys(isCpu)
optS=None
r=Client("localhost:11211")
initPop=80
sys.startClient(initPop)
pops=[initPop]

while(r.get("sim")==None):
    print("waiting")
    time.sleep(0.2)
    
cores_init=[10]
ctrlPeriod=0.1

#monitor object
mnt=systemMnt()
c1 = CTControllerScaleXNode(ctrlPeriod, cores_init, 100, BCs=[0.15], DCs=[0.05])
c1.cores=cores_init
c1.setSLA([tgt*0.1])
c1.monitoring=mnt

CTRL=""


try:
    while True:
        time.sleep(ctrlPeriod)
        rt=float(r.get("rt_t1"))/(10**9)
        if(not np.isnan(rt)):
            mnt.rt.append(rt);
            rts.append(rt)
        
        if(len(mnt.rt)>0 and not np.isnan(mnt.rt[-1])):
            if r.get("sim").decode('UTF-8')=="step":
                r.set("sim","-1")
                if(drep>=nrep):
                    break
                drep+=1
                print("change")
                
            state=sys.getstate(r)[0]
            pops.append(np.sum(state))
            
            c1.control(step)
            print("opt=",optS,"pid=",c1.cores,mnt.rt[-1])
            
            optS=[max(float(state[1])/tgt+(0.1*Ik),0.1)]
            #optS=c1.cores
            
            
            r.set("t1_hw",optS[0])
            if(isCpu):
                sys.setU(optS[0],"tier1")
            
            queue.append(state[0])
            S.append(optS[0])
            Ik+=mnt.rt[-1]-tgt*0.1
            
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
    plt.savefig("./exp/rt.pdf")
    
    plt.figure()
    plt.plot(S,label="cores")
    plt.savefig("./exp/core.pdf")
    
    plt.figure()
    plt.plot(pops,label="pop")
    plt.savefig("./exp/pop.pdf")
    
    
except Exception as ex:
    traceback.print_exception(type(ex), ex, ex.__traceback__)

finally:
    sys.stopClient()
    sys.stopSystem()

