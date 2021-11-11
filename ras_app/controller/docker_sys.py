from system_int import system_interface
import docker
import time
from pymemcache.client.base import Client
import numpy as np

class dockersys(system_interface):
    
    sys = None
    client_cnt = None
    dck_client = None
    cnt_names = ["tier1","monitor"]
    keys = ["think", "e1_bl", "e1_ex", "t1_hw"]
    period = 100000
    
    def __init__(self):
        self.dck_client = docker.from_env()
        self.sys=[]
    
    def startClient(self,initPop):
        r=Client("localhost:11211")
        r.set("stop","0")
        
        self.client_cnt=self.dck_client.containers.run(image="bistrulli/ras_client:0.1",
                              command="java -Xmx4G -jar ras_client-0.0.1-SNAPSHOT-jar-with-dependencies.jar --initPop %d --queues \
                                      '[\"think\", \"e1_bl\", \"e1_ex\", \"t1_hw\"]' \
                                       --jedisHost monitor.app --tier1Host tier1.app"%(initPop),
                              auto_remove=False,
                              detach=True,
                              name="client",
                              hostname="client.app",
                              network="3tier-app_default",
                              stop_signal="SIGINT")
        
        self.waitRunning(self.client_cnt)
        while(r.get("think")==None):
            time.sleep(0.2)
        
    def getNetworkCne(self):
        net=None
        try:
            net=self.dck_client.networks.get("3tier-app_default")
        except docker.errors.NotFound:
            net=self.dck_client.networks.create("3tier-app_default", driver="bridge")
        return net
    
    def stopClient(self):
        if(self.client_cnt is not None):
            print("stopping client")
            r=Client("localhost:11211")
            r.set("stop","1")
            r.close()
            self.client_cnt.reload()
            # while(self.client_cnt.status!="exited"):
            #     time.sleep(0.2)
            #     self.client_cnt.reload()
            self.client_cnt.reload()
            self.client_cnt.kill()
            self.client_cnt.remove()
            self.dck_client.containers.prune()
            self.client_cnt=None
            print("client stopping complete")
    
    def startSys(self,isCpu):
        cpuEmu=0 if(isCpu) else 1
        
        self.getNetworkCne()
        
        self.sys.append(self.dck_client.containers.run(image="memcached:1.6.12",
                              auto_remove=True,
                              detach=True,
                              name="monitor",
                              ports={'11211/tcp': 11211},
                              hostname="monitor.app",
                              network="3tier-app_default",
                              stop_signal="SIGINT",
                              command="memcached -c 2048 -t 20"))
        
        self.waitRunning(self.sys[-1])
        
        self.sys.append(self.dck_client.containers.run(image="bistrulli/ras_tier1:0.1",
                              command=["java","-Xmx4G","-jar","ras_tier1-0.0.1-SNAPSHOT-jar-with-dependencies.jar",
                                       "--cpuEmu","%d"%cpuEmu,"--jedisHost","monitor.app","--tier2Host","tier2.app"],
                              auto_remove=True,
                              detach=True,
                              name="tier1",
                              hostname="tier1.app",
                              network="3tier-app_default",
                              stop_signal="SIGINT"))
        
        self.waitRunning(self.sys[-1])
    
    def stopSystem(self):
        for cnt_n in self.cnt_names:
            try:
                cnt=self.dck_client.containers.get(cnt_n)
                print("killing %s "%(cnt.name))
                cnt.reload()
                cnt.kill()
                #cnt.remove()
            except docker.errors.NotFound:
                pass
        self.sys=[]
    
    def getstate(self,monitor):
        N = int((len(self.keys) - 2) / 2)
        str_state = [monitor.get(self.keys[i]) for i in range(len(self.keys))]
        estate = [float(str_state[i]) for i in range(len(self.keys))]
        try:
            astate = [float(str_state[0].decode('UTF-8'))]
            gidx = 1;
            for i in range(0, N):
                astate.append(float(str_state[gidx].decode('UTF-8')) + float(str_state[gidx + 1].decode('UTF-8')))
                if(float(str_state[gidx]) < 0 or float(str_state[gidx + 1]) < 0):
                    raise ValueError("Error! state < 0")
                gidx += 2
        except:
            print(time.asctime())
            for i in range(len(self.keys)):
                print(str_state[i], self.keys[i])
        
        return [astate,estate]
    
    def waitRunning(self,cnt):
        while(cnt.status!="running"):
            time.sleep(0.2)
            cnt.reload()
        print("Cnt %s is running"%(cnt.name))
        
    def setU(self,RL,cnt_name):
        found=False
        for cnt in self.sys:
            if(cnt.name==cnt_name):
                quota=np.round(RL * self.period)
                found=True
                cnt.update(cpu_period=self.period,cpu_quota=max(int(quota),1000))
                break
        
        if(not found):
            raise ValueError("container %s not found during cpulimit update"%(cnt_name))


if __name__ == "__main__":
    
    try:
        dck_sys=dockersys()
        dck_sys.startSys(False)
        dck_sys.startClient(10)
        
        mnt=Client("localhost:11211")
        for i in range(10):
            print(dck_sys.getstate(mnt)[0])
            time.sleep(0.2)
        mnt.close()
        
        #dck_sys.setU(2, "tier1-k")
        
        dck_sys.stopClient()
        dck_sys.stopSystem()
    except Exception as e:
        print(e)
        dck_sys.stopClient()
        dck_sys.stopSystem()
    
    
    