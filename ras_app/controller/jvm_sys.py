from system_int import system_interface
import time
import numpy as np
import subprocess
from cgroupspy import trees
from pymemcache.client.base import Client
import os
import psutil
import requests as req


class jvm_sys(system_interface):
    
    sysRootPath = None
    sys = None
    client = None
    croot = None
    cgroups = None
    period = 100000
    keys = ["think", "e1_bl", "e1_ex", "t1_hw"]
    javaCmd=None
    
    def __init__(self, sysRootPath,isCpu=True):
        
        try:
            self.javaCmd = os.environ['JAVA_HOME'] + "/bin/java"
        except:
            raise ValueError("Need to setup JAVA_HOME env variable")
        
        self.sysRootPath = sysRootPath
        if(isCpu):
            self.initCgroups()
    
    def startClient(self, pop):
        r=Client("localhost:11211")
        r.set("stop","0")
        r.set("started","0")
        r.close()
        
        
        subprocess.Popen([self.javaCmd, "-Xmx4G",
                         "-Djava.compiler=NONE", "-jar",
                         '%sras_client/target/ras_client-0.0.1-SNAPSHOT-jar-with-dependencies.jar' % (self.sysRootPath),
                         '--initPop', '%d' % (pop), '--jedisHost','localhost', '--tier1Host','localhost',
                         '--queues','[\"think\", \"e1_bl\", \"e1_ex\", \"t1_hw\"]'])
        
        self.waitClient()
        
        self.client = self.findProcessIdByName("client-0.0.1")[0]
        
    
    def stopClient(self):
        if(self.client!=None):
            r=Client("localhost:11211")
            r.set("stop","1")
            r.close()
            
            try:
                self.client.wait(timeout=2)
            except psutil.TimeoutExpired as e:
                print("terminate client forcibly")
                self.client.terminate()
                self.client.kill()
                self.client=None
        
    
    def startSys(self, isCpu):
        cpuEmu = 0 if(isCpu) else 1
        
        self.sys = []
        subprocess.Popen(["memcached","-c","2048","-t","20"])
        self.waitMemCached()
        self.sys.append(self.findProcessIdByName("memcached")[0])
        
        if(not isCpu):
            subprocess.Popen([self.javaCmd, "-Xmx4G",
                             "-Djava.compiler=NONE", "-jar",
                             '%sras_tier1/target/ras_tier1-0.0.1-SNAPSHOT-jar-with-dependencies.jar' % (self.sysRootPath),
                             '--cpuEmu', "%d" % (cpuEmu), '--jedisHost', 'localhost'])
            
            self.waitTier1()
            self.sys.append(self.findProcessIdByName("tier1-0.0.1")[0])
        else:
            subprocess.Popen(["cgexec", "-g", "cpu:t1", "--sticky", self.javaCmd, "-Xmx4G",
                             "-Djava.compiler=NONE", "-jar","-Xint",
                             '%sras_tier1/target/ras_tier1-0.0.1-SNAPSHOT-jar-with-dependencies.jar' % (self.sysRootPath),
                             '--cpuEmu', "%d" % (cpuEmu), '--jedisHost', 'localhost'])
            self.waitTier1()
            self.sys.append(self.findProcessIdByName("tier1-0.0.1")[0])
    
    def findProcessIdByName(self,processName):
        
        
        '''
        Get a list of all the PIDs of a all the running process whose name contains
        the given string processName
        '''
        listOfProcessObjects = []
        # Iterate over the all the running process
        for proc in psutil.process_iter():
           if(proc.status()=="zombie"):
               continue
           try:
               pinfo = proc.as_dict(attrs=['pid', 'name', 'create_time'])
               # Check if process name contains the given name string.
               if processName.lower() in pinfo['name'].lower() or processName.lower() in " ".join(proc.cmdline()).lower():
                   listOfProcessObjects.append(proc)
           except (psutil.NoSuchProcess, psutil.AccessDenied , psutil.ZombieProcess):
               pass
        if(len(listOfProcessObjects)!=1):
            print(len(listOfProcessObjects))
            raise ValueError("process %s not found!"%processName)
        return listOfProcessObjects;
    
    def stopSystem(self):
        if(self.sys is not None):
            for i in range(len(self.sys),0,-1):
                proc=self.sys[i-1]
                print("killing %s"%(proc.name()+" "+"".join(proc.cmdline())))
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except psutil.TimeoutExpired as e:
                    proc.kill()
                
                
        self.sys=None
    
    def getstate(self, monitor):

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
    
    def waitTier1(self):
        connected=False
        limit=1000
        atpt=0
        base_client = Client(("localhost", 11211))
        base_client.set("test_ex","1")
        while(atpt<limit and not connected):
            try:
                r = req.get('http://localhost:3000?entry=e1&snd=test')
                connected=True
                break
            except:
                time.sleep(0.2)
            finally:
                atpt+=1
        
        base_client.close()
        if(connected):
            print("connected to tier1")
        else:
            raise ValueError("error while connceting to tier1")
    
    def waitClient(self):
        connected=False
        limit=10000
        atpt=0
        base_client = Client(("localhost", 11211))
        while(atpt<limit and (base_client.get("started")==None or base_client.get("started").decode('UTF-8')=="0")):
           time.sleep(0.2)
           atpt+=1
        
        time.sleep(2)
            
        
    def waitMemCached(self):
        connected = False
        base_client = Client(("localhost", 11211))
        for i in range(1000):
            try:
                base_client.get('some_key')
                connected = True
                base_client.close()
                break
            except ConnectionRefusedError:
                time.sleep(0.2)
        base_client.close()
        
        if(connected):
            print("connected to memcached")
        else:
            raise ValueError("Impossible to connected to memcached")
        
        time.sleep(0.5)
    
    
    def initCgroups(self): 
        self.cgroups={"tier1":{"name":"t1","cg":None}}
        
        p= subprocess.Popen(["cgget", "-g", "cpu:t1"],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if(str(err).find("Cgroup does not exist") != -1):
            subprocess.check_output(["sudo", "cgcreate", "-g", "cpu:t1","-a","emilio:emilio","-t","emilio:emilio"])
    
    def setU(self,RL,cnt_name):
        
        if(self.cgroups[cnt_name]["cg"]== None):
            print("set cgrop for %s"%(self.cgroups[cnt_name]["name"]))
            self.cgroups[cnt_name]["cg"] = trees.Tree().get_node_by_path('/cpu/%s'%(self.cgroups[cnt_name]["name"]))
            
        
        quota=int(np.round(RL * self.period))
    
        self.cgroups[cnt_name]["cg"].controller.cfs_period_us=self.period
        self.cgroups[cnt_name]["cg"].controller.cfs_quota_us = max(quota,1000) 
    
    def getRT(self,monitor):
        #qui si deve estendere per prendere tutti i response time
        RT=monitor.get("rt_t1")
        if(RT is not None):
            RT=float(RT.decode('UTF-8'))
        
        
        return RT
        
       
            
if __name__ == "__main__":
    try:
        isCpu=True
        jvm_sys = jvm_sys("../",isCpu)
        
        for i in range(1):
            
            
            jvm_sys.startSys(isCpu)
            
            g = Client("localhost:11211")
            g.set("t1_hw","10")
            jvm_sys.setU(1.0,"tier1")  
            
            jvm_sys.startClient(10)
                
            mnt = Client("localhost:11211")
            
            X=[]
            for i in range(1000):
                # state=jvm_sys.getstate(mnt)
                # print(state[0],i)
                # X.append(state[0][0])
                #
                # if(isCpu):
                #     jvm_sys.setU(10,"tier1")
                
                RT=jvm_sys.getRT(mnt)
                print(RT/10**9)
                time.sleep(0.3)
                print(i)
            
           
            mnt.close()
            
            #print(np.mean(X))
            
            jvm_sys.stopClient()
            jvm_sys.stopSystem()
        
    except Exception as e:
        pass
        print(e)
        jvm_sys.stopClient()
        jvm_sys.stopSystem()
    finally:
        g.close()
        
