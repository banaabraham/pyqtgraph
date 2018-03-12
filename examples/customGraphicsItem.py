import random
import matplotlib.pyplot as plt

class tsp(object):
    
    def __init__(self):    
        self.coordinates = []
        self.start = []
        self.mindistance = 0
        self.best = []
        self.hist = 0
        self.buku = dict()
        self.fig = 0
        
    def setCoordinates(self,c):
        self.coordinates = c 
     
    
    def setStart(self,n):
        self.start = self.coordinates[n]
        
    def distance(self,a,b):
        return ((a[0]-b[0])**2+(a[1]-b[1])**2)**0.5
    
    
    """
    calculate total traver distance
    """
    
    def alldistance(self,coordinates):
        dis = 0
        for i in range(len(coordinates)-1):
            dis += self.distance(coordinates[i],coordinates[i+1])
        return dis   
    
    
    """
    a rough dynamic programming solution functuin
    """
            
    def dynamic_prog(self):
        r = random
        exp = dict()
        recol = []
        self.mindistance = self.alldistance(self.coordinates)
        self.hist = self.mindistance
        for i in range(3):          
            tabu = [self.start]
            epoch = 0
            distance = 0         
            while True:
                j = 0  
                while len(tabu) != len(self.coordinates):
                    coordinates = self.coordinates
                    while True:
                        tempcor = r.sample(coordinates,1)[0]
                        if tempcor not in tabu:
                            tabu.append(tempcor)
                            break  
                    

                    if j==len(self.coordinates)-3:
                        tabu.append(self.start)
                        
                        
                    tb = ""
                    for i in range(len(tabu)):
                        tb+=str(tabu[i])
                                       
                    if tb in exp:
                        distance += exp[tb]
                    else:    
                        distance += self.distance(tabu[j],tabu[j+1])
                        exp[tb] = distance
                       
                    j+=1
            
                
                epoch +=1
                print(epoch)
                if self.mindistance>distance or self.mindistance==distance :
                    self.mindistance = distance
                    self.best = tabu
                
                if tabu not in recol or epoch>3:    
                    recol.append(tabu)
                    break
        self.buku = exp         
    
    """
    function to iterate solving function
    """    
                                   
    def iterate(self,n):
        for i in range(n):
            self.dynamic_prog()
    
    """
    plot the traverse
    """
    def plot_coor(self,c):
        x = []
        y = []
        for i in c:
            x.append(i[0])
            y.append(i[1])
        x.append(self.start[0])
        y.append(self.start[1])
        plt.figure(self.fig)    
        plt.plot(x,y) 
        self.fig+=1
           
        
if __name__ =="__main__":
    sales = tsp()
    """
    input coordinates here
    """
    
    cities = [[0,1],[10,0],[20,20],[3,10],[5,60]]
               
    sales.setCoordinates(cities)
    sales.setStart(0)
    sales.iterate(100)
    kamus = sales.buku
    
    awal = sales.alldistance(cities)
    hasil = sales.mindistance
    tabu = sales.best
    sales.plot_coor(cities)
    sales.plot_coor(tabu)



